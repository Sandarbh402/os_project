/**
 * Autonomous Closed-Loop Orchestration Pipeline - Frontend Dashboard Client
 * Light Theme: Alabaster Canvas with Royal Amethyst & Terracotta Accents
 * (Zero Black, Zero Blue, Zero Green)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Lucide Icons Initialization
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Set Chart.js global defaults for light theme
  if (window.Chart) {
    Chart.defaults.font.family = "'JetBrains Mono', monospace";
    Chart.defaults.color = "#78716c";
  }

  // --- 1. Vis.js Network Dynamic Topology Setup ---
  const container = document.getElementById("network-canvas");
  const nodesDataSet = new vis.DataSet([]);
  const edgesDataSet = new vis.DataSet([]);
  let network = null;
  let currentNodesMap = {};

  const networkOptions = {
    layout: {
      hierarchical: {
        enabled: true,
        direction: "LR", // Left-to-Right architectural call chain
        sortMethod: "directed",
        levelSeparation: 220,
        nodeSpacing: 130,
        treeSpacing: 150
      }
    },
    physics: {
      hierarchicalRepulsion: {
        centralGravity: 0.0,
        springLength: 100,
        springConstant: 0.01,
        nodeDistance: 130,
        damping: 0.09
      },
      stabilization: { iterations: 100 }
    },
    nodes: {
      shape: "box",
      margin: { top: 12, right: 16, bottom: 12, left: 16 },
      borderWidth: 2,
      shadow: {
        enabled: true,
        color: "rgba(120, 113, 108, 0.15)",
        size: 8,
        x: 0,
        y: 3
      },
      font: {
        color: "#1c1917",
        face: "'JetBrains Mono', monospace",
        size: 13,
        bold: { color: "#1c1917", size: 13 }
      }
    },
    edges: {
      arrows: {
        to: { enabled: true, scaleFactor: 1.0, type: "arrow" }
      },
      width: 2.5,
      color: {
        color: "#78716c", // Clear, visible warm stone
        highlight: "#ea580c",
        hover: "#ea580c"
      },
      smooth: {
        type: "cubicBezier",
        forceDirection: "horizontal",
        roundness: 0.35
      },
      font: {
        color: "#44403c",
        face: "'JetBrains Mono', monospace",
        size: 11,
        align: "top",
        background: "#fbfaf8",
        strokeWidth: 2,
        strokeColor: "#e8e2d8"
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      zoomView: true,
      dragView: true
    }
  };

  network = new vis.Network(container, { nodes: nodesDataSet, edges: edgesDataSet }, networkOptions);

  // Click on node in graph to inspect
  let inspectedNodeId = null;

  function updateInspector(nodeId) {
    if (!nodeId) return;
    const nodeData = currentNodesMap[nodeId];
    if (nodeData) {
      document.getElementById("inspect-node-name").textContent = nodeData.label || nodeId;
      document.getElementById("inspect-cid").textContent = (nodeData.container_id || "unknown").slice(0, 12);
      document.getElementById("inspect-pid").textContent = nodeData.pid || "-";
      document.getElementById("inspect-endpoint").textContent = nodeData.endpoint || "-";
      
      const statusEl = document.getElementById("inspect-status");
      statusEl.textContent = nodeData.status || "NORMAL";
      if (nodeData.status === "ALERT") {
        statusEl.className = "text-rose-700 font-bold";
      } else if (nodeData.status === "MITIGATED") {
        statusEl.className = "text-purple-700 font-bold";
      } else if (nodeData.status === "HEALED") {
        statusEl.className = "text-orange-700 font-bold";
      } else {
        statusEl.className = "text-stone-700 font-bold";
      }

      const quotaEl = document.getElementById("inspect-quota");
      if (quotaEl) {
        if (nodeData.status === "HEALED" && window.latestRcaAction && window.latestRcaAction.includes("10%")) {
          quotaEl.textContent = "10% (cpu.max throttled)";
          quotaEl.className = "text-orange-700 font-bold";
        } else if (nodeData.status === "MITIGATED") {
          quotaEl.textContent = "0% (Traffic Draining)";
          quotaEl.className = "text-purple-700 font-bold";
        } else {
          quotaEl.textContent = "100% (Unthrottled)";
          quotaEl.className = "text-stone-800 font-bold";
        }
      }
    }
  }

  network.on("click", (params) => {
    if (params.nodes.length > 0) {
      inspectedNodeId = params.nodes[0];
      updateInspector(inspectedNodeId);
    }
  });


  // --- 2. Chart.js Real-Time Telemetry Setup (Light Theme) ---
  const maxDataPoints = 25;
  const initialLabels = Array.from({ length: maxDataPoints }, (_, i) => `-${maxDataPoints - i}s`);

  // Chart 1: Connection Retries vs Threshold (Terracotta & Crimson)
  const ctxRetries = document.getElementById("chart-retries").getContext("2d");
  const chartRetries = new Chart(ctxRetries, {
    type: "line",
    data: {
      labels: [...initialLabels],
      datasets: [
        {
          label: "Connection Retries / sec",
          data: Array(maxDataPoints).fill(0),
          borderColor: "#ea580c",
          backgroundColor: "rgba(234, 88, 12, 0.08)",
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointRadius: 2
        },
        {
          label: "Storm Threshold (10/s)",
          data: Array(maxDataPoints).fill(10),
          borderColor: "rgba(225, 29, 72, 0.8)",
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { display: false },
        y: {
          min: 0,
          suggestedMax: 30,
          grid: { color: "rgba(232, 226, 216, 0.9)" },
          ticks: { color: "#78716c", font: { size: 10 } }
        }
      }
    }
  });

  // Chart 2: K-Sense Socket Buffer Allocation (Royal Amethyst)
  const ctxBuffer = document.getElementById("chart-buffer").getContext("2d");
  const chartBuffer = new Chart(ctxBuffer, {
    type: "line",
    data: {
      labels: [...initialLabels],
      datasets: [
        {
          label: "sk_rmem_alloc (KB)",
          data: Array(maxDataPoints).fill(10),
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.08)",
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointRadius: 2
        },
        {
          label: "Buffer Limit (1024 KB)",
          data: Array(maxDataPoints).fill(1024),
          borderColor: "rgba(225, 29, 72, 0.6)",
          borderWidth: 1.5,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { display: false },
        y: {
          min: 0,
          suggestedMax: 1100,
          grid: { color: "rgba(232, 226, 216, 0.9)" },
          ticks: { color: "#78716c", font: { size: 10 } }
        }
      }
    }
  });

  function pushTelemetryData(retries, sk_rmem_bytes) {
    const rVal = Number(retries) || 0;
    const bValKB = Math.round((Number(sk_rmem_bytes) || 0) / 1024);

    chartRetries.data.datasets[0].data.shift();
    chartRetries.data.datasets[0].data.push(rVal);
    chartRetries.update("none");

    chartBuffer.data.datasets[0].data.shift();
    chartBuffer.data.datasets[0].data.push(bValKB);
    chartBuffer.update("none");

    document.getElementById("metric-retries").textContent = `${rVal} / sec`;
    const pct = Math.min(Math.round((bValKB / 1024) * 100), 100);
    document.getElementById("metric-buffer").textContent = `${bValKB} KB (${pct}%)`;
  }

  // Periodic ambient pulse if idle
  setInterval(() => {
    pushTelemetryData(0, Math.floor(Math.random() * 20000));
  }, 1200);


  // --- 3. Topology Renderer Helper (Light Theme Palette) ---
  function renderTopology(topologyData) {
    if (!topologyData || !topologyData.nodes) return;

    currentNodesMap = {};
    const visNodes = topologyData.nodes.map((n) => {
      currentNodesMap[n.id] = n;
      let bg = "#ffffff";
      let border = "#a8a29e"; // Warm Stone Border for Healthy Baseline
      let shadowColor = "rgba(168, 162, 158, 0.25)";
      let statusTag = "HEALTHY";

      if (n.status === "ALERT") {
        border = "#e11d48"; // High-voltage Crimson Coral
        shadowColor = "rgba(225, 29, 72, 0.5)";
        bg = "#fff1f2";
        statusTag = "CRASH ALERT";
      } else if (n.status === "MITIGATED") {
        border = "#9333ea"; // Royal Violet (NetEdit tc Drain)
        shadowColor = "rgba(147, 51, 234, 0.45)";
        bg = "#faf5ff";
        statusTag = "PHASE 1 DRAINED";
      } else if (n.status === "HEALED") {
        border = "#ea580c"; // Terracotta Orange (Phase 2 Healed)
        shadowColor = "rgba(234, 88, 12, 0.45)";
        bg = "#fff7ed";
        statusTag = "PHASE 2 HEALED";
      }

      return {
        id: n.id,
        level: n.level !== undefined ? n.level : 1,
        label: `${n.label}\n(${n.endpoint || n.id})\n[${statusTag}]`,
        color: {
          background: bg,
          border: border,
          highlight: { background: bg, border: "#ea580c" }
        },
        shadow: {
          enabled: true,
          color: shadowColor,
          size: n.status === "ALERT" ? 22 : (n.status === "MITIGATED" || n.status === "HEALED" ? 16 : 6)
        }
      };
    });

    const visEdges = topologyData.edges.map((e) => {
      const isErr = Boolean(e.is_error);
      const edgeColor = isErr ? "#e11d48" : "#78716c";
      const edgeWidth = isErr ? 4.0 : 2.5;

      return {
        id: `e-${e.from}-${e.to}`,
        from: e.from,
        to: e.to,
        label: `${e.latency_ms}ms`,
        width: edgeWidth,
        color: {
          color: edgeColor,
          highlight: isErr ? "#e11d48" : "#ea580c",
          hover: "#ea580c"
        },
        dashes: isErr ? [6, 4] : false
      };
    });

    // Smooth dataset update (preserves physical stability, no canvas bouncing)
    visNodes.forEach(node => {
      if (nodesDataSet.get(node.id)) {
        nodesDataSet.update(node);
      } else {
        nodesDataSet.add(node);
      }
    });

    visEdges.forEach(edge => {
      if (edgesDataSet.get(edge.id)) {
        edgesDataSet.update(edge);
      } else {
        edgesDataSet.add(edge);
      }
    });

    // Keep inspector updated live if a node is currently selected
    if (inspectedNodeId) {
      updateInspector(inspectedNodeId);
    }
  }


  // --- 4. Experiment Stepper & Status UI Updater ---
  function updateExperimentTracker(step, status, title, desc) {
    const badgeEl = document.getElementById("experiment-current-badge");
    const descEl = document.getElementById("experiment-desc-text");

    if (badgeEl && status) {
      if (status === "RUNNING") {
        badgeEl.className = "text-[11px] font-mono-code px-3 py-1 rounded-full bg-orange-100 text-orange-800 font-bold border border-orange-300 animate-pulse";
        badgeEl.textContent = `STATUS: PHASE ${step} RUNNING`;
      } else if (status === "COMPLETED") {
        badgeEl.className = "text-[11px] font-mono-code px-3 py-1 rounded-full bg-purple-100 text-purple-800 font-bold border border-purple-300";
        badgeEl.textContent = (step === 0 || step === 4) ? "STATUS: ALL 4 PHASES COMPLETED" : `STATUS: PHASE ${step} COMPLETED`;
      } else {
        badgeEl.className = "text-[11px] font-mono-code px-3 py-1 rounded-full bg-stone-100 text-stone-700 font-bold border border-warm-border";
        badgeEl.textContent = "STATUS: STANDBY (PHASE 1 ACTIVE)";
      }
    }

    if (descEl && (title || desc)) {
      descEl.innerHTML = `<strong>${title || ""}:</strong> ${desc || ""}`;
    }

    // Update 4 phase cards
    for (let i = 1; i <= 4; i++) {
      const card = document.getElementById(`step-card-${i}`);
      const badge = document.getElementById(`step-badge-${i}`);
      if (!card || !badge) continue;

      if (i < step || (step === 0 && status === "COMPLETED")) {
        // Already completed
        card.className = "p-3 rounded-xl border border-purple-300 bg-purple-50/50 transition";
        badge.className = "text-[10px] px-1.5 py-0.5 rounded bg-purple-200 text-purple-800 font-bold";
        badge.textContent = "DONE ✓";
      } else if (i === step) {
        if (status === "RUNNING") {
          card.className = "p-3 rounded-xl border-2 border-orange-500 bg-orange-50 shadow-md shadow-orange-500/10 transition animate-pulse";
          badge.className = "text-[10px] px-1.5 py-0.5 rounded bg-orange-500 text-white font-bold";
          badge.textContent = "ACTIVE";
        } else if (status === "COMPLETED") {
          card.className = "p-3 rounded-xl border border-purple-400 bg-purple-50 transition";
          badge.className = "text-[10px] px-1.5 py-0.5 rounded bg-purple-200 text-purple-800 font-bold";
          badge.textContent = "DONE ✓";
        } else {
          card.className = "p-3 rounded-xl border-2 border-purple-300 bg-purple-50/70 transition";
          badge.className = "text-[10px] px-1.5 py-0.5 rounded bg-purple-200 text-purple-800 font-bold";
          badge.textContent = "READY";
        }
      } else {
        // Pending / Waiting
        card.className = "p-3 rounded-xl border border-warm-border bg-stone-50/70 transition opacity-75";
        badge.className = "text-[10px] px-1.5 py-0.5 rounded bg-stone-200 text-stone-600 font-semibold";
        badge.textContent = "WAITING";
      }
    }
  }

  function updateStatus(statusData) {
    if (!statusData) return;

    // Runtime mode
    if (statusData.runtime_mode) {
      document.getElementById("runtime-mode-text").textContent = statusData.runtime_mode;
    }

    // Update experiment stepper if present
    if (statusData.experiment_step !== undefined) {
      updateExperimentTracker(
        statusData.experiment_step,
        statusData.experiment_status,
        statusData.experiment_title,
        statusData.experiment_desc
      );
    }

    // System State Pill
    const pill = document.getElementById("status-pill");
    const pText = document.getElementById("status-text");
    const state = statusData.system_state;

    if (state === "ANOMALY_DETECTED") {
      pill.className = "flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-rose-300 bg-rose-50 text-rose-800 text-xs font-mono-code font-bold shadow-sm";
      pText.textContent = "ANOMALY DETECTED";
    } else if (state === "PHASE1_DRAINING") {
      pill.className = "flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-purple-300 bg-purple-50 text-purple-800 text-xs font-mono-code font-bold shadow-sm";
      pText.textContent = "PHASE 1: RING 0 TC DRAIN";
    } else if (state === "PHASE2_HEALING") {
      pill.className = "flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-orange-300 bg-orange-50 text-orange-800 text-xs font-mono-code font-bold shadow-sm";
      pText.textContent = "PHASE 2: SURGICAL HEALING";
    } else {
      pill.className = "flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-purple-300 bg-purple-50 text-purple-800 text-xs font-mono-code font-semibold shadow-sm";
      pText.textContent = "HEALTHY BASELINE";
    }

    // Indicators for Two-Phase Actuation Card
    const p1Ind = document.getElementById("p1-indicator");
    const p1Stat = document.getElementById("p1-status");
    const p2Ind = document.getElementById("p2-indicator");
    const p2Stat = document.getElementById("p2-status");

    if (state === "PHASE1_DRAINING") {
      p1Ind.className = "w-2.5 h-2.5 rounded-full bg-purple-600 animate-ping";
      p1Stat.className = "text-[10px] font-mono-code text-purple-800 font-bold";
      p1Stat.textContent = "DRAINING ACTIVE";
    } else if (state === "PHASE2_HEALING") {
      p1Ind.className = "w-2.5 h-2.5 rounded-full bg-purple-600";
      p1Stat.textContent = "RESTORED";
      p2Ind.className = "w-2.5 h-2.5 rounded-full bg-orange-600 animate-ping";
      p2Stat.className = "text-[10px] font-mono-code text-orange-800 font-bold";
      p2Stat.textContent = "REMEDIATING";
    } else {
      p1Ind.className = "w-2.5 h-2.5 rounded-full bg-stone-300";
      p1Stat.className = "text-[10px] font-mono-code text-stone-400 font-bold";
      p1Stat.textContent = "STANDBY";
      p2Ind.className = "w-2.5 h-2.5 rounded-full bg-stone-300";
      p2Stat.className = "text-[10px] font-mono-code text-stone-400 font-bold";
      p2Stat.textContent = "STANDBY";
    }

    // Update eBPF XDP Driver-Level Metrics
    if (statusData.xdp_metrics) {
      const xdp = statusData.xdp_metrics;
      const xdpPktsEl = document.getElementById("xdp-pkts-dropped");
      const xdpSkbEl = document.getElementById("xdp-skb-saved");
      if (xdpPktsEl) xdpPktsEl.textContent = `${(xdp.total_packets_dropped || 0).toLocaleString()} pkts`;
      if (xdpSkbEl) xdpSkbEl.textContent = `${(xdp.sk_buff_saved_kb || 0).toLocaleString()} KB`;
    }

    // Update TORAI RCA card
    const rca = statusData.latest_rca;
    if (rca && rca.action) {
      window.latestRcaAction = rca.action;
    }
    if (rca && rca.root_cause) {
      document.getElementById("rca-confidence-badge").textContent = `${rca.confidence}% CONFIDENCE`;
      document.getElementById("rca-confidence-badge").className = "text-[10px] font-mono-code px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-bold";

      document.getElementById("rca-root-node").innerHTML = `
        <span class="text-rose-700 flex items-center gap-1.5">
          <i data-lucide="alert-triangle" class="w-4 h-4 text-rose-600"></i> ${rca.root_cause}
        </span>
      `;
      document.getElementById("rca-subgraph-info").textContent = `State Space Sliced: ${rca.subgraph_nodes || 4} nodes (${rca.subgraph_edges || 3} edges)`;

      // Ranked candidates list
      const candContainer = document.getElementById("rca-candidates-list");
      candContainer.innerHTML = "";
      (rca.ranked_causes || []).forEach((c, idx) => {
        const row = document.createElement("div");
        row.className = "flex items-center justify-between p-2 rounded bg-stone-50 border border-warm-border text-[11px] font-mono-code";
        row.innerHTML = `
          <span class="text-stone-700">${idx + 1}. ${c.node}</span>
          <span class="text-purple-700 font-bold">${c.score}</span>
        `;
        candContainer.appendChild(row);
      });

      // Update CARAF card
      document.getElementById("caraf-badge").textContent = rca.classification || "ANOMALY";
      document.getElementById("caraf-badge").className = "text-[10px] font-mono-code px-2 py-0.5 rounded bg-orange-50 text-orange-800 border border-orange-200 font-bold";
      document.getElementById("caraf-diagnosis").textContent = rca.diagnosis || "Contention detected";
      document.getElementById("caraf-action").textContent = rca.action || "Container Remediation";

    } else if (state === "HEALTHY") {
      if (rca && rca.action) {
        document.getElementById("rca-confidence-badge").textContent = `${rca.confidence || 100}% RESOLVED`;
        document.getElementById("rca-confidence-badge").className = "text-[10px] font-mono-code px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 font-bold";
        document.getElementById("rca-root-node").innerHTML = `
          <i data-lucide="check-circle" class="w-4 h-4 text-purple-700"></i> ${rca.root_cause} (Healed)
        `;
        document.getElementById("caraf-badge").textContent = "REMEDIATED";
        document.getElementById("caraf-badge").className = "text-[10px] font-mono-code px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 font-bold";
        document.getElementById("caraf-diagnosis").textContent = rca.diagnosis || "All services operating within SLA";
        document.getElementById("caraf-action").textContent = `${rca.action} [APPLIED]`;
      } else {
        document.getElementById("rca-confidence-badge").textContent = "100% HEALTHY";
        document.getElementById("rca-confidence-badge").className = "text-[10px] font-mono-code px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 font-bold";
        document.getElementById("rca-root-node").innerHTML = `
          <i data-lucide="check-circle" class="w-4 h-4 text-purple-700"></i> No Anomaly Detected
        `;
        document.getElementById("rca-subgraph-info").textContent = `State Space: 5 nodes in full topology`;
        document.getElementById("rca-candidates-list").innerHTML = `<div class="text-stone-400 text-xs italic font-mono-code">Awaiting anomaly alert...</div>`;
        document.getElementById("caraf-badge").textContent = "INACTIVE";
        document.getElementById("caraf-badge").className = "text-[10px] font-mono-code px-2 py-0.5 rounded bg-stone-100 text-stone-600 border border-warm-border font-bold";
        document.getElementById("caraf-diagnosis").textContent = "All services operating within SLA";
        document.getElementById("caraf-action").textContent = "Standby";
      }
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  // --- 5. Light Parchment Terminal Audit Log Appender ---
  const terminalEl = document.getElementById("terminal-stream");

  function appendLog(logEntry) {
    if (!logEntry) return;

    const row = document.createElement("div");
    let colorClass = "text-stone-700";

    if (logEntry.level === "ALERT") {
      colorClass = "text-rose-700 font-bold";
    } else if (logEntry.level === "MITIGATION") {
      colorClass = "text-purple-800 font-semibold";
    } else if (logEntry.level === "REMEDIATION" || logEntry.level === "SUCCESS") {
      colorClass = "text-orange-700 font-semibold";
    }

    row.className = `${colorClass} py-0.5 font-mono-code`;
    row.innerHTML = `<span class="text-stone-400">[${logEntry.time || ""}]</span> <span class="text-stone-500">[${logEntry.level}]</span> ${logEntry.message}`;
    terminalEl.appendChild(row);

    // Auto-scroll
    terminalEl.scrollTop = terminalEl.scrollHeight;
  }


  // --- 6. WebSocket Connection Handler ---
  let ws = null;

  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      appendLog({ time: new Date().toLocaleTimeString(), level: "INFO", message: "WebSocket telemetry stream connected." });
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "init_state") {
          updateStatus(msg.data.status);
          renderTopology(msg.data.topology);
          if (msg.data.logs) {
            terminalEl.innerHTML = "";
            msg.data.logs.forEach(appendLog);
          }
        } else if (msg.type === "state_update") {
          updateStatus(msg.data.status);
          renderTopology(msg.data.topology);
        } else if (msg.type === "log_event") {
          appendLog(msg.data);
        } else if (msg.type === "telemetry_pulse") {
          pushTelemetryData(msg.data.retries, msg.data.sk_rmem_alloc);
        } else if (msg.type === "experiment_step") {
          updateExperimentTracker(
            msg.data.step,
            msg.data.status,
            msg.data.title,
            msg.data.desc
          );
        } else if (msg.type === "benchmark_progress") {
          appendLog({ time: new Date().toLocaleTimeString(), level: "INFO", message: `[BENCHMARK] ${msg.data.message}` });
        } else if (msg.type === "benchmark_result") {
          openBenchmarkModal(msg.data);
        }
      } catch (err) {
        console.error("WS Parse error", err);
      }
    };

    ws.onclose = () => {
      appendLog({ time: new Date().toLocaleTimeString(), level: "WARN", message: "WebSocket disconnected. Reconnecting in 2s..." });
      setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = (err) => {
      console.warn("WebSocket error:", err);
    };
  }

  connectWebSocket();


  // --- 7. Control Buttons Action Wiring ---
  async function triggerFault(scenario, extra = {}) {
    try {
      const resp = await fetch("/api/fault/inject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, ...extra })
      });
      const data = await resp.json();
      console.log("Fault triggered:", data);
    } catch (err) {
      console.error("Fault request error", err);
    }
  }

  document.getElementById("btn-full-demo").addEventListener("click", () => {
    triggerFault("full_demo");
  });

  document.getElementById("btn-fault-storm").addEventListener("click", () => {
    triggerFault("retry_storm", { retries: 28 });
  });

  document.getElementById("btn-fault-buffer").addEventListener("click", () => {
    triggerFault("buffer_starvation");
  });

  document.getElementById("btn-fault-futex").addEventListener("click", () => {
    triggerFault("futex_deadlock");
  });

  document.getElementById("btn-fault-caraf").addEventListener("click", () => {
    triggerFault("host_contention");
  });

  document.getElementById("btn-reset").addEventListener("click", async () => {
    await fetch("/api/pipeline/reset", { method: "POST" });
  });


  // --- 8. Sliders & Parameter Tuning Wiring ---
  const sWin = document.getElementById("slider-window");
  const sThr = document.getElementById("slider-threshold");
  const sSt2 = document.getElementById("slider-stage2");

  function sendConfigUpdate() {
    fetch("/api/pipeline/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        window: sWin.value,
        threshold: sThr.value,
        stage2_delay: sSt2.value
      })
    });
  }

  sWin.addEventListener("input", (e) => {
    document.getElementById("val-window").textContent = `${e.target.value}s`;
    sendConfigUpdate();
  });

  sThr.addEventListener("input", (e) => {
    document.getElementById("val-threshold").textContent = `${e.target.value} retries`;
    sendConfigUpdate();
  });

  sSt2.addEventListener("input", (e) => {
    document.getElementById("val-stage2").textContent = `${e.target.value}s`;
    sendConfigUpdate();
  });

  // --- 9. Side-by-Side A/B Benchmark Modal Actions ---
  const benchmarkModal = document.getElementById("benchmark-modal");

  function openBenchmarkModal(data) {
    if (benchmarkModal) {
      benchmarkModal.classList.remove("hidden");
    }
  }

  function closeBenchmarkModal() {
    if (benchmarkModal) {
      benchmarkModal.classList.add("hidden");
    }
  }

  const btnOpenBenchmark = document.getElementById("btn-benchmark");
  if (btnOpenBenchmark) {
    btnOpenBenchmark.addEventListener("click", async () => {
      openBenchmarkModal();
      appendLog({ time: new Date().toLocaleTimeString(), level: "INFO", message: "[BENCHMARK] Initiating Comparative A/B Benchmark Suite..." });
      try {
        await fetch("/api/benchmark/run", { method: "POST" });
      } catch (err) {
        console.error("Benchmark launch error:", err);
      }
    });
  }

  const btnRerunBenchmark = document.getElementById("btn-rerun-benchmark");
  if (btnRerunBenchmark) {
    btnRerunBenchmark.addEventListener("click", async () => {
      appendLog({ time: new Date().toLocaleTimeString(), level: "INFO", message: "[BENCHMARK] Re-running Comparative A/B Benchmark..." });
      try {
        await fetch("/api/benchmark/run", { method: "POST" });
      } catch (err) {
        console.error("Benchmark re-run error:", err);
      }
    });
  }

  const btnCloseBenchmark = document.getElementById("btn-close-benchmark");
  if (btnCloseBenchmark) btnCloseBenchmark.addEventListener("click", closeBenchmarkModal);

  const btnDismissBenchmark = document.getElementById("btn-dismiss-benchmark");
  if (btnDismissBenchmark) btnDismissBenchmark.addEventListener("click", closeBenchmarkModal);

  if (benchmarkModal) {
    benchmarkModal.addEventListener("click", (e) => {
      if (e.target === benchmarkModal) closeBenchmarkModal();
    });
  }

});
