"""Stage 3 review server."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pipeline.review import create_app
from pipeline.schema import RecordStatus
from pipeline.store import RecordStore


@pytest.fixture
def corrected_store(drafted_store: RecordStore) -> RecordStore:
    for index, record in enumerate(drafted_store):
        record.mark(
            RecordStatus.CORRECTED,
            draft_text="toi di hoc %d" % index,
            corrected_text="tôi đi học %d" % index,
        )
    drafted_store.save()
    return drafted_store


@pytest.fixture
def client(corrected_store: RecordStore, settings) -> TestClient:
    return TestClient(create_app(corrected_store, settings))


def test_index_serves_the_ui(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Annotation review" in response.text


def test_stats_reports_review_queue(client: TestClient):
    body = client.get("/api/stats").json()
    assert body["total"] == 3
    assert body["remaining"] == 3
    assert body["reviewer"] == "tester"


def test_next_returns_a_reviewable_record(client: TestClient):
    record = client.get("/api/next").json()["record"]
    assert record["status"] == "corrected"
    assert record["draft_text"].startswith("toi di hoc")
    assert record["review_text"].startswith("tôi đi học")
    assert record["was_corrected"] is True
    assert record["exists"] is True


def test_next_after_skips_forward(client: TestClient, corrected_store: RecordStore):
    first = client.get("/api/next").json()["record"]
    second = client.get("/api/next", params={"after": first["id"]}).json()["record"]
    assert second["id"] != first["id"]


def test_image_is_served(client: TestClient):
    record = client.get("/api/next").json()["record"]
    response = client.get(record["image_url"])
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


def test_image_404_for_unknown_record(client: TestClient):
    assert client.get("/api/image/doesnotexist").status_code == 404


def test_image_404_when_file_removed(client: TestClient, settings):
    record = client.get("/api/next").json()["record"]
    (Path(settings.IMAGES_DIR) / record["image"]).unlink()
    assert client.get(record["image_url"]).status_code == 404


def test_image_path_traversal_is_refused(
    client: TestClient, corrected_store: RecordStore, tmp_path: Path
):
    """A manifest entry pointing outside IMAGES_DIR must not be served."""
    secret = tmp_path / "secret.txt"
    secret.write_text("private", encoding="utf-8")

    record = next(iter(corrected_store))
    record.image = "../secret.txt"

    response = client.get("/api/image/%s" % record.id)
    assert response.status_code == 400
    assert "outside" in response.json()["detail"]


def test_approve_saves_edited_text_and_returns_next(
    client: TestClient, settings
):
    record = client.get("/api/next").json()["record"]
    response = client.post(
        "/api/review/%s" % record["id"],
        json={"status": "approved", "final_text": "văn bản đã sửa", "note": "ok"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["record"]["status"] == "approved"
    assert body["next"] is not None
    assert body["next"]["id"] != record["id"]

    reloaded = RecordStore.load(Path(settings.MANIFEST_PATH)).get(record["id"])
    assert reloaded.final_text == "văn bản đã sửa"
    assert reloaded.reviewer == "tester"
    assert reloaded.note == "ok"


def test_reject_records_the_note(client: TestClient, settings):
    record = client.get("/api/next").json()["record"]
    response = client.post(
        "/api/review/%s" % record["id"],
        json={"status": "rejected", "final_text": "ignored", "note": "illegible"},
    )
    assert response.status_code == 200
    assert response.json()["record"]["status"] == "rejected"

    reloaded = RecordStore.load(Path(settings.MANIFEST_PATH)).get(record["id"])
    assert reloaded.final_text is None
    assert reloaded.note == "illegible"


def test_approve_with_blank_text_is_refused(client: TestClient):
    record = client.get("/api/next").json()["record"]
    response = client.post(
        "/api/review/%s" % record["id"],
        json={"status": "approved", "final_text": "   "},
    )
    assert response.status_code == 400
    assert "non-empty" in response.json()["detail"]


def test_review_with_non_review_status_is_refused(client: TestClient):
    record = client.get("/api/next").json()["record"]
    response = client.post(
        "/api/review/%s" % record["id"],
        json={"status": "corrected", "final_text": "x"},
    )
    assert response.status_code == 400


def test_review_unknown_record_404(client: TestClient):
    response = client.post(
        "/api/review/doesnotexist",
        json={"status": "approved", "final_text": "x"},
    )
    assert response.status_code == 404


def test_queue_drains_to_empty(client: TestClient):
    for _ in range(3):
        record = client.get("/api/next").json()["record"]
        assert record is not None
        client.post(
            "/api/review/%s" % record["id"],
            json={"status": "approved", "final_text": "ok"},
        )

    assert client.get("/api/next").json()["record"] is None
    assert client.get("/api/stats").json()["remaining"] == 0


def test_drafted_records_are_reviewable_too(store: RecordStore, settings):
    """If stage 2 is skipped, the reviewer still sees the raw draft."""
    for record in store:
        record.mark(RecordStatus.DRAFTED, draft_text="raw draft")
    store.save()

    with TestClient(create_app(store, settings)) as client:
        record = client.get("/api/next").json()["record"]

    assert record["status"] == "drafted"
    assert record["corrected_text"] is None
    assert record["review_text"] == "raw draft"
    assert record["was_corrected"] is False
