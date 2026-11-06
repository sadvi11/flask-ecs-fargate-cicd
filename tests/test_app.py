import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from app import app  # noqa: E402


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


def test_home(client):
    assert client.get("/").status_code == 200


def test_calculate_matches_readme_example(client):
    resp = client.post("/calculate", json={"principal": 500000, "annual_rate": 5.5, "years": 25})
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["monthly_payment"] == 3070.44
    assert body["total_payment"] == pytest.approx(3070.44 * 300, abs=1.0)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"principal": 1000, "annual_rate": 5},
        {"principal": 1000, "annual_rate": 0, "years": 5},  # would divide by zero
        {"principal": -1, "annual_rate": 5, "years": 5},
        {"principal": "1000", "annual_rate": 5, "years": 5},
        {"principal": True, "annual_rate": 5, "years": 5},
        {"principal": 1000, "annual_rate": 5000, "years": 5},
        {"principal": 1000, "annual_rate": 5, "years": 10_000},
    ],
)
def test_calculate_rejects_invalid_input(client, payload):
    resp = client.post("/calculate", json=payload)
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.parametrize("kwargs", [
    {"data": "not json", "content_type": "application/json"},
    {"data": "[1, 2]", "content_type": "application/json"},
    {"data": "x", "content_type": "text/plain"},
])
def test_calculate_rejects_non_object_body(client, kwargs):
    assert client.post("/calculate", **kwargs).status_code == 400
