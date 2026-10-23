import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import pytest
import networkx as nx
from collector.namespace_resolver import NamespaceResolver
from engine.loop_detector import ThreadDynamicsGraphEngine
from engine.topology_graph import TopologyGraph
from engine.rca_engine import RootCauseAnalysisEngine
from actuator.cgroup_actuator import Cgroupv2Actuator
from actuator.docker_actuator import DockerApiActuator
from actuator.netedit_actuator import NetEditBpfAdapter
from controller import RemediationPipeline

# --- 1. Collector & Namespace Resolver Tests ---

def test_namespace_resolver_mock_registry():
    assert NamespaceResolver.resolve_pid_to_container_id(4812) == "d4a8c91f021e"
    assert NamespaceResolver.resolve_pid_to_container_id(999999) == "host"

def test_namespace_resolver_service_name():
    assert NamespaceResolver.resolve_service_name("d4a8c91f021e") == "orders-service"
    assert NamespaceResolver.resolve_service_name("unknown_cid", comm="custom-svc") == "custom-svc"

def test_cgroup_v2_path():
    path = NamespaceResolver.get_cgroup_v2_path("d4a8c91f021e")
    assert "d4a8c91f021e" in path

# --- 2. Sliding Window Loop Detector Tests ---

def test_graph_engine_no_anomaly_below_threshold():
    engine = ThreadDynamicsGraphEngine(window_seconds=1.5, min_retry_threshold=10)
    now = time.time()
    for i in range(5):
        engine.record_event(pid=1001, comm="svc", container_id="cid123", target_endpoint="10.0.0.1:80", timestamp=now + (i * 0.1))

    g, anomalies = engine.evaluate_operational_loops(now + 0.6)
    assert len(anomalies) == 0

def test_graph_engine_detects_anomaly_above_threshold():
    engine = ThreadDynamicsGraphEngine(window_seconds=1.5, min_retry_threshold=10)
    now = time.time()
    for i in range(12):
        engine.record_event(pid=1001, comm="svc", container_id="cid123", target_endpoint="10.0.0.1:80", timestamp=now + (i * 0.05))

    g, anomalies = engine.evaluate_operational_loops(now + 0.7)
    assert len(anomalies) == 1
    assert anomalies[0]["pid"] == 1001
    assert anomalies[0]["retry_count"] == 12
    assert anomalies[0]["hysteresis_confirmed"] is True
    assert g.has_node("proc:1001:svc")
    assert g.has_node("endpoint:10.0.0.1:80")
    assert g.has_edge("proc:1001:svc", "endpoint:10.0.0.1:80")

def test_graph_engine_sliding_window_eviction():
    engine = ThreadDynamicsGraphEngine(window_seconds=1.0, min_retry_threshold=5)
    t0 = 1000.0
    for i in range(5):
        engine.record_event(pid=1001, comm="svc", container_id="cid123", target_endpoint="10.0.0.1:80", timestamp=t0 + i * 0.05)

    g, anomalies = engine.evaluate_operational_loops(t0 + 2.0)
    assert len(anomalies) == 0

# --- 3. NetEdit BpfAdapter & Actuator Tests ---

def test_netedit_microsecond_traffic_drain():
    NetEditBpfAdapter.clear_registry()
    metrics = NetEditBpfAdapter.drain_traffic("10.0.1.20", 8080)
    assert metrics["draining"] is True
    assert metrics["latency_us"] < 1000.0 # < 1 millisecond SLA
    assert NetEditBpfAdapter.is_draining("10.0.1.20", 8080) is True

    restored = NetEditBpfAdapter.restore_traffic("10.0.1.20", 8080)
    assert restored is True
    assert NetEditBpfAdapter.is_draining("10.0.1.20", 8080) is False

def test_cgroup_actuator_handles_missing_path(tmp_path):
    res = Cgroupv2Actuator.apply_cpu_quota(str(tmp_path / "nonexistent"), quota_pct=10)
    assert res is False

def test_cgroup_actuator_writes_quota(tmp_path):
    cgroup_dir = tmp_path / "cgroup_test"
    cgroup_dir.mkdir()
    cpu_max = cgroup_dir / "cpu.max"
    cpu_max.write_text("max 100000\n")

    res = Cgroupv2Actuator.apply_cpu_quota(str(cgroup_dir), quota_pct=20)
    assert res is True
    content = cpu_max.read_text()
    assert content.strip() == "20000 100000"

def test_docker_actuator_safe_fallbacks():
    # Verify methods execute without unhandled exceptions in mock/test environment
    assert DockerApiActuator.pause_container("mock_cid_123") is True
    assert DockerApiActuator.restart_container("mock_cid_123") is True
    assert DockerApiActuator.evict_container("mock_cid_123", pod_name="orders-pod") is True

# --- 4. CrossTrace Dynamic Topology & k-Hop Slicing Tests ---

def test_topology_graph_crosstrace_spans_and_subgraph():
    topo = TopologyGraph()
    # Build 4-tier chain: A -> B -> C -> D
    topo.record_span("svc-A", "svc-B", span_id=1, latency_ms=5.0)
    topo.record_span("svc-B", "svc-C", span_id=2, latency_ms=10.0)
    topo.record_span("svc-C", "svc-D", span_id=3, latency_ms=2.0)
    topo.record_span("svc-X", "svc-Y", span_id=9, latency_ms=1.0) # Unconnected island

    assert topo.G.number_of_nodes() == 6
    assert topo.G.has_edge("svc-A", "svc-B")

    # 1-hop subgraph around B: should include A, B, C
    sub1 = topo.get_k_hop_subgraph("svc-B", k=1)
    assert set(sub1.nodes()) == {"svc-A", "svc-B", "svc-C"}
    assert "svc-D" not in sub1
    assert "svc-X" not in sub1

    # 2-hop subgraph around B: should include A, B, C, D (not X, Y)
    sub2 = topo.get_k_hop_subgraph("svc-B", k=2)
    assert set(sub2.nodes()) == {"svc-A", "svc-B", "svc-C", "svc-D"}
    assert "svc-X" not in sub2

# --- 5. TORAI TCORW & CARAF Residual Classifier Tests ---

def test_rca_engine_anomaly_scoring():
    # Normal metrics
    score_normal = RootCauseAnalysisEngine.compute_anomaly_score({
        "sk_rmem_alloc": 100,
        "sk_rcvbuf": 1048576,
        "stall_duration_ns": 0,
        "retry_count": 1
    })
    assert score_normal == 1.0

    # Starvation + Deadlock metrics
    score_critical = RootCauseAnalysisEngine.compute_anomaly_score({
        "sk_rmem_alloc": 1048576, # 100% full
        "sk_rcvbuf": 1048576,
        "stall_duration_ns": 120_000_000, # 120ms futex block
        "retry_count": 15
    })
    assert score_critical > score_normal * 10

def test_rca_engine_tcorw_pagerank_convergence():
    engine = RootCauseAnalysisEngine(damping_factor=0.85)
    topo = nx.DiGraph()
    topo.add_edge("gateway", "orders")
    topo.add_edge("orders", "inventory")
    topo.add_edge("orders", "redis")

    node_metrics = {
        "gateway": {"sk_rmem_alloc": 0, "sk_rcvbuf": 1048576, "stall_duration_ns": 0},
        "orders": {"sk_rmem_alloc": 1048576, "sk_rcvbuf": 1048576, "stall_duration_ns": 150_000_000}, # Heavy anomaly
        "inventory": {"sk_rmem_alloc": 0, "sk_rcvbuf": 1048576, "stall_duration_ns": 0},
        "redis": {"sk_rmem_alloc": 0, "sk_rcvbuf": 1048576, "stall_duration_ns": 0}
    }

    rankings = engine.execute_tcorw_pagerank(topo, node_metrics, alert_node="orders")
    assert len(rankings) == 4
    top_cause, prob = rankings[0]
    # Orders node should be mathematically identified as top root cause
    assert top_cause == "orders"
    assert prob > 0.35

def test_rca_engine_caraf_classification():
    # Test internal deadlock classification
    deadlock_res = RootCauseAnalysisEngine.classify_residual_factor(
        root_cause_node="orders-svc",
        metrics={"stall_duration_ns": 120_000_000, "event_type": 3},
        host_context={"host_cpu_steal_pct": 2.0, "sibling_stall_count": 0}
    )
    assert deadlock_res["classification"] == "INTERNAL_DEADLOCK"
    assert deadlock_res["recommended_phase2"] == "RESTART_CONTAINER"

    # Test host-level noisy neighbor / residual contention
    contention_res = RootCauseAnalysisEngine.classify_residual_factor(
        root_cause_node="orders-svc",
        metrics={"stall_duration_ns": 90_000_000, "event_type": 4},
        host_context={"host_cpu_steal_pct": 72.0, "sibling_stall_count": 3}
    )
    assert contention_res["classification"] == "HOST_RESIDUAL_CONTENTION"
    assert contention_res["recommended_phase2"] == "EVICT_POD"

# --- 6. End-to-End Remediation Pipeline Escalation Tests ---

def test_remediation_pipeline_escalation():
    pipeline = RemediationPipeline(window_s=1.5, threshold=5, stage2_delay=1.0)
    now = 1000.0
    for i in range(6):
        pipeline.process_connect_event(pid=4812, comm="orders-svc", daddr_str="10.0.0.42", dport=6379, now=now + i * 0.05)

    # First evaluation: Phase 1 NetEdit traffic drain & CPU throttle applied
    g, anomalies = pipeline.evaluate_and_remediate(current_time=now + 0.4)
    assert len(anomalies) == 1
    state = pipeline.remediation_state.get("d4a8c91f021e")
    assert state is not None
    assert state["phase1_applied"] is True
    assert state["phase2_applied"] is False

    # Second evaluation after stage2_delay: Phase 2 triggered
    later = now + 1.8
    for i in range(6):
        pipeline.process_connect_event(pid=4812, comm="orders-svc", daddr_str="10.0.0.42", dport=6379, now=later - 0.5 + i * 0.05)
    g, anomalies = pipeline.evaluate_and_remediate(current_time=later)
    assert state["phase2_applied"] is True

def test_remediation_pipeline_deadlock_restart():
    pipeline = RemediationPipeline(window_s=1.5, threshold=5, stage2_delay=1.0)
    now = 2000.0

    anomaly = {
        "container_id": "d4a8c91f021e",
        "pid": 4812,
        "comm": "orders-svc",
        "target_endpoint": "10.0.1.20:8080",
        "event_type": 3, # FUTEX_DEADLOCK
        "sk_rmem_alloc": 1048576,
        "sk_rcvbuf": 1048576,
        "stall_duration_ns": 150_000_000,
        "retry_count": 1
    }

    # Phase 1
    pipeline.evaluate_and_remediate(current_time=now, forced_anomaly=anomaly)
    state = pipeline.remediation_state.get("d4a8c91f021e")
    assert state["phase1_applied"] is True
    assert state["classification"] == "INTERNAL_DEADLOCK"

    # Phase 2 after delay
    pipeline.evaluate_and_remediate(current_time=now + 1.5, forced_anomaly=anomaly)
    assert state["phase2_applied"] is True
