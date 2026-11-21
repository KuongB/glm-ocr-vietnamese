"""Export the approved annotations.

Writes two views of the same data:

* ``dataset.jsonl`` -- one ``{"image": ..., "text": ...}`` object per line, the
  shape a fine-tuning script wants.
* ``label.json`` -- the ``{"<image file>": "<text>"}`` mapping the rest of this
  repo already uses (``data_sample/1/label.json``, and what the Colab
  preprocessing notebook produces).

Only ``approved`` records are exported; rejected and in-flight records are left
in the manifest.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from .schema import Record, RecordStatus
from .store import RecordStore

logger = logging.getLogger(__name__)


def approved_records(store: RecordStore) -> List[Record]:
    """Approved records that actually carry text, in manifest order."""
    out = []
    for record in store:
        if record.status is not RecordStatus.APPROVED:
            continue
        text = (record.final_text or "").strip()
        if not text:
            logger.warning("%s is approved but has no final text; skipping", record.id)
            continue
        out.append(record)
    return out


def export(store: RecordStore, out_dir: Path) -> Dict[str, object]:
    """Write ``dataset.jsonl`` and ``label.json`` into ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = approved_records(store)

    jsonl_path = out_dir / "dataset.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(
                json.dumps(
                    {
                        "image": record.image,
                        "text": (record.final_text or "").strip(),
                        "id": record.id,
                    },
                    ensure_ascii=False,
                )
            )
            fh.write("\n")

    # label.json is keyed by image path. Two images with the same basename in
    # different subfolders would collide, so key on the full relative path and
    # warn if a plain basename key would have been ambiguous.
    labels: Dict[str, str] = {}
    basenames: Dict[str, int] = {}
    for record in records:
        labels[record.image] = (record.final_text or "").strip()
        name = Path(record.image).name
        basenames[name] = basenames.get(name, 0) + 1

    collisions = sum(1 for count in basenames.values() if count > 1)
    if collisions:
        logger.warning(
            "%d image basename(s) appear in more than one subfolder; "
            "label.json is keyed by relative path",
            collisions,
        )

    label_path = out_dir / "label.json"
    with label_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(labels, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    total_chars = sum(len(text) for text in labels.values())
    summary = {
        "exported": len(records),
        "characters": total_chars,
        "dataset_jsonl": str(jsonl_path),
        "label_json": str(label_path),
    }
    logger.info("exported %d approved pair(s) to %s", len(records), out_dir)
    return summary
