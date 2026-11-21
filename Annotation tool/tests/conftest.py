"""Shared fixtures. Nothing here touches the network."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PIPELINE_ROOT = Path(__file__).resolve().parent.parent
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from pipeline.config import Settings  # noqa: E402
from pipeline.schema import Record, RecordStatus  # noqa: E402
from pipeline.store import RecordStore  # noqa: E402

# A 1x1 PNG, enough for anything that only needs real image bytes on disk.
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae"
    "426082"
)


@pytest.fixture
def images_dir(tmp_path: Path) -> Path:
    """Three images, one of them in a subfolder."""
    root = tmp_path / "images"
    (root / "sub").mkdir(parents=True)
    for name in ("a.jpg", "b.png"):
        (root / name).write_bytes(PNG_1PX)
    (root / "sub" / "c.jpg").write_bytes(PNG_1PX)
    # Should be ignored by the scanner.
    (root / "notes.txt").write_text("not an image", encoding="utf-8")
    return root


@pytest.fixture
def settings(tmp_path: Path, images_dir: Path) -> Settings:
    """Settings pointed entirely at tmp_path, with dummy endpoint URLs."""
    return Settings(
        _env_file=None,
        OCR_API_URL="https://ocr.test/endpoint",
        CORRECTOR_API_URL="https://corrector.test/endpoint",
        IMAGES_DIR=images_dir,
        MANIFEST_PATH=tmp_path / "manifest.jsonl",
        EXPORT_DIR=tmp_path / "export",
        REQUEST_TIMEOUT=5,
        MAX_RETRIES=2,
        CONCURRENCY=2,
        CORRECTOR_BATCH_SIZE=2,
        REVIEWER_NAME="tester",
    )


@pytest.fixture
def store(settings: Settings) -> RecordStore:
    """A store with the three scanned images registered as pending."""
    store = RecordStore.load(Path(settings.MANIFEST_PATH))
    store.scan_images(Path(settings.IMAGES_DIR), settings.image_suffixes)
    store.save()
    return store


@pytest.fixture
def drafted_store(store: RecordStore) -> RecordStore:
    """Every record already carries a draft, ready for stage 2."""
    for index, record in enumerate(store):
        record.mark(RecordStatus.DRAFTED, draft_text="draft %d" % index)
    store.save()
    return store


def make_record(image: str, status: RecordStatus, **fields) -> Record:
    record = Record.for_image(image)
    record.mark(status, **fields)
    return record
