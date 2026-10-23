"""
Diagnostic Brain RCA Engine:
Combines TORAI TCORW Graph Random Walk (ACM FSE 2026, Pham et al.)
with CARAF Residual Factor Classification (IEEE TETC 2026, Tang et al.).
Operates on localized k-hop subgraphs to achieve sub-millisecond root cause convergence.
"""

import math
from typing import Dict, List, Tuple, Optional, Any
import networkx as nx

class RootCauseAnalysisEngine:
    """
    Executes Temporal Cause Oriented Random Walk (TCORW) on sub-graphs
    and classifies ambiguous residual factors to guide surgical two-phase self-healing.
    """

    def __init__(self, damping_factor: float = 0.85, max_iterations: int = 50, tolerance: float = 1e-5):
        # damping_factor (0.85): probability of following graph anomaly edges
        # teleport_ratio (0.15): probability of jumping via personalized teleportation vector
        self.damping_factor = damping_factor
        self.teleport_ratio = 1.0 - damping_factor
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    @staticmethod
    def compute_anomaly_score(metrics: Dict[str, Any]) -> float:
        """
        Calculates mathematical anomaly score S_i based on Ring 0 kernel structs:
        - sk_rmem_alloc vs sk_rcvbuf (K-Sense socket starvation)
        - futex stall duration (Beyond Thread States deadlock)
        - connect retry storm rate
        """
        base_score = 1.0

        # 1. K-Sense Socket Buffer Starvation Factor
        sk_rmem = metrics.get("sk_rmem_alloc", 0)
        sk_rcv = max(metrics.get("sk_rcvbuf", 1), 1)
        buffer_ratio = sk_rmem / sk_rcv
        if buffer_ratio > 0.5:
            base_score += 25.0 * buffer_ratio

        # 2. Beyond Thread States Futex / Sched Stall Factor
        stall_ns = metrics.get("stall_duration_ns", 0)
        stall_ms = stall_ns / 1_000_000.0
        if stall_ms > 10.0:
            base_score += 15.0 * math.log10(stall_ms + 1.0)

        # 3. Connect Retry Spikes
        retries = metrics.get("retry_count", 0)
        if retries >= 5:
            base_score += 3.0 * min(retries, 50)

        return round(base_score, 3)

    def execute_tcorw_pagerank(
        self,
        subgraph: nx.DiGraph,
        node_metrics: Dict[str, Dict[str, Any]],
        alert_node: str
    ) -> List[Tuple[str, float]]:
        """
        TORAI-inspired Temporal Cause Oriented Random Walk (TCORW).
        Constructs the anomaly-weighted transition matrix P with personalized teleportation
        and computes stationary PageRank probabilities using fast power iteration.
        Returns sorted list of (node_name, probability_score).
        """
        nodes = list(subgraph.nodes())
        n = len(nodes)
        if n == 0:
            return []
        if n == 1:
            return [(nodes[0], 1.0)]

        node_to_idx = {node: i for i, node in enumerate(nodes)}

        # 1. Compute anomaly severity vector S
        scores = []
        for node in nodes:
            metrics = node_metrics.get(node, {})
            score = self.compute_anomaly_score(metrics)
            scores.append(score)

        total_score = sum(scores) or float(n)
        # Personalized teleportation vector biased toward anomalous nodes
        v_teleport = [s / total_score for s in scores]

        # 2. Build transition matrix P (row-stochastic)
        P = [[0.0 for _ in range(n)] for _ in range(n)]
        d = self.damping_factor
        teleport = self.teleport_ratio

        for i, u in enumerate(nodes):
            # In microservice causal analysis, errors propagate across dependencies.
            # We consider bidirectional connectivity (predecessors & successors)
            neighbors = set(subgraph.successors(u)) | set(subgraph.predecessors(u))
            if not neighbors:
                # Isolated node: teleport directly
                for j in range(n):
                    P[i][j] = v_teleport[j]
                continue

            sum_neighbor_scores = sum(scores[node_to_idx[nbr]] for nbr in neighbors) or 1.0

            for j, v in enumerate(nodes):
                if v in neighbors:
                    edge_prob = d * (scores[j] / sum_neighbor_scores)
                else:
                    edge_prob = 0.0
                teleport_prob = teleport * v_teleport[j]
                P[i][j] = edge_prob + teleport_prob

        # 3. Power iteration for stationary distribution
        p = list(v_teleport)
        for _ in range(self.max_iterations):
            p_next = [0.0] * n
            for j in range(n):
                for i in range(n):
                    p_next[j] += p[i] * P[i][j]

            # Check convergence
            diff = sum(abs(p_next[i] - p[i]) for i in range(n))
            p = p_next
            if diff < self.tolerance:
                break

        # Normalize probabilities
        total = sum(p) or 1.0
        results = [(nodes[i], round(p[i] / total, 4)) for i in range(n)]
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    @staticmethod
    def classify_residual_factor(
        root_cause_node: str,
        metrics: Dict[str, Any],
        host_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        CARAF Ambiguous Residual Factor Classifier:
        Disambiguates internal application code deadlocks from noisy neighbor
        hardware/CPU contention and downstream dependency connection storms.
        """
        host_context = host_context or {}
        host_cpu_pressure = host_context.get("host_cpu_steal_pct", 0.0) > 40.0
        sibling_stall_count = host_context.get("sibling_stall_count", 0)

        stall_ns = metrics.get("stall_duration_ns", 0)
        sk_rmem = metrics.get("sk_rmem_alloc", 0)
        retries = metrics.get("retry_count", 0)
        event_type = metrics.get("event_type", 0)

        # 1. Host-level Residual Contention (CARAF Ambiguous Residual Factor)
        if host_cpu_pressure or sibling_stall_count >= 2:
            return {
                "classification": "HOST_RESIDUAL_CONTENTION",
                "diagnosis": "Noisy Neighbor: Shared physical host CPU thrashing (Node Overload)",
                "recommended_phase1": "DRAIN_TRAFFIC",
                "recommended_phase2": "EVICT_POD",
                "confidence": 0.92
            }

        # 2. Internal Thread Deadlock (Beyond Thread States)
        if event_type == 3 or stall_ns > 80_000_000: # > 80ms futex block
            return {
                "classification": "INTERNAL_DEADLOCK",
                "diagnosis": "Internal Deadlock: Application worker thread blocked on mutex lock",
                "recommended_phase1": "DRAIN_TRAFFIC",
                "recommended_phase2": "RESTART_CONTAINER",
                "confidence": 0.95
            }

        # 3. Socket Starvation (K-Sense)
        if event_type == 2 or sk_rmem > 500_000:
            return {
                "classification": "SOCKET_QUEUE_STARVATION",
                "diagnosis": "Queue Starvation: Inbound socket receive queue backed up (Slow Consumer)",
                "recommended_phase1": "DRAIN_TRAFFIC",
                "recommended_phase2": "RESTART_CONTAINER",
                "confidence": 0.91
            }

        # 4. Connection Retry Storm
        return {
            "classification": "CONNECTION_RETRY_STORM",
            "diagnosis": "Connection Retry Storm: Downstream dependency unreachable / offline",
            "recommended_phase1": "DRAIN_TRAFFIC",
            "recommended_phase2": "THROTTLE_CPU",
            "confidence": 0.88
        }
