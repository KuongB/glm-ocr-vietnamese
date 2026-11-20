"""Store, schema and export behaviour."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.export import export
from pipeline.schema import Record, RecordStatus, record_id
from pipeline.store import RecordStore


def test_scan_registers_only_images(store: RecordStore):
    assert len(store) == 3
    images = sorted(rec.image for rec in store)
    assert images == ["a.jpg", "b.png", "sub/c.jpg"]
    assert all(rec.status is RecordStatus.PENDING for rec in store)


def test_scan_is_idempotent(store: RecordStore, settings):
    added = store.scan_images(Path(settings.IMAGES_DIR), settings.image_suffixes)
    assert added == 0
    assert len(store) == 3


def test_scan_picks_up_new_images_without_touching_old(store: RecordStore, settings):
    images_dir = Path(settings.IMAGES_DIR)
    first = next(iter(store))
    first.mark(RecordStatus.APPROVED, final_text="done")

    (images_dir / "d.jpg").write_bytes(b"\x89PNG\r\n\x1a\n")
    added = store.scan_images(images_dir, settings.image_suffixes)

    assert added == 1
    assert store.get(first.id).status is RecordStatus.APPROVED
    assert store.get(first.id).final_text == "done"


def test_scan_missing_dir_raises(tmp_path: Path, settings):
    store = RecordStore(tmp_path / "m.jsonl")
    with pytest.raises(FileNotFoundError):
        store.scan_images(tmp_path / "nope", settings.image_suffixes)


def test_record_id_is_stable_and_path_separator_agnostic():
    assert record_id("sub/c.jpg") == record_id("sub\\c.jpg")
    assert Record.for_image("sub\\c.jpg").image == "sub/c.jpg"


def test_save_load_round_trip(store: RecordStore, settings):
    target = next(iter(store))
    target.mark(RecordStatus.CORRECTED, draft_text="toi di hoc", corrected_text="tôi đi học")
    store.save()

    reloaded = RecordStore.load(Path(settings.MANIFEST_PATH))
    assert len(reloaded) == 3
    restored = reloaded.get(target.id)
    assert restored.status is RecordStatus.CORRECTED
    assert restored.corrected_text == "tôi đi học"
    assert restored.was_corrected is True


def test_load_skips_corrupt_lines(tmp_path: Path):
    manifest = tmp_path / "m.jsonl"
    good = Record.for_image("a.jpg")
    manifest.write_text(
        good.model_dump_json() + "\n" + "{not json}\n" + "\n",
        encoding="utf-8",
    )
    store = RecordStore.load(manifest)
    assert len(store) == 1
    assert store.get(good.id) is not None


def test_save_is_atomic_and_leaves_no_temp_file(store: RecordStore, settings):
    store.save()
    manifest = Path(settings.MANIFEST_PATH)
    leftovers = list(manifest.parent.glob("*.tmp"))
    assert leftovers == []
    assert len(manifest.read_text(encoding="utf-8").strip().splitlines()) == 3


def test_with_status_respects_limit(store: RecordStore):
    assert len(store.with_status([RecordStatus.PENDING], limit=2)) == 2
    assert store.with_status([RecordStatus.APPROVED]) == []


def test_review_text_prefers_most_recent_stage():
    record = Record.for_image("a.jpg")
    assert record.review_text == ""
    record.draft_text = "draft"
    assert record.review_text == "draft"
    record.corrected_text = "corrected"
    assert record.review_text == "corrected"
    record.final_text = "final"
    assert record.review_text == "final"


def test_next_for_review_wraps_around(drafted_store: RecordStore):
    ids = drafted_store.ids()
    last = ids[-1]
    # Nothing follows the last record, so it should wrap to the first.
    nxt = drafted_store.next_for_review([RecordStatus.DRAFTED], after_id=last)
    assert nxt is not None
    assert nxt.id == ids[0]


def test_next_for_review_returns_none_when_queue_empty(store: RecordStore):
    assert store.next_for_review([RecordStatus.CORRECTED]) is None


def test_apply_review_approve_persists(drafted_store: RecordStore, settings):
    target = next(iter(drafted_store))
    drafted_store.apply_review(
        target.id,
        status=RecordStatus.APPROVED,
        final_text="  tôi đi học  ",
        reviewer="tester",
        note="clean",
    )
    reloaded = RecordStore.load(Path(settings.MANIFEST_PATH)).get(target.id)
    assert reloaded.status is RecordStatus.APPROVED
    assert reloaded.final_text == "  tôi đi học  "
    assert reloaded.reviewer == "tester"
    assert reloaded.reviewed_at is not None


def test_apply_review_reject_drops_final_text(drafted_store: RecordStore):
    target = next(iter(drafted_store))
    record = drafted_store.apply_review(
        target.id,
        status=RecordStatus.REJECTED,
        final_text="ignored",
        reviewer="tester",
        note="illegible",
    )
    assert record.status is RecordStatus.REJECTED
    assert record.final_text is None
    assert record.note == "illegible"


def test_apply_review_rejects_non_review_status(drafted_store: RecordStore):
    target = next(iter(drafted_store))
    with pytest.raises(ValueError):
        drafted_store.apply_review(
            target.id,
            status=RecordStatus.CORRECTED,
            final_text="x",
            reviewer="tester",
        )


def test_apply_review_unknown_id(store: RecordStore):
    with pytest.raises(KeyError):
        store.apply_review(
            "nope", status=RecordStatus.APPROVED, final_text="x", reviewer="t"
        )


def test_stats_counts_by_status(drafted_store: RecordStore):
    target = next(iter(drafted_store))
    target.mark(RecordStatus.APPROVED, final_text="ok")
    stats = drafted_store.stats()
    assert stats.total == 3
    assert stats.approved == 1
    assert stats.by_status["drafted"] == 2
    assert any("approved" in line for line in stats.as_lines())


# -- export ---------------------------------------------------------------


def test_export_only_includes_approved(drafted_store: RecordStore, settings):
    records = list(drafted_store)
    records[0].mark(RecordStatus.APPROVED, final_text=" tôi đi học ")
    records[1].mark(RecordStatus.REJECTED)
    # records[2] stays drafted

    summary = export(drafted_store, Path(settings.EXPORT_DIR))
    assert summary["exported"] == 1

    lines = Path(summary["dataset_jsonl"]).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["text"] == "tôi đi học"
    assert row["image"] == records[0].image

    labels = json.loads(Path(summary["label_json"]).read_text(encoding="utf-8"))
    assert labels == {records[0].image: "tôi đi học"}


def test_export_skips_approved_without_text(drafted_store: RecordStore, settings):
    record = next(iter(drafted_store))
    record.mark(RecordStatus.APPROVED, final_text="   ")
    summary = export(drafted_store, Path(settings.EXPORT_DIR))
    assert summary["exported"] == 0


def test_export_keys_label_json_by_relative_path(drafted_store: RecordStore, settings):
    """Same basename in two folders must not collapse into one label."""
    extra = Record.for_image("other/a.jpg")
    extra.mark(RecordStatus.APPROVED, final_text="second")
    drafted_store.put(extra)
    first = next(iter(drafted_store))
    first.mark(RecordStatus.APPROVED, final_text="first")

    summary = export(drafted_store, Path(settings.EXPORT_DIR))
    labels = json.loads(Path(summary["label_json"]).read_text(encoding="utf-8"))
    assert labels["a.jpg"] == "first"
    assert labels["other/a.jpg"] == "second"
    assert summary["exported"] == 2
