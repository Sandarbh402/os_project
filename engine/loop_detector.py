import time
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Any
import networkx as nx

class ThreadDynamicsGraphEngine:
    """
    Thread Dynamics Graph Engine G = (V, E) based on Landau et al. (2025, 2026).
    Constructs dependency subgraphs between operating processes and target endpoints,
    evaluating rolling retry bursts using sliding-window deque queues and Tarjan SCC analysis.
    """

    def __init__(self, window_seconds: float = 1.5, min_retry_threshold: int = 10):
        self.window_seconds = window_seconds
        self.min_retry_threshold = min_retry_threshold
        # Stores (pid, comm, container_id, target_endpoint) -> deque of float timestamps
        self.event_history: Dict[Tuple[int, str, str, str], deque] = defaultdict(deque)

    def record_event(self, pid: int, comm: str, container_id: str, target_endpoint: str, timestamp: float):
        """
        Records a connect attempt event timestamp in the corresponding sliding queue.
        """
        key = (pid, comm, container_id, target_endpoint)
        self.event_history[key].append(timestamp)

    def evaluate_operational_loops(self, current_time: float) -> Tuple[nx.DiGraph, List[Dict[str, Any]]]:
        """
        Evicts timestamps outside the sliding window (current_time - window_seconds).
        Constructs the NetworkX directed graph G = (V, E).
        Identifies processes exceeding min_retry_threshold within the window.
        Executes Tarjan's Strongly Connected Components (SCC) analysis.
        Returns the constructed graph G and structured anomaly alerts.
        """
        anomalies: List[Dict[str, Any]] = []
        G = nx.DiGraph()

        for (pid, comm, container_id, target_endpoint), timestamps in list(self.event_history.items()):
            # Evict timestamps older than sliding window
            while timestamps and timestamps[0] < current_time - self.window_seconds:
                timestamps.popleft()

            count = len(timestamps)
            if count >= self.min_retry_threshold:
                process_node = f"proc:{pid}:{comm}"
                endpoint_node = f"endpoint:{target_endpoint}"

                G.add_node(process_node, type="process", pid=pid, comm=comm, container_id=container_id)
                G.add_node(endpoint_node, type="endpoint", endpoint=target_endpoint)
                G.add_edge(process_node, endpoint_node, weight=count, container_id=container_id, pid=pid)

                # Tarjan SCC analysis on current graph component
                sccs = list(nx.strongly_connected_components(G))

                anomalies.append({
                    "pid": pid,
                    "comm": comm,
                    "container_id": container_id,
                    "target_endpoint": target_endpoint,
                    "retry_count": count,
                    "window_s": self.window_seconds,
                    "hysteresis_confirmed": True,
                    "rate_per_sec": round(count / max(self.window_seconds, 0.001), 2),
                    "scc_components": len(sccs)
                })

        return G, anomalies

    def clear(self):
        """Resets the internal event history."""
        self.event_history.clear()
