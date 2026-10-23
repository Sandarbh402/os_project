import os
import posixpath

class Cgroupv2Actuator:
    """
    Stage 1 Actuator: Writes CPU bandwidth quotas directly to cgroup v2 cpu.max.
    Example: 10% CPU quota = '10000 100000' (10ms quota per 100ms CFS period).
    """

    @staticmethod
    def apply_cpu_quota(cgroup_path: str, quota_pct: int = 10) -> bool:
        """
        Applies a CPU quota percentage to the specified cgroup directory by writing to cpu.max.
        Returns True on success, False if file doesn't exist or write permissions fail.
        """
        cpu_max_file = posixpath.join(cgroup_path, "cpu.max") if "/" in cgroup_path else os.path.join(cgroup_path, "cpu.max")
        quota_us = quota_pct * 1000
        period_us = 100000
        payload = f"{quota_us} {period_us}\n"

        try:
            if os.path.exists(cpu_max_file):
                with open(cpu_max_file, "w") as f:
                    f.write(payload)
                print(f"  [✓] CPU Quota Applied: Capped container CPU to {quota_pct}% via cgroup v2 ({cgroup_path})")
                return True
            else:
                print(f"  [i] CPU Quota Bypassed: {cpu_max_file} not found on host (simulation mode)")
                return False
        except Exception as e:
            print(f"[ACTUATOR ERROR] Failed writing cgroup v2 quota to {cpu_max_file}: {e}")
            return False
