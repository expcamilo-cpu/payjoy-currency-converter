from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from providers import ProviderError, UnsupportedCurrencyError

client = TestClient(app)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_happy_path_uses_primary_provider():
    with patch("providers.fetch_rate_from_exchangerate", return_value=Decimal("5.2281")):
        response = client.get("/convert?amount=200&currency=BRL")

    assert response.status_code == 200
    data = response.json()
    assert data["amount_usd"] == 200.0
    assert data["currency"] == "BRL"
    assert data["converted"] == 1045.62
    assert data["rate"] == 5.2281
    assert data["provider"] == "exchangerate-api"
    assert data["fallback_used"] is False


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_invalid_iso_code_returns_400():
    response = client.get("/convert?amount=200&currency=XYZ")
    assert response.status_code == 400
    assert "Invalid currency code" in response.json()["detail"]


def test_phl_is_rejected_because_it_is_not_iso_4217():
    """PHL is a common typo for Philippine peso; the correct ISO code is PHP."""
    response = client.get("/convert?amount=200&currency=PHL")
    assert response.status_code == 400
    assert "Invalid currency code" in response.json()["detail"]


def test_missing_amount_returns_422():
    response = client.get("/convert?currency=BRL")
    assert response.status_code == 422


def test_negative_amount_returns_422():
    response = client.get("/convert?amount=-50&currency=BRL")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Failover behavior
# ---------------------------------------------------------------------------

def test_primary_fails_fallback_succeeds():
    with (
        patch("providers.fetch_rate_from_exchangerate", side_effect=ProviderError("down")),
        patch("providers.fetch_rate_from_fastforex", return_value=Decimal("5.2290")),
    ):
        response = client.get("/convert?amount=200&currency=BRL")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "fastforex"
    assert data["fallback_used"] is True
    assert data["converted"] == 1045.80


def test_both_providers_fail_returns_502():
    with (
        patch("providers.fetch_rate_from_exchangerate", side_effect=ProviderError("down")),
        patch("providers.fetch_rate_from_fastforex", side_effect=ProviderError("down")),
    ):
        response = client.get("/convert?amount=200&currency=BRL")

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]


def test_currency_valid_iso_but_unsupported_returns_422():
    """A valid ISO code that neither provider knows about must be a client error, not a 5xx."""
    with (
        patch(
            "providers.fetch_rate_from_exchangerate",
            side_effect=UnsupportedCurrencyError("nope"),
        ),
        patch(
            "providers.fetch_rate_from_fastforex",
            side_effect=UnsupportedCurrencyError("nope"),
        ),
    ):
        response = client.get("/convert?amount=200&currency=BRL")

    assert response.status_code == 422
    assert "not supported" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["fallback_configured"] is True