"""Pipeline configuration.

Values come from the environment or an ``.env`` file next to the pipeline
folder. Only the two endpoint URLs normally need setting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PIPELINE_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Pipeline settings."""

    model_config = SettingsConfigDict(
        env_file=str(PIPELINE_ROOT / ".env"),
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
    )

    # -- stage 1: OCR endpoint (the GLM-OCR model on Modal) ---------------
    OCR_API_URL: str = ""
    OCR_API_TOKEN: str = ""

    # -- stage 2: SLM spelling-correction endpoint -----------------------
    # Hosted separately; the pipeline only ever POSTs text to it.
    CORRECTOR_API_URL: str = ""
    CORRECTOR_API_TOKEN: str = ""
    #: How many texts to send per correction request.
    CORRECTOR_BATCH_SIZE: int = 16

    # -- shared HTTP behaviour -------------------------------------------
    REQUEST_TIMEOUT: int = 120
    MAX_RETRIES: int = 3
    #: Concurrent in-flight requests per stage.
    CONCURRENCY: int = 4

    # -- data layout ------------------------------------------------------
    #: Root directory holding the images to annotate.
    IMAGES_DIR: Path = Field(default=PIPELINE_ROOT / "data" / "images")
    #: JSONL manifest holding one record per image.
    MANIFEST_PATH: Path = Field(default=PIPELINE_ROOT / "data" / "manifest.jsonl")
    #: Where `export` writes the approved annotations.
    EXPORT_DIR: Path = Field(default=PIPELINE_ROOT / "data" / "export")

    #: Image extensions picked up when scanning IMAGES_DIR.
    IMAGE_SUFFIXES: str = ".jpg,.jpeg,.png,.bmp,.webp,.tif,.tiff"

    # -- review server ----------------------------------------------------
    REVIEW_HOST: str = "127.0.0.1"
    REVIEW_PORT: int = 8100
    #: Recorded on each record the reviewer signs off on.
    REVIEWER_NAME: str = "reviewer"

    @property
    def image_suffixes(self) -> tuple[str, ...]:
        return tuple(
            s.strip().lower()
            for s in self.IMAGE_SUFFIXES.split(",")
            if s.strip()
        )

    def require(self, name: str) -> str:
        """Return a required setting or raise with an actionable message."""
        value = getattr(self, name, "")
        if not value:
            raise RuntimeError(
                "%s is not set. Add it to %s or export it in your shell."
                % (name, PIPELINE_ROOT / ".env")
            )
        return str(value)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Process-wide settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Drop the cached settings. Used by the tests."""
    global _settings
    _settings = None
