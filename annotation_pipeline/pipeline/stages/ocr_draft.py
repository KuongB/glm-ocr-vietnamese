"""Stage 1 -- semi-automatic OCR for draft transcriptions.

Sends every pending image to the OCR endpoint and stores the result as
``draft_text``. Nothing here is authoritative: the point is to give the human
reviewer in stage 3 something to correct rather than a blank box.

Records that fail land in ``ocr_failed`` with the error attached, and are picked
up again the next time the stage runs.
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import AsyncExitStack
from pathlib import Path
from typing import List, Optional

import httpx

from ..clients import OCRClient, build_async_client
from ..config import Settings
from ..schema import (
    OCR_INPUT_STATUSES,
    Record,
    RecordStatus,
    StageMeta,
)
from ..store import RecordStore

logger = logging.getLogger(__name__)

STAGE_NAME = "ocr"


async def _one(
    client,
    ocr: OCRClient,
    record: Record,
    images_dir: Path,
    semaphore: asyncio.Semaphore,
) -> None:
    image_path = images_dir / record.image
    started = time.monotonic()

    async with semaphore:
        if not image_path.exists():
            record.mark(RecordStatus.OCR_FAILED)
            record.record_stage(
                STAGE_NAME,
                StageMeta(
                    duration_s=0.0,
                    error="image file not found: %s" % image_path,
                ),
            )
            logger.error("%s: image not found at %s", record.id, image_path)
            return

        try:
            text = await ocr.transcribe(client, image_path)
        except Exception as exc:  # noqa: BLE001 - recorded on the record
            record.mark(RecordStatus.OCR_FAILED)
            record.record_stage(
                STAGE_NAME,
                StageMeta(duration_s=time.monotonic() - started, error=str(exc)),
            )
            logger.error("%s: OCR failed: %s", record.id, exc)
            return

    record.mark(RecordStatus.DRAFTED, draft_text=text)
    record.record_stage(
        STAGE_NAME, StageMeta(duration_s=time.monotonic() - started)
    )
    logger.info("%s: drafted %d char(s)", record.id, len(text))


async def run(
    store: RecordStore,
    settings: Settings,
    *,
    limit: Optional[int] = None,
    save_every: int = 50,
    client: Optional[httpx.AsyncClient] = None,
) -> dict:
    """Run stage 1 over every pending record.

    Pass ``client`` to reuse an existing ``httpx`` client (the tests inject a
    mock transport this way); otherwise one is created and closed here.

    Returns a summary dict with ``processed``, ``drafted`` and ``failed``.
    """
    todo: List[Record] = store.with_status(OCR_INPUT_STATUSES, limit=limit)
    if not todo:
        logger.info("stage 1 (ocr): nothing to do")
        return {"processed": 0, "drafted": 0, "failed": 0}

    ocr = OCRClient(
        settings.require("OCR_API_URL"),
        token=settings.OCR_API_TOKEN,
        timeout=settings.REQUEST_TIMEOUT,
        max_retries=settings.MAX_RETRIES,
    )
    semaphore = asyncio.Semaphore(max(1, settings.CONCURRENCY))
    images_dir = Path(settings.IMAGES_DIR)

    logger.info("stage 1 (ocr): %d record(s) to transcribe", len(todo))

    done = 0
    async with AsyncExitStack() as stack:
        if client is None:
            client = await stack.enter_async_context(
                build_async_client(settings.REQUEST_TIMEOUT)
            )
        # Chunk the work so progress is flushed to disk as we go, which keeps a
        # long run resumable without holding one giant task list.
        for start in range(0, len(todo), save_every):
            chunk = todo[start : start + save_every]
            await asyncio.gather(
                *(_one(client, ocr, rec, images_dir, semaphore) for rec in chunk)
            )
            store.save()
            done += len(chunk)
            logger.info("stage 1 (ocr): %d/%d done", done, len(todo))

    drafted = sum(1 for rec in todo if rec.status is RecordStatus.DRAFTED)
    failed = sum(1 for rec in todo if rec.status is RecordStatus.OCR_FAILED)
    return {"processed": len(todo), "drafted": drafted, "failed": failed}
