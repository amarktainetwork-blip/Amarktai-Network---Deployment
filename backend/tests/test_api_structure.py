"""
API Structure Tests
Validates that routes are properly structured and no duplicates exist
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_no_duplicate_auth_paths():
    """Ensure no /api/auth/auth/* path duplication"""
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi = response.json()
    paths = openapi.get("paths", {})
    
    # Check for duplicated auth paths
    duplicate_patterns = ["/api/auth/auth", "/api/api/"]
    
    for path in paths.keys():
        for pattern in duplicate_patterns:
            assert pattern not in path, f"Duplicate path detected: {path}"


def test_health_ping_exists():
    """Ensure /api/health/ping endpoint exists"""
    response = client.get("/api/health/ping")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_system_limits_endpoint():
    """Test /api/system/limits endpoint structure (auth required)"""
    # This will fail auth but should not 404
    response = client.get("/api/system/limits")
    # Should be 401 (unauthorized) not 404 (not found)
    assert response.status_code in [401, 403], "Limits endpoint should exist but require auth"


def test_bot_lifecycle_endpoints_exist():
    """Test that bot lifecycle endpoints are registered"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi = response.json()
    paths = openapi.get("paths", {})
    
    # Check for start/stop/pause endpoints
    expected_paths = [
        "/api/bots/{bot_id}/start",
        "/api/bots/{bot_id}/stop",
        "/api/bots/{bot_id}/pause",
        "/api/bots/{bot_id}/resume"
    ]
    
    for expected in expected_paths:
        assert expected in paths, f"Expected endpoint {expected} not found"


def test_analytics_pnl_timeseries():
    """Test /api/analytics/pnl_timeseries endpoint structure"""
    response = client.get("/api/analytics/pnl_timeseries")
    # Should be 401 (unauthorized) not 404
    assert response.status_code in [401, 403], "Analytics endpoint should exist but require auth"


def test_live_gate_endpoints():
    """Test live trading gate endpoints are registered"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi = response.json()
    paths = openapi.get("paths", {})
    
    expected_paths = [
        "/api/system/request-live",
        "/api/system/live-eligibility",
        "/api/system/start-paper-learning"
    ]
    
    for expected in expected_paths:
        assert expected in paths, f"Expected endpoint {expected} not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
