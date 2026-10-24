import pytest
from fastapi.testclient import TestClient
from dashboard_server import app, bridge

@pytest.fixture
def client():
    return TestClient(app)

def test_dashboard_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Autonomous Closed-Loop Orchestration" in res.text

def test_dashboard_status_route(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "system_state" in data
    assert data["active_services"] == 5

def test_dashboard_topology_route(client):
    res = client.get("/api/topology")
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) == 5
    assert len(data["edges"]) == 4

def test_dashboard_fault_injection(client):
    res = client.post("/api/fault/inject", json={"scenario": "retry_storm", "retries": 15})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"

def test_dashboard_config_update(client):
    res = client.post("/api/pipeline/config", json={"window": 2.0, "threshold": 12, "stage2_delay": 3.0})
    assert res.status_code == 200
    assert bridge.pipeline.window_s == 2.0
    assert bridge.pipeline.threshold == 12
    assert bridge.pipeline.stage2_delay == 3.0

def test_dashboard_xdp_status(client):
    res = client.get("/api/xdp/status")
    assert res.status_code == 200
    data = res.json()
    assert "hook_layer" in data
    assert "OSI Layer 2" in data["hook_layer"]
    assert "sk_buff_allocation" in data
    assert "BYPASSED" in data["sk_buff_allocation"]

def test_dashboard_benchmark_route(client):
    res = client.post("/api/benchmark/run")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"

    res_latest = client.get("/api/benchmark/latest")
    assert res_latest.status_code == 200

