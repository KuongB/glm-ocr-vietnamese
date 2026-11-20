"""JSONL-backed record store.

The manifest is a plain JSONL file: one :class:`~pipeline.schema.Record` per
line. That keeps it greppable and diffable, and large enough to hold the whole
corpus in memory while a stage runs (~100 MB at 100K records).

Writes go through :meth:`RecordStore.save`, which writes a sibling temp file and
then replaces the manifest, so an interrupted run never truncates it.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set

from .schema import Record, RecordStatus, Stats, utcnow

logger = logging.getLogger(__name__)


class RecordStore:
    """An ordered, id-keyed collection of records persisted as JSONL."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._records: Dict[str, Record] = {}
        self._lock = threading.RLock()

    # -- persistence ------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> "RecordStore":
        """Read a manifest, or return an empty store if it does not exist."""
        store = cls(path)
        if not store.path.exists():
            return store

        skipped = 0
        with store.path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = Record.model_validate_json(line)
                except Exception as exc:  # noqa: BLE001 - keep going on bad lines
                    skipped += 1
                    logger.warning("%s:%d is not a valid record: %s", path, lineno, exc)
                    continue
                store._records[record.id] = record

        if skipped:
            logger.warning("skipped %d unreadable line(s) in %s", skipped, path)
        return store

    def save(self) -> None:
        """Atomically rewrite the manifest."""
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8", newline="\n") as fh:
                for record in self._records.values():
                    fh.write(record.model_dump_json(exclude_none=True))
                    fh.write("\n")
            os.replace(tmp, self.path)

    # -- collection access ------------------------------------------------

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[Record]:
        return iter(list(self._records.values()))

    def __contains__(self, record_id: object) -> bool:
        return record_id in self._records

    def get(self, record_id: str) -> Optional[Record]:
        return self._records.get(record_id)

    def put(self, record: Record) -> None:
        with self._lock:
            self._records[record.id] = record

    def ids(self) -> List[str]:
        return list(self._records.keys())

    # -- queries ----------------------------------------------------------

    def with_status(
        self,
        statuses: Iterable[RecordStatus],
        limit: Optional[int] = None,
    ) -> List[Record]:
        """Records in any of ``statuses``, in manifest order."""
        wanted: Set[RecordStatus] = set(statuses)
        out: List[Record] = []
        for record in self._records.values():
            if record.status in wanted:
                out.append(record)
                if limit is not None and len(out) >= limit:
                    break
        return out

    def stats(self) -> Stats:
        counts: Dict[str, int] = {}
        for record in self._records.values():
            counts[record.status.value] = counts.get(record.status.value, 0) + 1
        return Stats(total=len(self._records), by_status=counts)

    # -- ingestion --------------------------------------------------------

    def scan_images(
        self,
        images_dir: Path,
        suffixes: Sequence[str],
    ) -> int:
        """Add a pending record for every image not already in the manifest.

        Returns the number of records added. Existing records are left alone,
        so re-scanning after adding new images is safe and cheap.
        """
        images_dir = Path(images_dir)
        if not images_dir.exists():
            raise FileNotFoundError("images directory not found: %s" % images_dir)

        allowed = {s.lower() for s in suffixes}
        added = 0
        with self._lock:
            for path in sorted(images_dir.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in allowed:
                    continue
                relative = path.relative_to(images_dir).as_posix()
                record = Record.for_image(relative)
                if record.id in self._records:
                    continue
                self._records[record.id] = record
                added += 1
        return added

    # -- review helpers ---------------------------------------------------

    def next_for_review(
        self,
        statuses: Iterable[RecordStatus],
        after_id: Optional[str] = None,
    ) -> Optional[Record]:
        """The first reviewable record, optionally starting after ``after_id``."""
        wanted = set(statuses)
        seen_anchor = after_id is None
        for record in self._records.values():
            if not seen_anchor:
                if record.id == after_id:
                    seen_anchor = True
                continue
            if record.status in wanted:
                return record
        # Wrap around so the reviewer is not stranded at the end of the file.
        if after_id is not None:
            for record in self._records.values():
                if record.id == after_id:
                    break
                if record.status in wanted:
                    return record
        return None

    def apply_review(
        self,
        record_id: str,
        *,
        status: RecordStatus,
        final_text: Optional[str],
        reviewer: str,
        note: Optional[str] = None,
    ) -> Record:
        """Record a human decision and persist it immediately."""
        if status not in (RecordStatus.APPROVED, RecordStatus.REJECTED):
            raise ValueError("review status must be approved or rejected")

        with self._lock:
            record = self._records.get(record_id)
            if record is None:
                raise KeyError(record_id)
            record.mark(
                status,
                final_text=final_text if status is RecordStatus.APPROVED else None,
                reviewer=reviewer,
                reviewed_at=utcnow(),
                note=note,
            )
            self.save()
        return record
