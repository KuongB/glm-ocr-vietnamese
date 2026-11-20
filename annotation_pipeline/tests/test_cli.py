"""The run_pipeline.py command line, driven in-process."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_pipeline
from pipeline.config import Settings
from pipeline.schema import RecordStatus
from pipeline.store import RecordStore


@pytest.fixture
def cli(monkeypatch, settings: Settings):
    """Run main() with our tmp_path-scoped settings instead of the real .env."""
    monkeypatch.setattr(run_pipeline, "get_settings", lambda: settings)
    return run_pipeline.main


def test_scan_then_status(cli, settings, capsys):
    assert cli(["scan"]) == 0
    out = capsys.readouterr().out
    assert "3 new record(s)" in out

    assert cli(["status"]) == 0
    out = capsys.readouterr().out
    assert "total: 3" in out
    assert "pending" in out
    assert "awaiting review: 0" in out


def test_scan_twice_adds_nothing(cli, capsys):
    cli(["scan"])
    capsys.readouterr()
    assert cli(["scan"]) == 0
    assert "0 new record(s)" in capsys.readouterr().out


def test_scan_missing_images_dir_reports_cleanly(cli, settings, capsys, tmp_path):
    settings.IMAGES_DIR = tmp_path / "gone"
    assert cli(["scan"]) == 1
    assert "images directory not found" in capsys.readouterr().err


def test_ocr_without_url_reports_cleanly(cli, settings, capsys):
    cli(["scan"])
    capsys.readouterr()
    settings.OCR_API_URL = ""
    assert cli(["ocr"]) == 1
    assert "OCR_API_URL is not set" in capsys.readouterr().err


def test_review_with_empty_queue_exits_without_serving(cli, capsys):
    cli(["scan"])
    capsys.readouterr()
    assert cli(["review"]) == 0
    assert "Nothing to review" in capsys.readouterr().out


def test_export_writes_approved_pairs(cli, settings, capsys, tmp_path):
    cli(["scan"])
    capsys.readouterr()

    store = RecordStore.load(Path(settings.MANIFEST_PATH))
    target = next(iter(store))
    target.mark(RecordStatus.APPROVED, final_text="tôi đi học")
    store.save()

    out_dir = tmp_path / "out"
    assert cli(["export", "--out", str(out_dir)]) == 0
    assert "exported" in capsys.readouterr().out

    rows = (out_dir / "dataset.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    assert json.loads(rows[0])["text"] == "tôi đi học"

    labels = json.loads((out_dir / "label.json").read_text(encoding="utf-8"))
    assert labels == {target.image: "tôi đi học"}


def test_status_counts_review_queue(cli, settings, capsys):
    cli(["scan"])
    store = RecordStore.load(Path(settings.MANIFEST_PATH))
    for record in store:
        record.mark(RecordStatus.CORRECTED, draft_text="a", corrected_text="b")
    store.save()
    capsys.readouterr()

    assert cli(["status"]) == 0
    assert "awaiting review: 3" in capsys.readouterr().out


def test_unknown_command_exits_nonzero(cli):
    with pytest.raises(SystemExit) as excinfo:
        cli(["nope"])
    assert excinfo.value.code != 0


def test_no_command_exits_nonzero(cli):
    with pytest.raises(SystemExit) as excinfo:
        cli([])
    assert excinfo.value.code != 0


def test_every_subcommand_is_wired(cli):
    """Each parser subcommand must have a handler in COMMANDS."""
    parser = run_pipeline.build_parser()
    subparsers = [
        action
        for action in parser._actions
        if isinstance(action, type(parser._subparsers._group_actions[0]))
    ]
    names = set(subparsers[0].choices)
    assert names == set(run_pipeline.COMMANDS)
