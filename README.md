# Autonomous Closed-Loop Orchestration Pipeline

A real-time, three-tier closed-loop orchestration and autonomous self-healing system built with **C (eBPF)** and **Python 3**, implementing systems-engineering research (2024–2026):
- **TraceWeaver** (Ashok et al., ACM SIGCOMM 2024)
- **CrossTrace** (arXiv:2508.11342, 2025)
- **Beyond Thread States** (Landau et al., IEEE IPDPS 2026)
- **K-Sense** (Muslim et al., IEEE ICFEC 2026)
- **TORAI** (Pham et al., ACM FSE 2026)
- **CARAF** (Tang et al., IEEE TETC 2026)
- **NetEdit** (Zhang et al., ACM SIGCOMM 2024)

---

## Architecture Overview

```
[ Tier 1: Pre-Crash Sensory Nervous System (Ring 0 Kernel Space) ]
  ├── Tracepoints: sys_enter_connect, sys_enter_futex, sys_exit_futex, sock:sock_exceed_buf_limit
  ├── K-Sense: sk_rmem_alloc socket queue fill derivative monitoring
  ├── Beyond Thread States: task_struct states & futex mutex lockup profiling
  ├── CrossTrace: In-band TCP Option Span ID tracking and header injection
  └── BPF RingBuffer (256 pages) & In-Kernel Hash Maps (low-overhead sub-millisecond dispatch)
        │
        │ Sub-millisecond RingBuffer stream & sliding-window hysteresis
        ▼
[ Tier 2: Diagnostic Brain (User-Space Analytical Cortex) ]
  ├── Collector / Namespace Resolver: Resolves PID/cgroup to Pod/Container & Service DAG
  ├── Dynamic Topology Engine: CrossTrace deterministic in-band multi-hop service call graph
  ├── Sub-Graph Slicer: Localized k-hop extraction (caps search space to 10-50 nodes vs 5,000)
  ├── TORAI TCORW Solver: Anomaly-weighted PageRank random walk (converges in < 2ms)
  └── CARAF Classifier: Disambiguates internal deadlocks from bare-metal noisy-neighbor contention
        │
        ▼
[ Tier 3: Surgical Self-Healing (Two-Phase Progressive Actuation) ]
  ├── Phase 1 (Microsecond Mitigation, < 1ms):
  │   └── NetEdit BpfAdapter at tc / cgroup_skb to dynamically drain traffic from failing socket
  └── Phase 2 (Asynchronous Remediation, 2-5s):
      ├── Internal Deadlock -> Targeted Container Restart (Docker/K8s API)
      ├── Host Residual / Noisy Neighbor -> Kubernetes Pod Eviction & Node Rescheduling
      └── Connection Retry Storm -> Cgroup v2 CPU Bandwidth Throttling (cpu.max = 10%)
```

---

## Directory Structure

```
ebpf_triage_system/
├── ebpf/
│   └── connect_tracker.c       # Multi-vector eBPF sensor (connect, futex, socket buffer, drain map)
├── collector/
│   ├── __init__.py
│   └── namespace_resolver.py   # PID/cgroup/namespace resolver with service topology mapping
├── engine/
│   ├── __init__.py
│   ├── loop_detector.py        # Thread Dynamics Graph Engine & Tarjan SCC cycle detector
│   ├── topology_graph.py       # CrossTrace in-band call graph & k-hop localized sub-graph extractor
│   └── rca_engine.py           # TORAI TCORW PageRank random walk & CARAF residual factor classifier
├── actuator/
│   ├── __init__.py
│   ├── netedit_actuator.py     # NetEdit BpfAdapter tc traffic drain actuator (< 1ms mitigation)
│   ├── cgroup_actuator.py      # Direct cgroup v2 cpu.max writer (10% CPU quota)
│   └── docker_actuator.py      # Docker Engine SDK & Kubernetes pod eviction client
├── tests/
│   ├── conftest.py
│   └── test_pipeline.py        # Complete pytest test suite (16 automated tests)
├── controller.py               # Main orchestration pipeline & multi-tier demo runner
├── requirements.txt            # Python dependencies (networkx, docker)
└── Dockerfile                  # Containerized deployment with BCC & Linux kernel headers
```

---

## How to Run

### 1. Synthetic Demonstration Mode (Windows / macOS / Linux without root)
Demonstrates the full multi-tier microservice architecture, CrossTrace span propagation, K-Sense buffer starvation, Beyond Thread States futex deadlock, TORAI TCORW ranking, CARAF residual classification, and NetEdit two-phase self-healing:

```bash
# Run demonstration
py controller.py --demo

# Customize parameters
py controller.py --demo --window 1.5 --threshold 10 --stage2-delay 2.5
```

### 2. Live Linux eBPF Mode (Requires Linux Kernel & Root / CAP_BPF)
Requires `bcc` installed (`apt-get install bpfcc-tools python3-bpfcc` on Ubuntu/Debian):

```bash
sudo python3 controller.py
```

### 3. Running via Docker & Docker Compose (Containerized)
Both synthetic demonstration and live host eBPF remediation can be run directly inside Docker:

```bash
# Option A: Run the multi-tier demonstration inside Docker
.\docker.cmd compose run --rm demo-agent

# Option B: Run the full live closed-loop triage stack (Redis + Victim App + Privileged eBPF Agent)
.\docker.cmd compose up -d

# Check live eBPF telemetry & triage logs
.\docker.cmd logs -f ebpf-agent

# Stop services
.\docker.cmd compose down
```
For the complete step-by-step testbed failure injection walkthrough, see [DOCKER_GUIDE.md](file:///c:/Users/sanda/Downloads/os%20project/ebpf_triage_system/DOCKER_GUIDE.md).

### 4. Running the Test Suite

```bash
py -m pytest tests -v
```
