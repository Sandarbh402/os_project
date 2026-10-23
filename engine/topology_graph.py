"""
CrossTrace Dynamic Topology & Call Graph Engine (arXiv:2508.11342, 2025).
Maintains a real-time Directed Acyclic Graph (DAG) G = (V, E) of distributed microservices
using deterministic in-band Span IDs injected into TCP packet headers.
Provides k-hop localized sub-graph extraction to prevent state space explosion.
"""

import time
from typing import Dict, List, Tuple, Optional, Any, Set
import networkx as nx

class TopologyGraph:
    """
    Maintains the dynamic microservice call graph G = (V, E).
    Tracks services, containers, endpoints, and multi-hop RPC relationships.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        # Service -> set of active endpoints/containers
        self.service_registry: Dict[str, Dict[str, Any]] = {}
        # Span history for temporal auditing
        self.span_records: List[Dict[str, Any]] = []

    def register_service(
        self,
        service_name: str,
        container_id: str,
        host_ip: str,
        port: int,
        pid: Optional[int] = None,
        comm: Optional[str] = None
    ):
        """Registers or updates a microservice node in the topology graph."""
        self.service_registry[service_name] = {
            "container_id": container_id,
            "host_ip": host_ip,
            "port": port,
            "pid": pid,
            "comm": comm or service_name
        }
        self.G.add_node(
            service_name,
            type="service",
            container_id=container_id,
            endpoint=f"{host_ip}:{port}",
            pid=pid,
            comm=comm or service_name
        )

    def record_span(
        self,
        caller: str,
        callee: str,
        span_id: int,
        trace_id: int = 1,
        latency_ms: float = 1.0,
        is_error: bool = False,
        timestamp: Optional[float] = None
    ):
        """
        Records an observed in-band CrossTrace span between two microservices.
        Updates directed edge weights, request counts, and error tallies.
        """
        if timestamp is None:
            timestamp = time.time()

        if not self.G.has_node(caller):
            self.G.add_node(caller, type="service", container_id="unknown", endpoint="unknown")
        if not self.G.has_node(callee):
            self.G.add_node(callee, type="service", container_id="unknown", endpoint="unknown")

        if self.G.has_edge(caller, callee):
            edge_data = self.G[caller][callee]
            edge_data["call_count"] += 1
            if is_error:
                edge_data["error_count"] += 1
            edge_data["last_latency_ms"] = latency_ms
            edge_data["avg_latency_ms"] = round((edge_data["avg_latency_ms"] * 0.8) + (latency_ms * 0.2), 2)
            edge_data["last_timestamp"] = timestamp
            edge_data["span_id"] = span_id
        else:
            self.G.add_edge(
                caller,
                callee,
                call_count=1,
                error_count=1 if is_error else 0,
                last_latency_ms=latency_ms,
                avg_latency_ms=latency_ms,
                last_timestamp=timestamp,
                span_id=span_id,
                trace_id=trace_id
            )

        self.span_records.append({
            "caller": caller,
            "callee": callee,
            "span_id": span_id,
            "trace_id": trace_id,
            "latency_ms": latency_ms,
            "is_error": is_error,
            "timestamp": timestamp
        })

    def get_k_hop_subgraph(self, target_node: str, k: int = 2) -> nx.DiGraph:
        """
        Extracts a localized k-degree neighbor sub-graph surrounding target_node.
        Mitigates state-space explosion: bounds analysis to 10-50 nodes rather than
        traversing an entire 5,000-node cluster DAG.
        """
        if target_node not in self.G:
            sub = nx.DiGraph()
            sub.add_node(target_node, type="service")
            return sub

        # Collect k-hop predecessor (upstream) and successor (downstream) nodes
        nodes_to_keep: Set[str] = {target_node}
        current_frontier = {target_node}

        for _ in range(k):
            next_frontier = set()
            for node in current_frontier:
                if node in self.G:
                    predecessors = set(self.G.predecessors(node))
                    successors = set(self.G.successors(node))
                    next_frontier.update(predecessors | successors)
            next_frontier -= nodes_to_keep
            nodes_to_keep.update(next_frontier)
            current_frontier = next_frontier
            if not current_frontier:
                break

        return self.G.subgraph(nodes_to_keep).copy()

    def clear(self):
        """Clears the graph."""
        self.G.clear()
        self.service_registry.clear()
        self.span_records.clear()
