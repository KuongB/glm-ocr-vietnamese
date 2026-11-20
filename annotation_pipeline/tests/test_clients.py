"""Endpoint clients: response parsing, retries and failure handling.

Everything runs against an ``httpx.MockTransport``; no network access.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest

from pipeline.clients import CorrectorClient, EndpointError, OCRClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def transport(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5)


# -- OCR client -----------------------------------------------------------


async def test_ocr_sends_base64_and_reads_text(tmp_path: Path):
    image = tmp_path / "a.png"
    image.write_bytes(b"\x89PNG-bytes")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"text": "tôi đi học"})

    async with transport(handler) as client:
        result = await OCRClient("https://ocr.test").transcribe(client, image)

    assert result == "tôi đi học"
    assert base64.b64decode(seen["payload"]["image_b64"]) == b"\x89PNG-bytes"


async def test_ocr_missing_text_field_is_an_error(tmp_path: Path):
    image = tmp_path / "a.png"
    image.write_bytes(b"x")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    async with transport(handler) as client:
        with pytest.raises(EndpointError, match="no 'text' field"):
            await OCRClient("https://ocr.test").transcribe(client, image)


async def test_empty_url_rejected_early():
    with pytest.raises(ValueError):
        OCRClient("")


# -- retry policy ---------------------------------------------------------


async def test_retries_then_succeeds(tmp_path: Path, monkeypatch):
    image = tmp_path / "a.png"
    image.write_bytes(b"x")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, text="cold starting")
        return httpx.Response(200, json={"text": "ok"})

    # Don't actually sleep through the back-off.
    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)

    async with transport(handler) as client:
        result = await OCRClient("https://ocr.test", max_retries=3).transcribe(client, image)

    assert result == "ok"
    assert calls["n"] == 3


async def test_gives_up_after_max_retries(tmp_path: Path, monkeypatch):
    image = tmp_path / "a.png"
    image.write_bytes(b"x")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, text="boom")

    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)

    async with transport(handler) as client:
        with pytest.raises(EndpointError, match="failed after 2 attempt"):
            await OCRClient("https://ocr.test", max_retries=2).transcribe(client, image)

    assert calls["n"] == 2


async def test_4xx_fails_fast_without_retrying(tmp_path: Path, monkeypatch):
    image = tmp_path / "a.png"
    image.write_bytes(b"x")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, text="unauthorized")

    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)

    async with transport(handler) as client:
        with pytest.raises(EndpointError, match="401"):
            await OCRClient("https://ocr.test", max_retries=3).transcribe(client, image)

    assert calls["n"] == 1, "a 4xx must not be retried"


async def test_timeout_is_retried(tmp_path: Path, monkeypatch):
    image = tmp_path / "a.png"
    image.write_bytes(b"x")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ReadTimeout("too slow", request=request)
        return httpx.Response(200, json={"text": "ok"})

    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)

    async with transport(handler) as client:
        result = await OCRClient("https://ocr.test", max_retries=2).transcribe(client, image)

    assert result == "ok"
    assert calls["n"] == 2


async def test_bearer_token_is_sent(tmp_path: Path):
    image = tmp_path / "a.png"
    image.write_bytes(b"x")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"text": "ok"})

    async with transport(handler) as client:
        await OCRClient("https://ocr.test", token="sekret").transcribe(client, image)

    assert seen["auth"] == "Bearer sekret"


# -- corrector client -----------------------------------------------------


async def test_corrector_posts_texts_and_reads_corrected():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"corrected": ["tôi đi học", "hà nội"]})

    async with transport(handler) as client:
        out = await CorrectorClient("https://c.test").correct_batch(
            client, ["toi di hoc", "ha noi"]
        )

    assert out == ["tôi đi học", "hà nội"]
    assert seen["payload"] == {"texts": ["toi di hoc", "ha noi"]}


async def test_corrector_empty_batch_skips_the_call():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not have called the endpoint")

    async with transport(handler) as client:
        assert await CorrectorClient("https://c.test").correct_batch(client, []) == []


@pytest.mark.parametrize(
    "body",
    [
        {"corrected": ["a", "b"]},
        {"texts": ["a", "b"]},
        {"results": ["a", "b"]},
        {"outputs": ["a", "b"]},
        ["a", "b"],
    ],
)
async def test_corrector_accepts_alternative_response_shapes(body):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    async with transport(handler) as client:
        out = await CorrectorClient("https://c.test").correct_batch(client, ["x", "y"])

    assert out == ["a", "b"]


async def test_corrector_accepts_single_text_response_for_batch_of_one():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "tôi"})

    async with transport(handler) as client:
        out = await CorrectorClient("https://c.test").correct_batch(client, ["toi"])

    assert out == ["tôi"]


async def test_corrector_rejects_length_mismatch(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"corrected": ["only one"]})

    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)

    async with transport(handler) as client:
        with pytest.raises(EndpointError, match="returned 1 text"):
            await CorrectorClient("https://c.test").correct_batch(client, ["a", "b"])


async def test_corrector_rejects_unreadable_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"nothing": "useful"})

    monkeypatch.setattr("pipeline.clients.asyncio.sleep", _no_sleep)

    async with transport(handler) as client:
        with pytest.raises(EndpointError, match="cannot read corrected text"):
            await CorrectorClient("https://c.test").correct_batch(client, ["a", "b"])


async def _no_sleep(_seconds):
    return None
