"""Tests for telemetry API pagination, filtering, and aggregation."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_paginated_listing_and_filtering(tmp_path):
    """Readings support page size and asset/metric filters."""
    db_path = tmp_path / "test.db"
    app = create_app(db_path=str(db_path))
    with TestClient(app) as client:
        response = client.get("/readings?page=1&page_size=2")
        assert response.status_code == 200
        payload = response.json()
        assert payload["pagination"]["page"] == 1
        assert payload["pagination"]["page_size"] == 2
        assert len(payload["items"]) == 2

        response = client.get("/readings?asset_id=PS-042&metric=flow_rate")
        assert response.status_code == 200
        items = response.json()["items"]
        assert all(item["asset_id"] == "PS-042" for item in items)
        assert all(item["metric"] == "flow_rate" for item in items)


def test_aggregation_respects_filters(tmp_path):
    """Aggregation results match the same asset and metric filters."""
    db_path = tmp_path / "test.db"
    app = create_app(db_path=str(db_path))
    with TestClient(app) as client:
        reading = client.get("/readings?page=1&page_size=1").json()["items"][0]
        response = client.get(
            f"/aggregation?asset_id={reading['asset_id']}&metric={reading['metric']}"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] >= 1
        assert payload["items"][0]["asset_id"] == reading["asset_id"]
        assert payload["items"][0]["metric"] == reading["metric"]


def test_aggregation_supports_pagination(tmp_path):
    """Aggregation returns paginated groups with metadata."""
    db_path = tmp_path / "test.db"
    app = create_app(db_path=str(db_path))
    with TestClient(app) as client:
        response = client.get("/aggregation?page=1&page_size=2")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["items"]) == 2
        assert payload["pagination"]["page"] == 1
        assert payload["pagination"]["page_size"] == 2
        assert payload["pagination"]["total"] == payload["count"]
        assert payload["pagination"]["pages"] >= 1


def test_invalid_time_range_returns_empty_results(tmp_path):
    """An inverted time range returns empty results instead of an error."""
    db_path = tmp_path / "test.db"
    app = create_app(db_path=str(db_path))
    with TestClient(app) as client:
        response = client.get(
            "/readings?start_time=2025-01-01T00:00:00Z&end_time=2024-01-01T00:00:00Z"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["items"] == []
        assert payload["pagination"]["total"] == 0
