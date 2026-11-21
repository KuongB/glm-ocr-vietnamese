"""Command-line entry point for the annotation pipeline.

    python run_pipeline.py scan                 # register images as pending records
    python run_pipeline.py ocr                  # stage 1: draft transcriptions
    python run_pipeline.py correct              # stage 2: SLM spelling correction
    python run_pipeline.py review               # stage 3: open the review UI
    python run_pipeline.py export               # write the approved pairs out
    python run_pipeline.py status               # status counts
    python run_pipeline.py auto                 # scan + ocr + correct, then stop

Every command is safe to re-run: stages only pick up records sitting in the
status they expect.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from pipeline import export as export_mod
from pipeline.config import Settings, get_settings
from pipeline.review import serve as serve_review
from pipeline.schema import REVIEW_INPUT_STATUSES
from pipeline.stages import correct, ocr_draft
from pipeline.store import RecordStore


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # httpx logs every request at INFO, which drowns out progress lines.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _load(settings: Settings) -> RecordStore:
    store = RecordStore.load(Path(settings.MANIFEST_PATH))
    logging.getLogger(__name__).info(
        "manifest: %s (%d record(s))", settings.MANIFEST_PATH, len(store)
    )
    return store


def _print_summary(title: str, summary: dict) -> None:
    print("\n%s" % title)
    for key, value in summary.items():
        print("  %-12s %s" % (key, value))


# -- commands -------------------------------------------------------------


def cmd_scan(args: argparse.Namespace, settings: Settings) -> int:
    store = _load(settings)
    added = store.scan_images(Path(settings.IMAGES_DIR), settings.image_suffixes)
    store.save()
    print(
        "scanned %s: %d new record(s), %d total"
        % (settings.IMAGES_DIR, added, len(store))
    )
    return 0


def cmd_ocr(args: argparse.Namespace, settings: Settings) -> int:
    store = _load(settings)
    summary = asyncio.run(ocr_draft.run(store, settings, limit=args.limit))
    store.save()
    _print_summary("stage 1 (ocr)", summary)
    return 1 if summary["failed"] and not summary["drafted"] else 0


def cmd_correct(args: argparse.Namespace, settings: Settings) -> int:
    store = _load(settings)
    summary = asyncio.run(correct.run(store, settings, limit=args.limit))
    store.save()
    _print_summary("stage 2 (correct)", summary)
    return 1 if summary["failed"] and not summary["corrected"] else 0


def cmd_review(args: argparse.Namespace, settings: Settings) -> int:
    store = _load(settings)
    pending = store.with_status(REVIEW_INPUT_STATUSES)
    if not pending:
        print(
            "Nothing to review. Run 'ocr' and 'correct' first, "
            "or 'status' to see where records are."
        )
        return 0
    if args.reviewer:
        settings.REVIEWER_NAME = args.reviewer
    serve_review(store, settings)
    return 0


def cmd_export(args: argparse.Namespace, settings: Settings) -> int:
    store = _load(settings)
    out_dir = Path(args.out) if args.out else Path(settings.EXPORT_DIR)
    summary = export_mod.export(store, out_dir)
    _print_summary("export", summary)
    return 0


def cmd_status(args: argparse.Namespace, settings: Settings) -> int:
    store = _load(settings)
    stats = store.stats()
    print("\n".join(stats.as_lines()))
    awaiting = len(store.with_status(REVIEW_INPUT_STATUSES))
    print("\nawaiting review: %d" % awaiting)
    return 0


def cmd_auto(args: argparse.Namespace, settings: Settings) -> int:
    """scan -> ocr -> correct, stopping before the human stage."""
    store = _load(settings)

    added = store.scan_images(Path(settings.IMAGES_DIR), settings.image_suffixes)
    store.save()
    print("scan: %d new record(s)" % added)

    ocr_summary = asyncio.run(ocr_draft.run(store, settings, limit=args.limit))
    store.save()
    _print_summary("stage 1 (ocr)", ocr_summary)

    correct_summary = asyncio.run(correct.run(store, settings, limit=args.limit))
    store.save()
    _print_summary("stage 2 (correct)", correct_summary)

    awaiting = len(store.with_status(REVIEW_INPUT_STATUSES))
    print("\n%d record(s) ready for review -- run: python run_pipeline.py review" % awaiting)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_pipeline.py",
        description="Multi-stage annotation pipeline for Vietnamese handwriting.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("scan", help="register images in IMAGES_DIR as pending records")

    p_ocr = subparsers.add_parser("ocr", help="stage 1: draft transcriptions via the OCR endpoint")
    p_ocr.add_argument("--limit", type=int, default=None, help="process at most N records")

    p_correct = subparsers.add_parser("correct", help="stage 2: SLM spelling correction")
    p_correct.add_argument("--limit", type=int, default=None, help="process at most N records")

    p_review = subparsers.add_parser("review", help="stage 3: serve the manual review UI")
    p_review.add_argument("--reviewer", default=None, help="name recorded on each decision")

    p_export = subparsers.add_parser("export", help="write approved image-text pairs")
    p_export.add_argument("--out", default=None, help="output directory")

    subparsers.add_parser("status", help="show status counts")

    p_auto = subparsers.add_parser("auto", help="scan + ocr + correct in one go")
    p_auto.add_argument("--limit", type=int, default=None, help="process at most N records")

    return parser


COMMANDS = {
    "scan": cmd_scan,
    "ocr": cmd_ocr,
    "correct": cmd_correct,
    "review": cmd_review,
    "export": cmd_export,
    "status": cmd_status,
    "auto": cmd_auto,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    settings = get_settings()

    try:
        return COMMANDS[args.command](args, settings)
    except KeyboardInterrupt:
        print("\ninterrupted; progress up to the last flush is saved", file=sys.stderr)
        return 130
    except (RuntimeError, FileNotFoundError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
