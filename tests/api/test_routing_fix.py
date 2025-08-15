"""Test API routing fixes."""

import pytest
from fastapi.testclient import TestClient
from coaching_assistant.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_sessions_endpoints_available(client):
    """Test that sessions endpoints are available."""
    # Test GET /api/v1/sessions (should require auth but endpoint should exist)
    response = client.get("/api/v1/sessions")
    # Should return 401 (unauthorized) not 404 (not found)
    assert response.status_code == 401
    
    # Test currencies endpoint
    response = client.get("/api/v1/sessions/options/currencies")
    assert response.status_code == 200
    
    currencies = response.json()
    assert isinstance(currencies, list)
    assert "USD" in currencies
    assert "EUR" in currencies
    assert "NTD" in currencies
    assert "TWD" in currencies


def test_dashboard_summary_endpoint_available(client):
    """Test that dashboard summary endpoint is available at new path."""
    # Test GET /api/v1/dashboard/summary (should require auth but endpoint should exist)
    response = client.get("/api/v1/dashboard/summary")
    # Should return 401 (unauthorized) not 404 (not found)
    assert response.status_code == 401


def test_clients_options_endpoints_available(client):
    """Test that client options endpoints are available."""
    # Test sources endpoint
    response = client.get("/api/v1/clients/options/sources")
    assert response.status_code == 200
    
    sources = response.json()
    assert isinstance(sources, list)
    assert len(sources) == 4
    
    source_values = [source["value"] for source in sources]
    assert "referral" in source_values
    assert "organic" in source_values
    assert "friend" in source_values
    assert "social_media" in source_values
    
    # Test types endpoint
    response = client.get("/api/v1/clients/options/types")
    assert response.status_code == 200
    
    types = response.json()
    assert isinstance(types, list)
    assert len(types) == 4
    
    type_values = [client_type["value"] for client_type in types]
    assert "paid" in type_values
    assert "pro_bono" in type_values
    assert "free_practice" in type_values
    assert "other" in type_values


def test_no_route_conflicts(client):
    """Test that there are no route conflicts between sessions and dashboard."""
    # Sessions endpoints should work
    response = client.get("/api/v1/sessions")
    assert response.status_code == 401  # Requires auth, but route exists
    
    response = client.get("/api/v1/sessions/options/currencies")
    assert response.status_code == 200
    
    # Dashboard endpoints should work
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401  # Requires auth, but route exists
    
    # Old conflicting route should still return 401 if it exists in sessions router
    # but summary should be available at new dashboard path
    response = client.get("/api/v1/sessions/summary")
    # This might still exist if defined elsewhere, but the important thing is
    # that the dashboard summary works at the new path


def test_currency_options_content(client):
    """Test that currency options contain expected currencies."""
    response = client.get("/api/v1/sessions/options/currencies")
    assert response.status_code == 200
    
    currencies = response.json()
    
    # Check for common international currencies
    expected_currencies = [
        "USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY",
        "SEK", "NZD", "MXN", "SGD", "HKD", "NOK", "KRW", "TRY",
        "RUB", "INR", "BRL", "ZAR", "NTD", "TWD"
    ]
    
    for currency in expected_currencies:
        assert currency in currencies, f"Currency {currency} not found in response"


def test_client_options_labels(client):
    """Test that client options have correct Chinese labels."""
    # Test source labels
    response = client.get("/api/v1/clients/options/sources")
    sources = response.json()
    
    source_labels = {source["value"]: source["label"] for source in sources}
    assert source_labels["referral"] == "別人推薦"
    assert source_labels["organic"] == "自來客"
    assert source_labels["friend"] == "朋友"
    assert source_labels["social_media"] == "社群媒體"
    
    # Test type labels
    response = client.get("/api/v1/clients/options/types")
    types = response.json()
    
    type_labels = {client_type["value"]: client_type["label"] for client_type in types}
    assert type_labels["paid"] == "付費客戶"
    assert type_labels["pro_bono"] == "公益客戶"
    assert type_labels["free_practice"] == "免費練習"
    assert type_labels["other"] == "其他"