"""HTTP clients for the two hosted models.

Both endpoints are serverless, so the first call after an idle period pays a
cold start of 20-30s. Every call therefore retries with exponential back-off
(1s, 2s, 4s) on timeouts, network errors and 5xx, and fails fast on 4xx -- the
same policy the web backend uses in ``backend/app/services/ocr_service.py``.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import httpx

logger = logging.getLogger(__name__)


class EndpointError(RuntimeError):
    """Raised when an endpoint cannot be reached or keeps failing."""


class _BaseClient:
    """Shared retry/transport behaviour."""

    name = "endpoint"

    def __init__(
        self,
        url: str,
        *,
        token: str = "",
        timeout: int = 120,
        max_retries: int = 3,
    ):
        if not url:
            raise ValueError("%s URL is empty" % self.name)
        self.url = url
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer %s" % self.token
        return headers

    async def _post(self, client: httpx.AsyncClient, payload: Dict[str, Any]) -> Any:
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.post(
                    self.url, json=payload, headers=self._headers()
                )
                if response.status_code == 200:
                    return response.json()

                message = "%s returned %d: %s" % (
                    self.name,
                    response.status_code,
                    response.text[:300],
                )
                # A 4xx is our fault (bad payload, bad auth) -- retrying cannot help.
                if 400 <= response.status_code < 500:
                    raise EndpointError(message)
                last_error = EndpointError(message)
                logger.warning("attempt %d/%d: %s", attempt, self.max_retries, message)

            except httpx.TimeoutException as exc:
                last_error = EndpointError(
                    "%s timed out after %ds (the model may be cold-starting)"
                    % (self.name, self.timeout)
                )
                logger.warning("attempt %d/%d timed out: %s", attempt, self.max_retries, exc)
            except httpx.RequestError as exc:
                last_error = EndpointError("%s network error: %s" % (self.name, exc))
                logger.warning("attempt %d/%d network error: %s", attempt, self.max_retries, exc)

            if attempt < self.max_retries:
                wait = 2 ** (attempt - 1)
                logger.info("waiting %ds before retry", wait)
                await asyncio.sleep(wait)

        raise EndpointError(
            "%s failed after %d attempt(s): %s" % (self.name, self.max_retries, last_error)
        )


class OCRClient(_BaseClient):
    """Stage 1: image -> draft transcription.

    Talks to the GLM-OCR endpoint deployed by ``serve.py`` at the repo root,
    which accepts ``{"image_b64": ...}`` and returns ``{"text": ...}``.
    """

    name = "OCR endpoint"

    async def transcribe(self, client: httpx.AsyncClient, image_path: Path) -> str:
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        data = await self._post(client, {"image_b64": image_b64})
        if not isinstance(data, dict):
            raise EndpointError("OCR endpoint returned %s, expected an object" % type(data).__name__)
        text = data.get("text")
        if text is None:
            raise EndpointError("OCR endpoint response has no 'text' field: %r" % (data,))
        return str(text)


class CorrectorClient(_BaseClient):
    """Stage 2: draft text -> spelling-corrected text.

    The SLM (``nrl-ai/vn-spell-correction-small``, BARTpho-based) is hosted
    separately; this client only sends text and reads the result back. It POSTs
    ``{"texts": [...]}`` and accepts a response shaped as any of::

        {"corrected": ["...", "..."]}
        {"texts":     ["...", "..."]}
        {"results":   ["...", "..."]}
        ["...", "..."]

    so it keeps working if the endpoint is re-implemented behind a different
    serving stack. ``serve_corrector.py`` in this folder returns the first form.
    """

    name = "corrector endpoint"

    _LIST_KEYS = ("corrected", "texts", "results", "outputs")
    _SINGLE_KEYS = ("corrected", "text", "result", "output")

    async def correct_batch(
        self, client: httpx.AsyncClient, texts: Sequence[str]
    ) -> List[str]:
        """Correct a batch of texts, returning one output per input."""
        if not texts:
            return []

        data = await self._post(client, {"texts": list(texts)})
        corrected = self._extract(data, len(texts))

        if len(corrected) != len(texts):
            raise EndpointError(
                "corrector endpoint returned %d text(s) for %d input(s)"
                % (len(corrected), len(texts))
            )
        return corrected

    @classmethod
    def _extract(cls, data: Any, expected: int) -> List[str]:
        if isinstance(data, list):
            return [str(item) for item in data]

        if isinstance(data, dict):
            for key in cls._LIST_KEYS:
                value = data.get(key)
                if isinstance(value, list):
                    return [str(item) for item in value]
            # A single-text response is only unambiguous for a batch of one.
            if expected == 1:
                for key in cls._SINGLE_KEYS:
                    value = data.get(key)
                    if isinstance(value, str):
                        return [value]

        raise EndpointError(
            "cannot read corrected text from corrector response: %r" % (data,)
        )


def build_async_client(timeout: int) -> httpx.AsyncClient:
    """An ``httpx`` client configured for slow, serverless endpoints."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        limits=httpx.Limits(max_connections=32, max_keepalive_connections=8),
    )
