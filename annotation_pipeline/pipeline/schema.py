"""Record schema for the annotation pipeline.

One :class:`Record` per image. A record moves through the pipeline by status:

    pending ──(stage 1: OCR)──▶ drafted ──(stage 2: SLM)──▶ corrected
                   │                            │                │
                   ▼                            ▼                ▼
              ocr_failed                 correct_failed    (stage 3: review)
                                                            approved / rejected

Stages only touch records in the status they expect, which is what makes the
pipeline resumable: re-running a stage after a crash picks up where it stopped.
"""

from __future__ import annotations

import enum
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RecordStatus(str, enum.Enum):
    """Where a record currently sits in the pipeline."""

    PENDING = "pending"
    OCR_FAILED = "ocr_failed"
    DRAFTED = "drafted"
    CORRECT_FAILED = "correct_failed"
    CORRECTED = "corrected"
    APPROVED = "approved"
    REJECTED = "rejected"


#: Statuses a record can hold once a human has signed off on it.
TERMINAL_STATUSES = frozenset({RecordStatus.APPROVED, RecordStatus.REJECTED})

#: Statuses that stage 1 (OCR) will pick up.
OCR_INPUT_STATUSES = frozenset({RecordStatus.PENDING, RecordStatus.OCR_FAILED})

#: Statuses that stage 2 (SLM correction) will pick up.
CORRECT_INPUT_STATUSES = frozenset({RecordStatus.DRAFTED, RecordStatus.CORRECT_FAILED})

#: Statuses that stage 3 (review) will present to a human.
REVIEW_INPUT_STATUSES = frozenset({RecordStatus.CORRECTED, RecordStatus.DRAFTED})


def utcnow() -> str:
    """Current UTC time as an ISO-8601 string with a trailing ``Z``."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def record_id(image: str) -> str:
    """Stable id for an image path.

    Derived from the path so that re-scanning the image directory produces the
    same ids and never duplicates work already done.
    """
    digest = hashlib.sha1(image.replace("\\", "/").encode("utf-8")).hexdigest()
    return digest[:16]


class StageMeta(BaseModel):
    """Bookkeeping for one stage run against one record."""

    at: str = Field(default_factory=utcnow)
    duration_s: Optional[float] = None
    attempts: int = 1
    model: Optional[str] = None
    error: Optional[str] = None


class Record(BaseModel):
    """A single image/text annotation and its pipeline history."""

    id: str
    image: str
    status: RecordStatus = RecordStatus.PENDING

    #: Stage 1 output: raw OCR transcription.
    draft_text: Optional[str] = None
    #: Stage 2 output: draft after SLM spelling correction.
    corrected_text: Optional[str] = None
    #: Stage 3 output: the text a human signed off on.
    final_text: Optional[str] = None

    #: Free-form note a reviewer can leave (why it was rejected, etc.).
    note: Optional[str] = None
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None

    stages: Dict[str, StageMeta] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=utcnow)

    @classmethod
    def for_image(cls, image: str) -> "Record":
        """Build a fresh pending record for an image path."""
        normalised = image.replace("\\", "/")
        return cls(id=record_id(normalised), image=normalised)

    # -- transitions ------------------------------------------------------

    def mark(self, status: RecordStatus, **fields: Any) -> None:
        """Set the status and any extra fields, refreshing ``updated_at``."""
        self.status = status
        for key, value in fields.items():
            setattr(self, key, value)
        self.updated_at = utcnow()

    def record_stage(self, name: str, meta: StageMeta) -> None:
        self.stages[name] = meta
        self.updated_at = utcnow()

    @property
    def review_text(self) -> str:
        """The best available text to put in front of a reviewer."""
        for candidate in (self.final_text, self.corrected_text, self.draft_text):
            if candidate is not None:
                return candidate
        return ""

    @property
    def was_corrected(self) -> bool:
        """True when the SLM actually changed the draft."""
        if self.draft_text is None or self.corrected_text is None:
            return False
        return self.draft_text.strip() != self.corrected_text.strip()


class Stats(BaseModel):
    """Status counts across the whole manifest."""

    total: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)

    @property
    def approved(self) -> int:
        return self.by_status.get(RecordStatus.APPROVED.value, 0)

    def as_lines(self) -> List[str]:
        lines = ["total: %d" % self.total]
        for status in RecordStatus:
            count = self.by_status.get(status.value, 0)
            if count:
                lines.append("  %-15s %d" % (status.value, count))
        return lines
