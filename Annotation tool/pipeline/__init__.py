"""Multi-stage annotation pipeline for a Vietnamese handwriting dataset.

Stage 1  semi-automatic OCR         -> draft transcription   (pipeline.stages.ocr_draft)
Stage 2  SLM spelling correction    -> corrected text        (pipeline.stages.correct)
Stage 3  manual review              -> approved annotation   (pipeline.review)

Both models live behind HTTP endpoints, so this package has no ML dependencies.
"""

__all__ = ["clients", "config", "export", "schema", "store"]

__version__ = "0.1.0"
