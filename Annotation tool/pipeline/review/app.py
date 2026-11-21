"""Stage 3 -- manual review server.

A small FastAPI app serving a one-page reviewer UI: the image on one side, the
OCR draft and the SLM-corrected text on the other, with an editable box and
approve/reject/skip actions.

Every decision is written straight to the manifest, so closing the browser
mid-session loses nothing. The server is meant to be run locally by one
reviewer at a time; it takes a lock around manifest writes but does not try to
coordinate several concurrent reviewers over the same file.
"""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..config import Settings
from ..schema import REVIEW_INPUT_STATUSES, Record, RecordStatus
from ..store import RecordStore

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ReviewDecision(BaseModel):
    """What the reviewer sent back for one record."""

    status: RecordStatus
    final_text: Optional[str] = None
    note: Optional[str] = None


def _record_payload(record: Record, images_dir: Path) -> Dict[str, Any]:
    return {
        "id": record.id,
        "image": record.image,
        "image_url": "/api/image/%s" % record.id,
        "status": record.status.value,
        "draft_text": record.draft_text,
        "corrected_text": record.corrected_text,
        "review_text": record.review_text,
        "was_corrected": record.was_corrected,
        "note": record.note,
        "exists": (images_dir / record.image).exists(),
    }


def _safe_image_path(images_dir: Path, relative: str) -> Path:
    """Resolve an image path, refusing anything outside ``images_dir``."""
    root = images_dir.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise HTTPException(status_code=400, detail="image path outside images dir")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="image file not found")
    return candidate


def create_app(store: RecordStore, settings: Settings) -> FastAPI:
    """Build the review app around an already-loaded store."""
    app = FastAPI(title="Annotation review", docs_url="/api/docs")
    images_dir = Path(settings.IMAGES_DIR)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        page = STATIC_DIR / "index.html"
        if not page.exists():
            raise HTTPException(status_code=500, detail="review UI is missing")
        return HTMLResponse(page.read_text(encoding="utf-8"))

    @app.get("/api/stats")
    async def stats() -> JSONResponse:
        snapshot = store.stats()
        return JSONResponse(
            {
                "total": snapshot.total,
                "by_status": snapshot.by_status,
                "remaining": sum(
                    snapshot.by_status.get(s.value, 0) for s in REVIEW_INPUT_STATUSES
                ),
                "reviewer": settings.REVIEWER_NAME,
            }
        )

    @app.get("/api/next")
    async def next_record(after: Optional[str] = None) -> JSONResponse:
        record = store.next_for_review(REVIEW_INPUT_STATUSES, after_id=after)
        if record is None:
            return JSONResponse({"record": None})
        return JSONResponse({"record": _record_payload(record, images_dir)})

    @app.get("/api/record/{record_id}")
    async def one_record(record_id: str) -> JSONResponse:
        record = store.get(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="no such record")
        return JSONResponse({"record": _record_payload(record, images_dir)})

    @app.get("/api/image/{record_id}")
    async def image(record_id: str) -> FileResponse:
        record = store.get(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="no such record")
        path = _safe_image_path(images_dir, record.image)
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return FileResponse(path, media_type=media_type)

    @app.post("/api/review/{record_id}")
    async def review(record_id: str, decision: ReviewDecision) -> JSONResponse:
        if decision.status is RecordStatus.APPROVED and not (
            decision.final_text or ""
        ).strip():
            raise HTTPException(
                status_code=400,
                detail="approved records need non-empty text (reject it instead)",
            )
        try:
            record = store.apply_review(
                record_id,
                status=decision.status,
                final_text=decision.final_text,
                reviewer=settings.REVIEWER_NAME,
                note=decision.note,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="no such record") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None

        logger.info("%s -> %s", record.id, record.status.value)
        nxt = store.next_for_review(REVIEW_INPUT_STATUSES, after_id=record_id)
        return JSONResponse(
            {
                "record": _record_payload(record, images_dir),
                "next": _record_payload(nxt, images_dir) if nxt else None,
            }
        )

    return app


def serve(store: RecordStore, settings: Settings) -> None:
    """Run the review server with uvicorn (blocking)."""
    import uvicorn

    app = create_app(store, settings)
    print(
        "Review UI: http://%s:%d  (%d record(s) awaiting review)"
        % (
            settings.REVIEW_HOST,
            settings.REVIEW_PORT,
            len(store.with_status(REVIEW_INPUT_STATUSES)),
        )
    )
    uvicorn.run(app, host=settings.REVIEW_HOST, port=settings.REVIEW_PORT, log_level="info")
