"""Stage 1 and stage 2 end-to-end against a mock transport."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from pipeline.schema import RecordStatus
from pipeline.stages import correct, ocr_draft
from pipeline.store import RecordStore

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def no_backoff_sleep(monkeypatch):
    async def _no_sleep(_seconds):
        return None

    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)


def mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5)


# -- stage 1 --------------------------------------------------------------


async def test_ocr_stage_drafts_every_pending_record(store, settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "toi di hoc"})

    async with mock_client(handler) as client:
        summary = await ocr_draft.run(store, settings, client=client)

    assert summary == {"processed": 3, "drafted": 3, "failed": 0}
    assert all(rec.status is RecordStatus.DRAFTED for rec in store)
    assert all(rec.draft_text == "toi di hoc" for rec in store)
    assert all("ocr" in rec.stages for rec in store)


async def test_ocr_stage_is_resumable(store, settings):
    """A second run must not re-transcribe what already succeeded."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"text": "ok"})

    async with mock_client(handler) as client:
        await ocr_draft.run(store, settings, limit=1, client=client)
        assert calls["n"] == 1
        summary = await ocr_draft.run(store, settings, client=client)

    assert summary["processed"] == 2, "the already-drafted record must be skipped"
    assert calls["n"] == 3


async def test_ocr_stage_records_failure_and_retries_next_run(store, settings):
    state = {"fail": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["fail"]:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json={"text": "recovered"})

    async with mock_client(handler) as client:
        summary = await ocr_draft.run(store, settings, client=client)
        assert summary == {"processed": 3, "drafted": 0, "failed": 3}
        assert all(rec.status is RecordStatus.OCR_FAILED for rec in store)
        assert all(rec.stages["ocr"].error for rec in store)

        # ocr_failed records are picked up again.
        state["fail"] = False
        summary = await ocr_draft.run(store, settings, client=client)

    assert summary == {"processed": 3, "drafted": 3, "failed": 0}
    assert all(rec.draft_text == "recovered" for rec in store)


async def test_ocr_stage_flags_missing_image_file(store, settings):
    target = next(iter(store))
    (Path(settings.IMAGES_DIR) / target.image).unlink()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "ok"})

    async with mock_client(handler) as client:
        summary = await ocr_draft.run(store, settings, client=client)

    assert summary["failed"] == 1
    assert summary["drafted"] == 2
    assert store.get(target.id).status is RecordStatus.OCR_FAILED
    assert "not found" in store.get(target.id).stages["ocr"].error


async def test_ocr_stage_persists_progress(store, settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "saved"})

    async with mock_client(handler) as client:
        await ocr_draft.run(store, settings, client=client)

    reloaded = RecordStore.load(Path(settings.MANIFEST_PATH))
    assert all(rec.draft_text == "saved" for rec in reloaded)


async def test_ocr_stage_no_work_skips_endpoint(drafted_store, settings):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("endpoint must not be called")

    async with mock_client(handler) as client:
        summary = await ocr_draft.run(drafted_store, settings, client=client)

    assert summary == {"processed": 0, "drafted": 0, "failed": 0}


async def test_ocr_stage_requires_url(store, settings):
    settings.OCR_API_URL = ""
    with pytest.raises(RuntimeError, match="OCR_API_URL"):
        await ocr_draft.run(store, settings)


# -- stage 2 --------------------------------------------------------------


async def test_correct_stage_batches_requests(drafted_store, settings):
    """CORRECTOR_BATCH_SIZE is 2, so 3 records become 2 requests."""
    batches = []

    def handler(request: httpx.Request) -> httpx.Response:
        texts = json.loads(request.content)["texts"]
        batches.append(len(texts))
        return httpx.Response(200, json={"corrected": [t.upper() for t in texts]})

    async with mock_client(handler) as client:
        summary = await correct.run(drafted_store, settings, client=client)

    assert summary["processed"] == 3
    assert summary["corrected"] == 3
    assert summary["failed"] == 0
    assert sorted(batches) == [1, 2]
    assert all(rec.status is RecordStatus.CORRECTED for rec in drafted_store)
    assert all(rec.corrected_text == (rec.draft_text or "").upper() for rec in drafted_store)


async def test_correct_stage_counts_only_actual_changes(drafted_store, settings):
    def handler(request: httpx.Request) -> httpx.Response:
        texts = json.loads(request.content)["texts"]
        # Echo the input back untouched: nothing was corrected.
        return httpx.Response(200, json={"corrected": texts})

    async with mock_client(handler) as client:
        summary = await correct.run(drafted_store, settings, client=client)

    assert summary["corrected"] == 3
    assert summary["changed"] == 0
    assert all(rec.was_corrected is False for rec in drafted_store)


async def test_correct_stage_records_model_id(drafted_store, settings):
    def handler(request: httpx.Request) -> httpx.Response:
        texts = json.loads(request.content)["texts"]
        return httpx.Response(200, json={"corrected": texts})

    async with mock_client(handler) as client:
        await correct.run(drafted_store, settings, client=client)

    assert all(
        rec.stages["correct"].model == "nrl-ai/vn-spell-correction-small"
        for rec in drafted_store
    )


async def test_correct_stage_failure_marks_whole_batch(drafted_store, settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    async with mock_client(handler) as client:
        summary = await correct.run(drafted_store, settings, client=client)

    assert summary["processed"] == 3
    assert summary["failed"] == 3
    assert all(rec.status is RecordStatus.CORRECT_FAILED for rec in drafted_store)
    assert all(rec.stages["correct"].error for rec in drafted_store)


async def test_correct_stage_retries_failed_records(drafted_store, settings):
    state = {"fail": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["fail"]:
            return httpx.Response(500, text="boom")
        texts = json.loads(request.content)["texts"]
        return httpx.Response(200, json={"corrected": [t + "!" for t in texts]})

    async with mock_client(handler) as client:
        await correct.run(drafted_store, settings, client=client)
        state["fail"] = False
        summary = await correct.run(drafted_store, settings, client=client)

    assert summary["corrected"] == 3
    assert all(rec.corrected_text.endswith("!") for rec in drafted_store)


async def test_correct_stage_handles_empty_draft(store, settings):
    from pipeline.schema import RecordStatus as RS

    for rec in store:
        rec.mark(RS.DRAFTED, draft_text="")

    def handler(request: httpx.Request) -> httpx.Response:
        texts = json.loads(request.content)["texts"]
        assert all(t == "" for t in texts)
        return httpx.Response(200, json={"corrected": texts})

    async with mock_client(handler) as client:
        summary = await correct.run(store, settings, client=client)

    assert summary["corrected"] == 3
    assert summary["changed"] == 0


async def test_correct_stage_requires_url(drafted_store, settings):
    settings.CORRECTOR_API_URL = ""
    with pytest.raises(RuntimeError, match="CORRECTOR_API_URL"):
        await correct.run(drafted_store, settings)


# -- the two stages together ---------------------------------------------


async def test_full_automated_run_leaves_records_ready_for_review(store, settings):
    def ocr_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "toi di hoc"})

    def correct_handler(request: httpx.Request) -> httpx.Response:
        texts = json.loads(request.content)["texts"]
        return httpx.Response(
            200, json={"corrected": ["tôi đi học" for _ in texts]}
        )

    async with mock_client(ocr_handler) as client:
        await ocr_draft.run(store, settings, client=client)
    async with mock_client(correct_handler) as client:
        await correct.run(store, settings, client=client)

    assert all(rec.status is RecordStatus.CORRECTED for rec in store)
    assert all(rec.was_corrected for rec in store)
    assert all(rec.review_text == "tôi đi học" for rec in store)
