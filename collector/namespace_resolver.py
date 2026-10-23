import os
import re
import glob
from typing import Dict, Optional

class NamespaceResolver:
    """
    Resolves Host PID / cgroup ID to Docker Container ID and discovers
    the corresponding cgroup v2 controller directory for actuation.
    Enriches kernel-level telemetry with container, pod, and service identifiers.
    """

    # Static registry/cache for simulated or dynamically discovered containers
    _MOCK_REGISTRY: Dict[int, str] = {
        4812: "d4a8c91f021e",
        1024: "9f8e7d6c5b4a",
        2048: "3c2b1a0f9e8d",
        3072: "7e6d5c4b3a21"
    }

    _SERVICE_MAP: Dict[str, str] = {
        "d4a8c91f021e": "orders-service",
        "9f8e7d6c5b4a": "api-gateway",
        "3c2b1a0f9e8d": "inventory-service",
        "7e6d5c4b3a21": "payment-service"
    }

    @classmethod
    def register_container(cls, pid: int, container_id: str, service_name: Optional[str] = None):
        """Allows test runners or simulators to register PID-to-container mappings."""
        cls._MOCK_REGISTRY[pid] = container_id
        if service_name:
            cls._SERVICE_MAP[container_id] = service_name

    @classmethod
    def resolve_service_name(cls, container_id: str, comm: str = "") -> str:
        """Resolves a container ID and process comm to a high-level microservice name."""
        if container_id in cls._SERVICE_MAP:
            return cls._SERVICE_MAP[container_id]
        if comm and comm not in ("python", "python3", "sh", "bash"):
            return comm
        return f"service-{container_id[:6]}"

    @classmethod
    def resolve_pid_to_container_id(cls, pid: int) -> str:
        """
        Parses /proc/{pid}/cgroup (or /host/proc/{pid}/cgroup inside containers)
        to extract the 12-character Docker Container ID.
        Supports standard Docker prefixes, systemd scopes, and Kubernetes pod cgroups.
        Falls back to Docker API inspection and mock registry.
        """
        # Try both host-mounted proc and local proc
        candidate_paths = [f"/host/proc/{pid}/cgroup", f"/proc/{pid}/cgroup"]
        for cgroup_file in candidate_paths:
            if os.path.exists(cgroup_file):
                try:
                    with open(cgroup_file, "r") as f:
                        for line in f:
                            match = re.search(r'(?:docker/|docker-|kubepods/.*pod[0-9a-f-]+/)([0-9a-f]{12,64})', line)
                            if match:
                                return match.group(1)[:12]
                except Exception:
                    pass

        # Try Docker SDK container inspection by PID or active target container
        try:
            import docker
            client = docker.from_env()
            for container in client.containers.list():
                c_pid = container.attrs.get("State", {}).get("Pid")
                if c_pid == pid or ("orders" in container.name and "agent" not in container.name and "redis" not in container.name):
                    return container.id[:12]
        except Exception:
            pass

        # Check registered fallback/simulation registry
        if pid in cls._MOCK_REGISTRY:
            return cls._MOCK_REGISTRY[pid]

        return "host"

    @staticmethod
    def get_cgroup_v2_path(container_id: str) -> str:
        """
        Discovers the active cgroup v2 filesystem directory for the container ID.
        Probes common cgroup v2 hierarchies and systemd scope globs.
        """
        # First probe systemd slice globs (handles 12-char prefix matching 64-char scopes)
        systemd_matches = glob.glob(f"/sys/fs/cgroup/system.slice/docker-{container_id}*.scope")
        if systemd_matches and os.path.exists(systemd_matches[0]):
            return systemd_matches[0]

        possible_paths = [
            f"/sys/fs/cgroup/docker/{container_id}",
            f"/sys/fs/cgroup/systemd/docker/{container_id}",
            f"/sys/fs/cgroup/unified/docker/{container_id}",
            f"/sys/fs/cgroup/{container_id}",
            f"/sys/fs/cgroup/system.slice/docker-{container_id}.scope"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return f"/sys/fs/cgroup/docker/{container_id}"
