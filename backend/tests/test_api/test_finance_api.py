import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_unauthorized_finance_routes():
    res = client.get("/api/v1/finance/health")
    assert res.status_code == 401  # Requires JWT authorization header
