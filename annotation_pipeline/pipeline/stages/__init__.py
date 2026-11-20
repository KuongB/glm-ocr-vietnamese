"""Automated pipeline stages (everything before manual review)."""

from . import correct, ocr_draft

__all__ = ["ocr_draft", "correct"]
