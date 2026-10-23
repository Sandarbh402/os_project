# Running the Autonomous Closed-Loop Remediation Pipeline with Docker

This guide explains how to package, deploy, and test the three-tier autonomous closed-loop eBPF remediation system using Docker and Docker Compose.

---

## 1. Environment & Setup

Docker and the eBPF kernel tracing infrastructure run through the Linux kernel (including WSL2 Linux kernel `6.6+`), with direct CLI wrappers provided for Windows PowerShell.

### Using Docker CLI:
- **From Windows PowerShell (in project directory)**:
  ```powershell
  .\docker.cmd ps
  .\docker.cmd compose up -d
  .\docker.cmd compose down
  ```
- **From WSL Ubuntu / Linux**:
  ```bash
  docker ps
  docker compose up -d
  ```

---

## 2. Container Architecture & Privilege Requirements

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                Linux Host                                   │
│  Kernel Ring 0: sys_enter_connect, sys_futex, sock:sock_exceed_buf_limit     │
│  Host cgroups: /sys/fs/cgroup/system.slice/docker-*.scope                   │
│  Docker Engine Daemon: /var/run/docker.sock                                 │
└──────────────────────┬───────────────────────────────────────▲──────────────┘
                       │                                       │
            ┌──────────▼──────────┐                 ┌──────────┴──────────┐
            │     ebpf-agent      │                 │   orders-service    │
            │ (Privileged Daemon) │                 │ (Observed Container)│
            │                     │                 │                     │
            │ • privileged: true  │                 │ • connects to Redis │
            │ • pid: host         │                 │ • triggers retry    │
            │ • mounts /sys       │                 │   storm on fault    │
            │ • mounts /proc      │                 └─────────────────────┘
            │ • mounts docker.sock│
            └─────────────────────┘
```

### Essential Container Configuration:
1. `privileged: true` — Grants kernel capabilities (`CAP_BPF`, `CAP_SYS_ADMIN`, `CAP_PERFMON`) to attach tracepoints, load BPF bytecode, and update traffic drain maps.
2. `pid: host` — Aligns process IDs between kernel eBPF probes and `/proc/{pid}/cgroup`.
3. `/sys:/sys:rw` — Mounts sysfs for kernel debugfs, in-kernel headers (`kheaders.tar.xz`), and cgroups v2 (`cpu.max`).
4. `/proc:/host/proc:ro` — Enables user-space container namespace resolution.
5. `/var/run/docker.sock:/var/run/docker.sock:rw` — Allows Phase 2 actuator to invoke Docker REST API (`restart`, `pause`, `evict`).

---

## 3. Coordinated Services

| Container | Role | Description |
| :--- | :--- | :--- |
| `target-redis` | Target Dependency | Redis backend on port 6379. |
| `orders-service` | Microservice | Client connecting to Redis. When Redis goes down, triggers an aggressive retry storm (20 attempts/s). |
| `ebpf-agent` | Remediation Pipeline | Host-level eBPF sensor (K-Sense, Beyond Thread States, NetEdit), NetworkX graph analyzer, TORAI TCORW RCA, and progressive actuator. |

---

## 4. End-to-End Test Workflow

### Step 1: Start the Entire System
```powershell
.\docker.cmd compose up -d
```

### Step 2: Stream eBPF Agent Logs
```powershell
.\docker.cmd logs -f ebpf-agent
```
*Output in steady-state (healthy traffic, no alerts):*
```
[*] Compiling and attaching multi-vector eBPF sensor: /app/ebpf/connect_tracker.c
[*] Successfully attached to tracepoints:
    - syscalls:sys_enter_connect (Connection retry storm monitor)
    - syscalls:sys_enter_futex / sys_exit_futex (Beyond Thread States deadlock detector)
    - sock:sock_exceed_buf_limit (K-Sense socket buffer starvation)
[*] Listening for closed-loop triage events... (Press Ctrl+C to exit)
```

### Step 3: Verify Steady-State Health
```powershell
.\docker.cmd logs --tail 5 orders-service
```
*Output:*
```
[HEALTHY] Successfully connected to 127.0.0.1:6379
[HEALTHY] Successfully connected to 127.0.0.1:6379
```

### Step 4: Inject Failure (Stop Target Redis)
```powershell
.\docker.cmd stop target-redis
```

### Step 5: Observe Closed-Loop Autonomous Remediation
Within milliseconds:
1. `orders-service` triggers a reconnect storm (20 attempts/sec).
2. Kernel eBPF probe intercepts bursts crossing $\ge 10$ retries in $1.5\,\text{s}$.
3. Diagnostic Brain extracts localized $k$-hop sub-graph and executes TORAI TCORW Random Walk to isolate root cause.
4. CARAF Residual Factor Classifier classifies the failure.
5. **Phase 1 (< 1ms)**: NetEdit BpfAdapter tc traffic drain isolates the degraded endpoint in ring 0 to protect client SLAs.
6. **Phase 2 (2-5s)**: Targeted container restart or freeze resolves the fault.

### Step 6: Recovery
```powershell
.\docker.cmd unpause orders-service
.\docker.cmd start target-redis
```

---

## 5. Running the Multi-Tier Demonstration in Docker

To run the complete 2024–2026 literature review synthesis demonstration (K-Sense, Beyond Thread States, CrossTrace dynamic DAG, localized $k$-hop sub-graph slicing, TORAI TCORW PageRank random walk, CARAF residual classification, and NetEdit two-phase self-healing) inside an isolated Docker container:

```powershell
# From Windows PowerShell:
.\docker.cmd compose run --rm demo-agent

# From WSL Ubuntu / Linux:
docker compose run --rm demo-agent
```

---

## 6. System Teardown & Cleanup

To stop and remove all background containers, networks, and mounted resources:

```powershell
.\docker.cmd compose down
```
