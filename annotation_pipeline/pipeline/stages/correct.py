"""Stage 2 -- SLM spelling correction of the OCR drafts.

The small language model (``nrl-ai/vn-spell-correction-small``, BARTpho-based)
runs behind its own HTTP endpoint. This stage does nothing but batch the drafts,
POST the text, and store what comes back as ``corrected_text``.

Keeping the model behind an API means this stage has no ML dependencies and can
run anywhere, and the endpoint can be swapped or re-hosted without touching the
pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import AsyncExitStack
from typing import List, Optional

import httpx

from ..clients import CorrectorClient, build_async_client
from ..config import Settings
from ..schema import (
    CORRECT_INPUT_STATUSES,
    Record,
    RecordStatus,
    StageMeta,
)
from ..store import RecordStore

logger = logging.getLogger(__name__)

STAGE_NAME = "correct"

#: Model behind the endpoint, recorded on each record for traceability.
MODEL_ID = "nrl-ai/vn-spell-correction-small"


async def _one_batch(
    client,
    corrector: CorrectorClient,
    batch: List[Record],
    semaphore: asyncio.Semaphore,
) -> None:
    started = time.monotonic()
    texts = [rec.draft_text or "" for rec in batch]

    async with semaphore:
        try:
            corrected = await corrector.correct_batch(client, texts)
        except Exception as exc:  # noqa: BLE001 - recorded on each record
            elapsed = time.monotonic() - started
            for rec in batch:
                rec.mark(RecordStatus.CORRECT_FAILED)
                rec.record_stage(
                    STAGE_NAME,
                    StageMeta(duration_s=elapsed, model=MODEL_ID, error=str(exc)),
                )
            logger.error("batch of %d failed: %s", len(batch), exc)
            return

    elapsed = time.monotonic() - started
    per_record = elapsed / len(batch) if batch else 0.0
    changed = 0
    for rec, text in zip(batch, corrected):
        rec.mark(RecordStatus.CORRECTED, corrected_text=text)
        rec.record_stage(
            STAGE_NAME, StageMeta(duration_s=per_record, model=MODEL_ID)
        )
        if rec.was_corrected:
            changed += 1

    logger.info(
        "corrected batch of %d (%d changed) in %.2fs", len(batch), changed, elapsed
    )


async def run(
    store: RecordStore,
    settings: Settings,
    *,
    limit: Optional[int] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict:
    """Run stage 2 over every drafted record.

    Pass ``client`` to reuse an existing ``httpx`` client (the tests inject a
    mock transport this way); otherwise one is created and closed here.

    Returns a summary dict with ``processed``, ``corrected``, ``changed`` and
    ``failed``.
    """
    todo: List[Record] = store.with_status(CORRECT_INPUT_STATUSES, limit=limit)
    if not todo:
        logger.info("stage 2 (correct): nothing to do")
        return {"processed": 0, "corrected": 0, "changed": 0, "failed": 0}

    corrector = CorrectorClient(
        settings.require("CORRECTOR_API_URL"),
        token=settings.CORRECTOR_API_TOKEN,
        timeout=settings.REQUEST_TIMEOUT,
        max_retries=settings.MAX_RETRIES,
    )
    batch_size = max(1, settings.CORRECTOR_BATCH_SIZE)
    batches = [todo[i : i + batch_size] for i in range(0, len(todo), batch_size)]
    semaphore = asyncio.Semaphore(max(1, settings.CONCURRENCY))

    logger.info(
        "stage 2 (correct): %d record(s) in %d batch(es) of %d",
        len(todo),
        len(batches),
        batch_size,
    )

    async with AsyncExitStack() as stack:
        if client is None:
            client = await stack.enter_async_context(
                build_async_client(settings.REQUEST_TIMEOUT)
            )
        # Flush after each group of concurrent batches so a crash loses little.
        group = max(1, settings.CONCURRENCY)
        for start in range(0, len(batches), group):
            await asyncio.gather(
                *(
                    _one_batch(client, corrector, batch, semaphore)
                    for batch in batches[start : start + group]
                )
            )
            store.save()

    corrected = sum(1 for rec in todo if rec.status is RecordStatus.CORRECTED)
    failed = sum(1 for rec in todo if rec.status is RecordStatus.CORRECT_FAILED)
    changed = sum(1 for rec in todo if rec.was_corrected)
    return {
        "processed": len(todo),
        "corrected": corrected,
        "changed": changed,
        "failed": failed,
    }
