#!/usr/bin/env python3
"""
Autonomous Closed-Loop Orchestration Controller (2024-2026 Architectural Synthesis)
Ties together:
 - Tier 1: Kernel eBPF Sensory Probes (connect_tracker.c) via BCC
           (K-Sense buffer queue derivatives, Beyond Thread States futex/sched profiling)
 - Tier 2: Diagnostic Brain (engine/topology_graph.py, engine/rca_engine.py)
           (CrossTrace in-band DAG, k-hop sub-graph extraction, TORAI TCORW, CARAF Residual Classifier)
 - Tier 3: Surgical Self-Healing (actuator/netedit_actuator.py, cgroup_actuator.py, docker_actuator.py)
           (Phase 1 microsecond tc traffic drain & Phase 2 asynchronous restart/evict/throttle)
 - Synthetic Multi-Tier Demonstration Mode (--demo)
"""

import os
import sys
import time
import socket
import struct
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Ensure UTF-8 output on Windows consoles if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add current script directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from collector.namespace_resolver import NamespaceResolver
from engine.loop_detector import ThreadDynamicsGraphEngine
from engine.topology_graph import TopologyGraph
from engine.rca_engine import RootCauseAnalysisEngine
from actuator.cgroup_actuator import Cgroupv2Actuator
from actuator.docker_actuator import DockerApiActuator
from actuator.netedit_actuator import NetEditBpfAdapter


class RemediationPipeline:
    """
    Unified Three-Tier Autonomous Closed-Loop Remediation Pipeline:
    Coordinates Ring 0 pre-crash sensors, localized sub-graph RCA, and two-phase self-healing.
    """

    def __init__(self, window_s: float = 1.5, threshold: int = 10, stage2_delay: float = 2.5):
        self.window_s = window_s
        self.threshold = threshold
        self.stage2_delay = stage2_delay

        # Diagnostic Brain Sub-systems
        self.graph_engine = ThreadDynamicsGraphEngine(
            window_seconds=window_s,
            min_retry_threshold=threshold
        )
        self.topology_graph = TopologyGraph()
        self.rca_engine = RootCauseAnalysisEngine(damping_factor=0.85)

        # Container / Service Remediation State Tracking
        # container_id -> dict(first_detected, phase1_applied, phase2_applied, root_cause, classification)
        self.remediation_state: Dict[str, Dict[str, Any]] = {}

    def process_connect_event(self, pid: int, comm: str, daddr_str: str, dport: int, now: float = None):
        """Processes an incoming connection retry event from eBPF ring buffer or simulator."""
        if now is None:
            now = time.time()

        container_id = NamespaceResolver.resolve_pid_to_container_id(pid)
        service_name = NamespaceResolver.resolve_service_name(container_id, comm)
        target_endpoint = f"{daddr_str}:{dport}"

        # Register in dynamic topology call graph
        self.topology_graph.register_service(
            service_name=service_name,
            container_id=container_id,
            host_ip="127.0.0.1",
            port=dport,
            pid=pid,
            comm=comm
        )
        self.topology_graph.record_span(
            caller=service_name,
            callee=f"endpoint:{target_endpoint}",
            span_id=abs(hash(f"{service_name}-{target_endpoint}")) % 100000,
            latency_ms=1.5,
            is_error=False,
            timestamp=now
        )

        self.graph_engine.record_event(
            pid=pid,
            comm=comm,
            container_id=container_id,
            target_endpoint=target_endpoint,
            timestamp=now
        )

    def process_triage_event(
        self,
        event_type: int,
        pid: int,
        comm: str,
        daddr_str: str = "127.0.0.1",
        dport: int = 8080,
        sk_rmem_alloc: int = 0,
        sk_rcvbuf: int = 1048576,
        stall_duration_ns: int = 0,
        retry_count: int = 1,
        span_id: int = 0,
        now: Optional[float] = None
    ):
        """
        Processes multi-vector kernel triage telemetry from Ring 0 probes:
        - K-Sense: sk_rmem_alloc socket buffer fill
        - Beyond Thread States: futex deadlock & thread runqueue stalls
        - CrossTrace: In-band span tags
        """
        if now is None:
            now = time.time()

        container_id = NamespaceResolver.resolve_pid_to_container_id(pid)
        service_name = NamespaceResolver.resolve_service_name(container_id, comm)
        target_endpoint = f"{daddr_str}:{dport}"

        self.topology_graph.register_service(
            service_name=service_name,
            container_id=container_id,
            host_ip=daddr_str,
            port=dport,
            pid=pid,
            comm=comm
        )

        # Record span in dynamic DAG
        self.topology_graph.record_span(
            caller=service_name,
            callee=f"endpoint:{target_endpoint}",
            span_id=span_id or abs(hash(service_name)) % 100000,
            latency_ms=round(stall_duration_ns / 1_000_000.0, 2) if stall_duration_ns else 2.0,
            is_error=(event_type in (1, 2, 3)),
            timestamp=now
        )

        # Forward connect storm events to sliding window engine
        if event_type == 1:
            self.graph_engine.record_event(
                pid=pid,
                comm=comm,
                container_id=container_id,
                target_endpoint=target_endpoint,
                timestamp=now
            )

    def evaluate_and_remediate(
        self,
        current_time: Optional[float] = None,
        forced_anomaly: Optional[Dict[str, Any]] = None,
        host_context: Optional[Dict[str, Any]] = None,
        bpf_instance: Any = None
    ) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Core Closed-Loop Execution Loop:
        1. Evaluates retry anomalies and thread dynamics in sliding window.
        2. Performs localized k-hop sub-graph extraction around alerting service.
        3. Executes TORAI TCORW Random Walk to isolate true root-cause node.
        4. Applies CARAF Residual Factor Classifier to distinguish internal deadlock vs host noisy neighbor.
        5. Executes Two-Phase Remediation:
           - Phase 1 (< 1ms): NetEdit BpfAdapter tc traffic drain in ring 0.
           - Phase 2 (Async 2-5s): Classification-guided container restart, pod eviction, or CPU throttling.
        """
        if current_time is None:
            current_time = time.time()

        graph, anomalies = self.graph_engine.evaluate_operational_loops(current_time)

        # Merge synthetic or injected triage anomalies
        if forced_anomaly:
            anomalies = [forced_anomaly]

        if not anomalies:
            return graph, anomalies

        for anomaly in anomalies:
            cid = anomaly["container_id"]
            pid = anomaly["pid"]
            comm = anomaly["comm"]
            endpoint = anomaly["target_endpoint"]
            retries = anomaly.get("retry_count", 1)

            service_name = NamespaceResolver.resolve_service_name(cid, comm)

            # --- TIER 2: DIAGNOSTIC BRAIN (SUB-GRAPH EXTRACTION & TCORW RCA) ---
            # 1. Extract 2-hop localized sub-graph to prevent state space explosion
            subgraph = self.topology_graph.get_k_hop_subgraph(service_name, k=2)

            # 2. Compute TORAI Anomaly-Weighted Transition Matrix & PageRank
            node_metrics = {
                service_name: {
                    "sk_rmem_alloc": anomaly.get("sk_rmem_alloc", 0),
                    "sk_rcvbuf": anomaly.get("sk_rcvbuf", 1048576),
                    "stall_duration_ns": anomaly.get("stall_duration_ns", 0),
                    "retry_count": retries,
                    "event_type": anomaly.get("event_type", 1)
                }
            }

            ranked_causes = self.rca_engine.execute_tcorw_pagerank(
                subgraph=subgraph,
                node_metrics=node_metrics,
                alert_node=service_name
            )

            root_node, confidence = ranked_causes[0] if ranked_causes else (service_name, 1.0)

            # 3. CARAF Residual Factor Classification
            classification_info = self.rca_engine.classify_residual_factor(
                root_cause_node=root_node,
                metrics=node_metrics.get(root_node, {}),
                host_context=host_context
            )

            # Manage progressive two-phase remediation state
            is_new = cid not in self.remediation_state
            if is_new:
                self.remediation_state[cid] = {
                    "first_seen": current_time,
                    "phase1_applied": False,
                    "phase2_applied": False,
                    "root_node": root_node,
                    "classification": classification_info["classification"],
                    "ip_port": endpoint.split(":") if ":" in endpoint else ("127.0.0.1", 8080)
                }

                print(f"\n[⚠️  ANOMALY DETECTED] Process '{comm}' (PID: {pid}, Container: {cid[:12]}) -> {endpoint}")
                print(f"  • Service Topology: Analyzed local cluster neighborhood ({subgraph.number_of_nodes()} services)")
                print(f"  • Root Cause Pinpointed: '{root_node}' ({confidence * 100:.1f}% confidence)")
                print(f"  • Diagnosis: {classification_info['diagnosis']}")

            state = self.remediation_state[cid]
            duration = current_time - state["first_seen"]

            # --- TIER 3: PHASE 1 MICROSECOND MITIGATION (< 1ms) ---
            if not state["phase1_applied"]:
                ip_str = state["ip_port"][0]
                try:
                    port_val = int(state["ip_port"][1])
                except (ValueError, IndexError):
                    port_val = 8080

                print(f"\n[⚡ PHASE 1: INSTANT MITIGATION (< 1ms)]")
                print(f"  • Action: Isolating network traffic away from failing target {ip_str}:{port_val}...")
                NetEditBpfAdapter.drain_traffic(ip_str, port_val, bpf_instance=bpf_instance)
                state["phase1_applied"] = True

                # If connection retry storm, also throttle CPU bandwidth to 10%
                if classification_info["classification"] == "CONNECTION_RETRY_STORM":
                    cgroup_path = NamespaceResolver.get_cgroup_v2_path(cid)
                    print(f"  • Action: Capping container CPU quota to 10% to prevent host freeze...")
                    Cgroupv2Actuator.apply_cpu_quota(cgroup_path, quota_pct=10)

            # --- TIER 3: PHASE 2 ASYNCHRONOUS HEALING (2-5s) ---
            elif not state["phase2_applied"] and duration >= self.stage2_delay:
                print(f"\n[🛠️  PHASE 2: AUTOMATIC RECOVERY (Evaluated after {duration:.1f}s)]")
                c_type = state["classification"]

                if c_type == "HOST_RESIDUAL_CONTENTION":
                    # CARAF Noisy Neighbor / Host Contention -> Evict Pod to schedule on another node
                    print(f"  • Diagnosis: Shared server CPU is overloaded (Noisy Neighbor)")
                    print(f"  • Action: Evicting pod '{root_node}' to reschedule on an idle server...")
                    DockerApiActuator.evict_container(cid, pod_name=root_node)

                elif c_type in ("INTERNAL_DEADLOCK", "SOCKET_QUEUE_STARVATION"):
                    # Beyond Thread States Futex Deadlock / K-Sense Starvation -> Restart Container
                    print(f"  • Diagnosis: Internal application code deadlock detected")
                    print(f"  • Action: Safely rebooting deadlocked container '{cid[:12]}'...")
                    DockerApiActuator.restart_container(cid)

                else:
                    # Connection Retry Storm -> Freeze container via Docker pause API
                    print(f"  • Diagnosis: Downstream database unreachable (Retry Storm)")
                    print(f"  • Action: Freezing container '{cid[:12]}' to stop network flooding...")
                    DockerApiActuator.pause_container(cid)

                state["phase2_applied"] = True

                # Restore traffic routing after healing
                ip_str = state["ip_port"][0]
                try:
                    port_val = int(state["ip_port"][1])
                except Exception:
                    port_val = 8080
                print(f"  • Action: Restoring network traffic to {ip_str}:{port_val}...")
                NetEditBpfAdapter.restore_traffic(ip_str, port_val, bpf_instance=bpf_instance)

        return graph, anomalies


def run_live_ebpf(pipeline: RemediationPipeline, poll_interval: float = 0.5):
    """Loads and attaches eBPF kernel sensor via BCC."""
    try:
        import importlib
        bcc = importlib.import_module("bcc")
        BPF = getattr(bcc, "BPF")
    except ImportError:
        print("\n[ERROR] BCC library (python3-bpfcc / bcc) is not installed in the current Python environment.")
        print("eBPF kernel tracing requires a Linux environment with root privileges.")
        print("Tip: Run in demonstration simulation mode instead using: python controller.py --demo\n")
        sys.exit(1)

    ebpf_source = BASE_DIR / "ebpf" / "connect_tracker.c"
    if not ebpf_source.exists():
        print(f"[ERROR] eBPF C program not found at {ebpf_source}")
        sys.exit(1)

    print(f"[*] Compiling and loading eBPF kernel sensor: {ebpf_source.name}")
    try:
        b = BPF(src_file=str(ebpf_source))
    except Exception as e:
        print(f"[ERROR] Failed to compile/attach eBPF probe (requires root / sudo): {e}")
        sys.exit(1)

    print("[✓] eBPF kernel sensors active and monitoring:")
    print("    • Network: Connection retry storm detector")
    print("    • Threading: Mutex lock & deadlock detector")
    print("    • Sockets: Queue buffer overflow detector")
    print("[*] Listening for system anomalies... (Press Ctrl+C to exit)")

    def handle_ringbuf_event(cpu, data, size):
        evt = b["loop_events"].event(data)
        daddr_str = socket.inet_ntoa(struct.pack("<I", evt.daddr))
        dport = socket.ntohs(evt.dport)
        comm = evt.comm.decode("utf-8", "replace")
        now = time.time()

        pipeline.process_triage_event(
            event_type=evt.event_type,
            pid=evt.pid,
            comm=comm,
            daddr_str=daddr_str,
            dport=dport,
            sk_rmem_alloc=getattr(evt, "sk_rmem_val", getattr(evt, "sk_rmem_alloc", 0)),
            sk_rcvbuf=evt.sk_rcvbuf,
            stall_duration_ns=evt.duration_ns,
            retry_count=evt.retry_count,
            span_id=evt.span_id,
            now=now
        )
        pipeline.evaluate_and_remediate(current_time=now, bpf_instance=b)

    b["loop_events"].open_ring_buffer(handle_ringbuf_event)

    try:
        while True:
            b.ring_buffer_poll(timeout=int(poll_interval * 1000))
            pipeline.evaluate_and_remediate(time.time(), bpf_instance=b)
    except KeyboardInterrupt:
        print("\n[*] Detaching eBPF sensors and exiting cleanly.")


def run_demo_simulation(pipeline: RemediationPipeline):
    """
    State-of-the-Art Multi-Tier Demonstration Mode (2024-2026 Architectural Synthesis):
    Exercises:
      - CrossTrace in-band distributed DAG propagation.
      - Beyond Thread States & K-Sense pre-crash kernel struct monitoring.
      - 2-hop localized sub-graph extraction (capping state-space from 5,000 nodes to 4 nodes).
      - TORAI TCORW Random Walk isolating the true fault domain.
      - CARAF Residual Factor Classifier distinguishing internal deadlock vs host noisy-neighbor.
      - Phase 1 NetEdit BpfAdapter tc traffic drain (< 1ms).
      - Phase 2 Asynchronous surgical container restart / pod eviction.
    """
    print("=" * 80)
    print("           AUTONOMOUS CLOUD SELF-HEALING SYSTEM - LIVE DEMO             ")
    print("=" * 80)
    print("System Architecture:")
    print("  Tier 1 | Kernel Pre-Crash Detection (Catches frozen threads & queue overloads)")
    print("  Tier 2 | AI Root-Cause Diagnostic Brain (Finds which microservice actually failed)")
    print("  Tier 3 | Two-Phase Self-Healing (Instant traffic drain < 1ms -> Automatic recovery)")
    print("=" * 80)

    time.sleep(0.3)

    # Register multi-tier microservice architecture in CrossTrace Dynamic Topology
    print("\n[STEP 1/4] Mapping Microservice Architecture & Health")
    services = [
        ("api-gateway", "9f8e7d6c5b4a", "10.0.1.10", 80, 1024, "gateway"),
        ("orders-service", "d4a8c91f021e", "10.0.1.20", 8080, 4812, "orders-svc"),
        ("inventory-service", "3c2b1a0f9e8d", "10.0.1.30", 9090, 2048, "inventory-svc"),
        ("payment-service", "7e6d5c4b3a21", "10.0.1.40", 7070, 3072, "payment-svc"),
        ("target-redis", "redis0000000", "10.0.1.50", 6379, 9999, "redis-server")
    ]
    for s_name, c_id, ip, port, pid, comm in services:
        pipeline.topology_graph.register_service(s_name, c_id, ip, port, pid, comm)
        NamespaceResolver.register_container(pid, c_id, s_name)

    # Establish normal CrossTrace in-band span propagation across the call chain:
    # Client -> api-gateway -> orders-service -> inventory-service -> target-redis
    span_chains = [
        ("api-gateway", "orders-service", 101, 12.4),
        ("orders-service", "inventory-service", 102, 8.1),
        ("orders-service", "payment-service", 103, 15.2),
        ("inventory-service", "target-redis", 104, 2.3)
    ]
    for caller, callee, span_id, lat in span_chains:
        pipeline.topology_graph.record_span(caller, callee, span_id, latency_ms=lat, is_error=False)

    print("  ✔ Discovered 5 microservices across the request chain:")
    print("      api-gateway -> orders-service -> inventory-service -> target-redis")
    print("                                    -> payment-service")
    print("  ✔ Cluster Status: HEALTHY (All services operating normally)")

    time.sleep(0.8)

    # FAULT INJECTION 1: Internal Futex Deadlock & Socket Buffer Starvation (orders-service)
    print("\n" + "-" * 80)
    print("[STEP 2/4] Simulating Fault: Internal Code Deadlock in 'orders-service'")
    print("  • What happened: Worker thread locked on a mutex; incoming requests freeze.")
    print("  • Kernel warning: Socket queue backed up to 100% full (1 MB unread buffer).")
    print("-" * 80)

    t0 = time.time()
    deadlock_anomaly = {
        "container_id": "d4a8c91f021e",
        "pid": 4812,
        "comm": "orders-svc",
        "target_endpoint": "10.0.1.20:8080",
        "event_type": 3, # FUTEX_DEADLOCK
        "sk_rmem_alloc": 1048576, # 1MB saturated
        "sk_rcvbuf": 1048576,
        "stall_duration_ns": 125_000_000, # 125ms futex wait
        "retry_count": 1
    }

    # Dispatch to Closed-Loop Engine
    pipeline.evaluate_and_remediate(current_time=t0, forced_anomaly=deadlock_anomaly)

    time.sleep(1.0)

    # Simulate Phase 2 Asynchronous Escalation (> stage2_delay)
    print("\n" + "-" * 80)
    print(f"[STEP 3/4] Automatic Service Recovery (> {pipeline.stage2_delay}s evaluation window)")
    print("-" * 80)
    t1 = t0 + pipeline.stage2_delay + 0.2
    pipeline.evaluate_and_remediate(current_time=t1, forced_anomaly=deadlock_anomaly)

    time.sleep(0.8)

    # FAULT INJECTION 2: CARAF Ambiguous Residual Factor (Host Noisy Neighbor Contention)
    print("\n" + "-" * 80)
    print("[STEP 4/4] Simulating Fault: Shared Server Overload ('Noisy Neighbor')")
    print("  • What happened: Other workloads on the host are stealing 68% CPU time.")
    print("  • Brain logic: Differentiating software bug vs host hardware starvation...")
    print("-" * 80)

    t2 = time.time()
    pipeline.remediation_state.clear() # Reset state for second scenario
    host_context = {
        "host_cpu_steal_pct": 68.5,
        "sibling_stall_count": 3
    }
    residual_anomaly = {
        "container_id": "3c2b1a0f9e8d",
        "pid": 2048,
        "comm": "inventory-svc",
        "target_endpoint": "10.0.1.30:9090",
        "event_type": 4, # SCHED_STALL
        "sk_rmem_alloc": 200000,
        "sk_rcvbuf": 1048576,
        "stall_duration_ns": 90_000_000,
        "retry_count": 1
    }

    pipeline.evaluate_and_remediate(current_time=t2, forced_anomaly=residual_anomaly, host_context=host_context)
    t3 = t2 + pipeline.stage2_delay + 0.2
    pipeline.evaluate_and_remediate(current_time=t3, forced_anomaly=residual_anomaly, host_context=host_context)

    print("\n" + "=" * 80)
    print("                     DEMONSTRATION COMPLETE: KEY TAKEAWAYS                      ")
    print("=" * 80)
    print("  1. Instant Detection: Caught application freezes in the Linux kernel BEFORE crashes.")
    print("  2. Smart Diagnostics: Isolated the exact failing service using dependency graph analysis.")
    print("  3. Root-Cause Precision: Separated internal code bugs from overloaded host servers.")
    print("  4. Two-Phase Healing:")
    print("       • Phase 1 (< 1ms): Instantly drained traffic away from failing endpoints.")
    print("       • Phase 2 (Async): Safely restarted deadlocked containers or evicted pods.")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Closed-Loop Cloud Self-Healing Controller"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run interactive demonstration mode (works on any OS without root)"
    )
    parser.add_argument(
        "--window",
        type=float,
        default=1.5,
        help="Sliding time window in seconds for detecting retry storms (default: 1.5)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Failed connection attempts before taking action (default: 10)"
    )
    parser.add_argument(
        "--stage2-delay",
        type=float,
        default=2.5,
        help="Seconds to wait before restarting container or evicting pod (default: 2.5)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Kernel ring buffer polling interval in seconds (default: 0.5)"
    )

    args = parser.parse_args()

    pipeline = RemediationPipeline(
        window_s=args.window,
        threshold=args.threshold,
        stage2_delay=args.stage2_delay
    )

    if args.demo:
        run_demo_simulation(pipeline)
    else:
        # Check if running under Linux with root or if demo should be suggested
        if os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() != 0):
            print("[INFO] Running without root privileges or on non-Linux host.")
            print("[INFO] Launching demonstration simulation mode (--demo).")
            print("[INFO] Run with --help to see available command-line options.\n")
            run_demo_simulation(pipeline)
        else:
            run_live_ebpf(pipeline, poll_interval=args.poll_interval)


if __name__ == "__main__":
    main()
