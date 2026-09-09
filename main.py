#!/usr/bin/env python3
# Copyright 2026 hangtiancheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
NS-3 Swift TCP Simulation Management Tool
Features: Simulation (sim) / Plotting (draw) / Summary Report (summary)
"""

import argparse
import csv
import glob
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# =============================================================================
# Global Default Configuration
# =============================================================================
DEFAULT_DURATION = 20
DEFAULT_N_LEAF = 3
DEFAULT_SIM_SEED = 42
DEFAULT_PROTOCOLS = ["TcpSwift", "TcpNewReno", "TcpCubic", "TcpBbr"]
AGENT_SCRIPT = "./contrib/opengym/examples/swift-tcp/test_swift.py"

# 36 scenario definitions: (name, access_bw, bottleneck_bw, access_delay, bottleneck_delay)
SCENARIOS: List[Tuple[str, str, str, str, str]] = [
    # --- Category 1: Intra-Rack Data Center ---
    ("intra_rack_10g", "25Gbps", "10Gbps", "1us", "2us"),
    ("intra_rack_25g", "25Gbps", "25Gbps", "1us", "2us"),
    # --- Category 2: Leaf-Spine Architecture ---
    ("leaf_spine_20g", "50Gbps", "20Gbps", "2us", "5us"),
    ("leaf_spine_50g", "50Gbps", "50Gbps", "2us", "5us"),
    # --- Category 3: Oversubscription Convergence ---
    ("oversub_4to1_10g", "10Gbps", "2.5Gbps", "2us", "5us"),
    ("oversub_4to1_40g", "40Gbps", "10Gbps", "2us", "5us"),
    ("oversub_2to1_25g", "25Gbps", "12.5Gbps", "2us", "5us"),
    ("oversub_2to1_50g", "50Gbps", "25Gbps", "2us", "5us"),
    # --- Category 4: Congestion Level Gradient ---
    ("congested_light", "10Gbps", "5Gbps", "2us", "5us"),
    ("congested_medium", "10Gbps", "2Gbps", "2us", "5us"),
    # 20:1 -- was 10Gbps/1Gbps, identical to dc_oversub_10to1 (duplicate rows)
    ("congested_heavy", "10Gbps", "500Mbps", "2us", "5us"),
    # --- Category 5: Cross-Pod / Cross-DC ---
    ("cross_pod_10g", "25Gbps", "10Gbps", "5us", "50us"),
    ("cross_pod_20g", "50Gbps", "20Gbps", "5us", "50us"),
    ("cross_dc_wan", "10Gbps", "1Gbps", "10us", "5ms"),
    # --- Category 6: RDMA-like Ultra-Low Latency ---
    ("rdma_like_25g", "25Gbps", "25Gbps", "500ns", "1us"),
    ("rdma_like_50g", "50Gbps", "50Gbps", "500ns", "1us"),
    # --- Category 7: Mixed Traffic & Asymmetric ---
    ("mixed_small_flow", "10Gbps", "2Gbps", "2us", "10us"),
    ("mixed_large_flow", "50Gbps", "12.5Gbps", "2us", "10us"),
    ("asymmetric_high", "50Gbps", "1Gbps", "1us", "10us"),
    ("symmetric_low", "1Gbps", "1Gbps", "5us", "20us"),
    # --- Category 8: Data Center Bandwidth Scaling ---
    ("dc_100m", "1Gbps", "100Mbps", "2us", "5us"),
    ("dc_500m", "1Gbps", "500Mbps", "2us", "5us"),
    ("dc_100g", "100Gbps", "100Gbps", "1us", "2us"),
    ("dc_oversub_10to1", "10Gbps", "1Gbps", "2us", "5us"),
    # --- Category 9: WiFi Wireless ---
    ("wifi_ac", "1Gbps", "400Mbps", "1ms", "5ms"),
    ("wifi_ax", "1Gbps", "600Mbps", "1ms", "3ms"),
    ("wifi_n", "100Mbps", "50Mbps", "2ms", "10ms"),
    ("wifi_legacy", "100Mbps", "10Mbps", "5ms", "20ms"),
    # --- Category 10: Cellular Mobile (LTE / 5G NR) ---
    ("lte_good", "100Mbps", "50Mbps", "5ms", "20ms"),
    ("lte_poor", "50Mbps", "10Mbps", "10ms", "50ms"),
    ("nr_5g_embb", "1Gbps", "500Mbps", "1ms", "5ms"),
    ("nr_5g_edge", "500Mbps", "100Mbps", "2ms", "10ms"),
    # --- Category 11: WAN / Satellite ---
    ("wan_metro", "10Gbps", "1Gbps", "100us", "2ms"),
    ("wan_longhaul", "10Gbps", "1Gbps", "500us", "25ms"),
    # LEO (Starlink-like) -- was identical to lte_good (duplicate rows)
    ("satellite_leo", "500Mbps", "150Mbps", "2ms", "25ms"),
    ("satellite_geo", "50Mbps", "10Mbps", "10ms", "300ms"),
]

# Run artifacts are named "<scenario>_<Protocol>_s<seed>". Older artifacts
# without the seed suffix still parse (seed is None then).
RUN_NAME_RE = re.compile(r"^(.+)_(Tcp[A-Za-z0-9]+)(?:_s(\d+))?$")


def parse_run_name(basename: str) -> Optional[Tuple[str, str, Optional[int]]]:
    m = RUN_NAME_RE.match(basename)
    if not m:
        return None
    seed = int(m.group(3)) if m.group(3) else None
    return m.group(1), m.group(2), seed


# =============================================================================
# Simulation Runner (run_sim)
# =============================================================================
def run_sim(
    protocol: str,
    scenario: str,
    access_bw: str,
    bottleneck_bw: str,
    access_delay: str,
    bottleneck_delay: str,
    log_dir: str,
    duration: int = DEFAULT_DURATION,
    n_leaf: int = DEFAULT_N_LEAF,
    sim_seed: int = DEFAULT_SIM_SEED,
    enable_udp_burst: int = 0,
    open_gym_port: int = 5555,
) -> bool:
    """Run a single simulation scenario, return True on success."""
    os.makedirs(log_dir, exist_ok=True)
    prefix = os.path.join(log_dir, f"{scenario}_{protocol}_s{sim_seed}")
    flowmon_file = f"{prefix}.flowmonitor"

    # Resume support: skip if flowmonitor already exists
    if os.path.isfile(flowmon_file):
        print(f"[SKIP] {scenario}_{protocol}_s{sim_seed} - flowmonitor already exists")
        return True

    print(f"[INFO] Running: Protocol={protocol}, Scenario={scenario}, Seed={sim_seed}")
    print(
        f"[INFO]   Access: {access_bw} @ {access_delay}, "
        f"Bottleneck: {bottleneck_bw} @ {bottleneck_delay}"
    )

    ns3_cmd = (
        f"swift-tcp"
        f" --transport_prot={protocol}"
        f" --access_bandwidth={access_bw}"
        f" --bottleneck_bandwidth={bottleneck_bw}"
        f" --access_delay={access_delay}"
        f" --bottleneck_delay={bottleneck_delay}"
        f" --duration={duration}"
        f" --nLeaf={n_leaf}"
        f" --simSeed={sim_seed}"
        f" --enable_udp_burst={enable_udp_burst}"
        f" --openGymPort={open_gym_port}"
        f" --queue_disc_type=ns3::RedQueueDisc"
        f" --prefix_name={prefix}"
    )

    ns3_log = f"{prefix}_ns3.log"
    start_time = time.time()

    try:
        if protocol == "TcpSwift":
            # TcpSwift: launch ns-3 in background, start Python agent after RL env is ready
            with open(ns3_log, "w") as log_f:
                ns3_proc = subprocess.Popen(
                    ["./ns3", "run", ns3_cmd],
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                )

            time.sleep(5)
            agent_started = False
            agent_proc = None

            for _ in range(60):
                # Check if ns3 process has exited unexpectedly
                poll_result = ns3_proc.poll()
                if poll_result is not None:
                    if not agent_started:
                        print(
                            f"[ERROR] ns3 process crashed before agent started (exit code: {poll_result})"
                        )
                        return False
                    break

                try:
                    with open(ns3_log, "r") as f:
                        content = f.read()
                        # Check for fatal errors
                        if (
                            "pure virtual method called" in content
                            or "terminate called" in content
                        ):
                            print("[ERROR] ns3 process encountered fatal error")
                            ns3_proc.terminate()
                            ns3_proc.wait(timeout=5)
                            return False
                        if "Waiting for Python" in content and not agent_started:
                            agent_started = True
                            agent_log = f"{prefix}_agent.log"
                            with open(agent_log, "w") as af:
                                # cwd must be set to the agent script directory,
                                # otherwise "from tcp_swift import TcpSwift" will fail
                                agent_cwd = os.path.dirname(
                                    os.path.abspath(AGENT_SCRIPT)
                                )
                                agent_proc = subprocess.Popen(
                                    [
                                        sys.executable,
                                        "-u",  # unbuffered stdout for real-time logging
                                        os.path.abspath(AGENT_SCRIPT),
                                        "--start=0",
                                        "--iterations=1",
                                        f"--port={open_gym_port}",
                                    ],
                                    stdout=af,
                                    stderr=subprocess.STDOUT,
                                    cwd=agent_cwd,
                                )
                except FileNotFoundError:
                    pass
                time.sleep(1)

            ns3_proc.wait()

            # Wait for agent process to finish
            if agent_proc:
                try:
                    agent_proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    agent_proc.terminate()

            if ns3_proc.returncode != 0:
                print(
                    f"[ERROR] Simulation failed: {scenario}_{protocol} (exit code: {ns3_proc.returncode})"
                )
                return False
        else:
            # Non-RL protocols: run synchronously
            with open(ns3_log, "w") as log_f:
                result = subprocess.run(
                    ["./ns3", "run", ns3_cmd],
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                )
            if result.returncode != 0:
                print(f"[ERROR] Simulation failed: {scenario}_{protocol}")
                return False

    except Exception as e:
        print(f"[ERROR] Exception in {scenario}_{protocol}: {e}")
        return False

    elapsed = int(time.time() - start_time)
    print(f"[INFO] Completed: {scenario} with {protocol} in {elapsed}s")
    return True


def cmd_sim(args):
    """Execute simulations (compare / compare-udp)."""
    enable_udp = 1 if args.udp else 0
    open_gym_port = 7777 if args.udp else 5555
    log_dir = "./logs/comparison-udp" if args.udp else "./logs/comparison"
    protocols = args.protocols or DEFAULT_PROTOCOLS
    scenarios = SCENARIOS

    # Filter scenarios if specified
    if args.scenario:
        scenarios = [s for s in scenarios if s[0] in args.scenario]
        if not scenarios:
            print(f"[ERROR] No matching scenarios: {args.scenario}")
            sys.exit(1)

    total = len(scenarios) * len(protocols) * args.num_seeds
    done = 0
    failed = 0
    seeds = [args.sim_seed + k for k in range(args.num_seeds)]

    for (
        scenario_name,
        access_bw,
        bottleneck_bw,
        access_delay,
        bottleneck_delay,
    ) in scenarios:
        for protocol in protocols:
            for seed in seeds:
                ok = run_sim(
                    protocol=protocol,
                    scenario=scenario_name,
                    access_bw=access_bw,
                    bottleneck_bw=bottleneck_bw,
                    access_delay=access_delay,
                    bottleneck_delay=bottleneck_delay,
                    log_dir=log_dir,
                    duration=args.duration,
                    n_leaf=args.n_leaf,
                    sim_seed=seed,
                    enable_udp_burst=enable_udp,
                    open_gym_port=open_gym_port,
                )
                done += 1
                if not ok:
                    failed += 1
                print(f"[PROGRESS] {done}/{total} (failed: {failed})")

    print(f"\n[DONE] {done - failed}/{total} succeeded, {failed} failed")


# =============================================================================
# Summary Report (summary)
# =============================================================================
def cmd_summary(args):
    """Extract metrics from existing logs and generate a CSV report (TCP and UDP)."""
    search_dirs = [
        "./logs/swift",
        "./logs/comparison",
        "./logs/swift-udp",
        "./logs/comparison-udp",
    ]

    os.makedirs("./logs/summary", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = f"./logs/summary/results_{timestamp}.csv"

    fieldnames = [
        "Scenario",
        "Protocol",
        "Type",
        "AccessBW",
        "BottleneckBW",
        "Seeds",
        "Throughput_Mbps",
        "LossRate_Pct",
    ]
    # (scenario, protocol, type) -> samples across seeds
    groups: Dict[Tuple[str, str, str], Dict] = {}
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        tag = "udp" if "udp" in search_dir.lower() else "tcp"
        for flowmon in glob.glob(os.path.join(search_dir, "*.flowmonitor")):
            basename = os.path.basename(flowmon).replace(".flowmonitor", "")
            parsed = parse_run_name(basename)
            if not parsed:
                continue
            scenario, protocol, _seed = parsed

            log_file = flowmon.replace(".flowmonitor", "_ns3.log")
            if not os.path.isfile(log_file):
                continue

            with open(log_file, "r") as f:
                content = f.read()

            # Prefer the TCP aggregate over the first per-flow match
            throughput = _grep_first(
                r"AggregateThroughput: ([\d.]+)", content
            ) or _grep_first(r"Throughput: ([\d.]+)", content)
            loss_rate = _grep_first(
                r"AggregateLossRate: ([\d.]+)", content
            ) or _grep_first(r"Loss Rate: ([\d.]+)", content)
            access_bw = _grep_first(r"AccessBW:\s*([\d.]+[A-Za-z]*)", content)
            bottleneck_bw = _grep_first(r"BottleneckBW:\s*([\d.]+[A-Za-z]*)", content)

            g = groups.setdefault(
                (scenario, protocol, tag),
                {"throughput": [], "loss": [], "access": "N/A", "bottle": "N/A"},
            )
            if throughput is not None:
                g["throughput"].append(float(throughput))
            if loss_rate is not None:
                g["loss"].append(float(loss_rate))
            if access_bw:
                g["access"] = access_bw
            if bottleneck_bw:
                g["bottle"] = bottleneck_bw

    rows = []
    for (scenario, protocol, tag), g in sorted(groups.items()):
        seeds = max(len(g["throughput"]), len(g["loss"]))
        rows.append(
            {
                "Scenario": scenario,
                "Protocol": protocol,
                "Type": tag,
                "AccessBW": g["access"],
                "BottleneckBW": g["bottle"],
                "Seeds": seeds,
                "Throughput_Mbps": (
                    f"{np.mean(g['throughput']):.4f}" if g["throughput"] else "N/A"
                ),
                "LossRate_Pct": (f"{np.mean(g['loss']):.6f}" if g["loss"] else "N/A"),
            }
        )

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] Summary saved to {out_path} ({len(rows)} records)")


def _grep_first(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text)
    return m.group(1) if m else None


# =============================================================================
# Data Models (FlowMonitor Parsing)
# =============================================================================
@dataclass
class FlowData:
    flow_id: int
    src_addr: str
    dst_addr: str
    protocol: int
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    lost_packets: int
    delay_sum_ns: float
    jitter_sum_ns: float
    duration_ns: float

    @property
    def throughput_mbps(self) -> float:
        if self.duration_ns > 0:
            return (self.rx_bytes * 8) / (self.duration_ns / 1e9) / 1e6
        return 0.0

    @property
    def avg_delay_ms(self) -> float:
        if self.rx_packets > 0:
            return (self.delay_sum_ns / self.rx_packets) / 1e6
        return 0.0

    @property
    def avg_jitter_ms(self) -> float:
        if self.rx_packets > 1:
            return (self.jitter_sum_ns / (self.rx_packets - 1)) / 1e6
        return 0.0

    @property
    def loss_rate(self) -> float:
        if self.tx_packets > 0:
            return (self.lost_packets / self.tx_packets) * 100
        return 0.0


@dataclass
class ScenarioResult:
    scenario: str
    protocol: str
    flows: List[FlowData] = field(default_factory=list)

    @property
    def forward_flows(self) -> List[FlowData]:
        # Forward data flows only (10.1.x.x -> 10.2.x.x, subnets assigned in
        # sim.cc). Reverse ACK flows are also protocol 6; including them
        # inflates throughput and deflates average delay.
        return [
            f
            for f in self.flows
            if f.protocol == 6
            and f.src_addr.startswith("10.1.")
            and f.dst_addr.startswith("10.2.")
        ]

    @property
    def total_throughput_mbps(self) -> float:
        return sum(f.throughput_mbps for f in self.forward_flows)

    @property
    def avg_delay_ms(self) -> float:
        tcp = [f for f in self.forward_flows if f.rx_packets > 0]
        return float(np.mean([f.avg_delay_ms for f in tcp])) if tcp else 0.0

    @property
    def avg_jitter_ms(self) -> float:
        tcp = [f for f in self.forward_flows if f.rx_packets > 1]
        return float(np.mean([f.avg_jitter_ms for f in tcp])) if tcp else 0.0

    @property
    def total_loss_rate(self) -> float:
        tcp = self.forward_flows
        tx = sum(f.tx_packets for f in tcp)
        lost = sum(f.lost_packets for f in tcp)
        return (lost / tx) * 100 if tx > 0 else 0.0


# =============================================================================
# FlowMonitor XML Parsing
# =============================================================================
def _parse_ns_time(time_str: str) -> float:
    if not time_str:
        return 0.0
    time_str = time_str.strip("+").replace("ns", "")
    try:
        return float(time_str)
    except ValueError:
        return 0.0


def parse_flowmonitor(filepath: str) -> List[FlowData]:
    tree = ET.parse(filepath)
    root = tree.getroot()

    flow_info = {}
    for c in root.findall(".//Ipv4FlowClassifier/Flow"):
        fid = int(c.get("flowId") or 0)
        flow_info[fid] = {
            "src_addr": c.get("sourceAddress") or "",
            "dst_addr": c.get("destinationAddress") or "",
            "protocol": int(c.get("protocol") or 0),
        }

    flows = []
    for f in root.findall(".//FlowStats/Flow"):
        fid = int(f.get("flowId") or 0)
        info = flow_info.get(fid, {"src_addr": "", "dst_addr": "", "protocol": 0})
        first_tx = _parse_ns_time(f.get("timeFirstTxPacket") or "0ns")
        last_rx = _parse_ns_time(f.get("timeLastRxPacket") or "0ns")
        dur = last_rx - first_tx if last_rx > first_tx else 0

        flows.append(
            FlowData(
                flow_id=fid,
                src_addr=info["src_addr"],
                dst_addr=info["dst_addr"],
                protocol=info["protocol"],
                tx_bytes=int(f.get("txBytes", 0)),
                rx_bytes=int(f.get("rxBytes", 0)),
                tx_packets=int(f.get("txPackets", 0)),
                rx_packets=int(f.get("rxPackets", 0)),
                lost_packets=int(f.get("lostPackets", 0)),
                delay_sum_ns=_parse_ns_time(f.get("delaySum") or "0ns"),
                jitter_sum_ns=_parse_ns_time(f.get("jitterSum") or "0ns"),
                duration_ns=dur,
            )
        )
    return flows


def load_all_results(logs_dir: str) -> List[ScenarioResult]:
    results = []
    for fp in glob.glob(os.path.join(logs_dir, "**", "*.flowmonitor"), recursive=True):
        basename = os.path.basename(fp).replace(".flowmonitor", "")
        parsed = parse_run_name(basename)
        if parsed:
            scenario, protocol, _seed = parsed
            results.append(ScenarioResult(scenario, protocol, parse_flowmonitor(fp)))
    return results


@dataclass
class AggregatedResult:
    """Metrics of one (scenario, protocol) averaged across seed repetitions.

    Field names mirror the ScenarioResult properties consumed by the plot
    and table functions, so both types are interchangeable there.
    """

    scenario: str
    protocol: str
    total_throughput_mbps: float
    avg_delay_ms: float
    avg_jitter_ms: float
    total_loss_rate: float
    seed_count: int


def aggregate_results(results: List[ScenarioResult]) -> List[AggregatedResult]:
    grouped: Dict[Tuple[str, str], List[ScenarioResult]] = {}
    for r in results:
        grouped.setdefault((r.scenario, r.protocol), []).append(r)
    aggregated = []
    for (scenario, protocol), runs in sorted(grouped.items()):
        aggregated.append(
            AggregatedResult(
                scenario=scenario,
                protocol=protocol,
                total_throughput_mbps=float(
                    np.mean([r.total_throughput_mbps for r in runs])
                ),
                avg_delay_ms=float(np.mean([r.avg_delay_ms for r in runs])),
                avg_jitter_ms=float(np.mean([r.avg_jitter_ms for r in runs])),
                total_loss_rate=float(np.mean([r.total_loss_rate for r in runs])),
                seed_count=len(runs),
            )
        )
    return aggregated


# =============================================================================
# Plotting Functions
# =============================================================================
PROTOCOL_COLORS_BAR = [
    "#42b883",  # Vue Green
    "#61dafb",  # React Blue
    "#dd0031",  # Angular Red

    "#673ab8",  # Preact Purple
]
PROTOCOL_COLORS_MAP = {
    "TcpSwift": "#42b883",  # Vue Green
    "TcpNewReno": "#61dafb",  # React Blue
    "TcpCubic": "#dd0031",  # Angular Red
    "TcpBbr": "#673ab8",  # Preact Purple
}
PROTOCOL_ORDER = ["TcpSwift", "TcpNewReno", "TcpCubic", "TcpBbr"]
FLOW_COLORS = {
    "TcpNewReno": "#61dafb",  # React Blue
    "TcpCubic": "#673ab8",  # Preact Purple
    "TcpBbr": "#42b883",  # Vue Green
    "TcpSwift": "#dd0031",  # Angular Red
}


def _format_missing_list(items: List[str]) -> str:
    return ", ".join(items) if items else "none"


def _warn_missing_protocol_entries(
    scenarios: Dict[str, Dict[str, "ScenarioResult"]], context: str
):
    expected = [p for p in PROTOCOL_ORDER if any(p in v for v in scenarios.values())]
    missing_lines = []
    for scenario in sorted(scenarios.keys()):
        missing = [p for p in expected if p not in scenarios[scenario]]
        if missing:
            missing_lines.append(
                f"  - {scenario}: missing protocols -> {_format_missing_list(missing)}"
            )

    if missing_lines:
        print(f"Warning: Missing protocol data detected in {context}:")
        for line in missing_lines:
            print(line)


def _warn_missing_flow_entries(
    data: Dict[str, Dict[str, Dict[int, float]]], protos: List[str], flows: List[int]
):
    missing_lines = []
    for scenario in sorted(data.keys()):
        for proto in protos:
            if proto not in data[scenario]:
                missing_lines.append(
                    f"  - {scenario}/{proto}: missing entire protocol log"
                )
                continue
            missing_flows = [
                str(fid) for fid in flows if fid not in data[scenario][proto]
            ]
            if missing_flows:
                missing_lines.append(
                    f"  - {scenario}/{proto}: missing flows -> "
                    f"{_format_missing_list(missing_flows)}"
                )

    if missing_lines:
        print("Warning: Missing flow throughput data detected:")
        for line in missing_lines:
            print(line)


def _annotate_missing(ax, x: float, label: str = "N/A", y: float = 0.02):
    ax.text(
        x,
        y,
        label,
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="bottom",
        fontsize=8,
        color="#555555",
        rotation=90,
    )


def _plot_sparse_bars(ax, x_pos, values, width, color, label=None):
    valid_x = []
    valid_vals = []
    for x, v in zip(x_pos, values):
        if v is None or np.isnan(v):
            continue
        valid_x.append(x)
        valid_vals.append(v)

    if valid_x:
        ax.bar(valid_x, valid_vals, width, label=label, color=color)


def plot_protocol_comparison(results: List[ScenarioResult], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    scenarios: Dict[str, Dict[str, ScenarioResult]] = {}
    for r in results:
        scenarios.setdefault(r.scenario, {})[r.protocol] = r
    cmp = {k: v for k, v in scenarios.items() if len(v) > 1}
    if not cmp:
        print("No multi-protocol comparison data found")
        return
    _warn_missing_protocol_entries(cmp, "protocol comparison")

    x = np.arange(len(cmp))
    width = 0.2

    for metric, ylabel, title, getter in [
        (
            "throughput",
            "Throughput (Mbps)",
            "Protocol Throughput Comparison",
            lambda r: r.total_throughput_mbps,
        ),
        (
            "delay",
            "Average Delay (ms)",
            "Protocol Delay Comparison",
            lambda r: r.avg_delay_ms,
        ),
        (
            "loss",
            "Packet Loss Rate (%)",
            "Protocol Packet Loss Comparison",
            lambda r: r.total_loss_rate,
        ),
    ]:
        fig, ax = plt.subplots(figsize=(14, 6))
        for i, proto in enumerate(PROTOCOL_ORDER):
            vals = [getter(cmp[s][proto]) if proto in cmp[s] else np.nan for s in cmp]
            x_pos = x + i * width
            _plot_sparse_bars(
                ax, x_pos, vals, width, label=proto, color=PROTOCOL_COLORS_BAR[i]
            )
            for xpos, val in zip(x_pos, vals):
                if np.isnan(val):
                    _annotate_missing(ax, xpos)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(list(cmp.keys()), rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{metric}_comparison.png"), dpi=150)
        plt.close()

    print(f"Protocol comparison charts saved to: {output_dir}")


def plot_swift_scenarios(results: List[ScenarioResult], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    scenario_order = {scenario[0]: index for index, scenario in enumerate(SCENARIOS)}
    swift = sorted(
        [r for r in results if r.protocol == "TcpSwift"],
        key=lambda r: (scenario_order.get(r.scenario, len(scenario_order)), r.scenario),
    )
    if not swift:
        print("No TcpSwift data found")
        return

    old_combined_chart = os.path.join(output_dir, "swift_scenarios.png")
    if os.path.exists(old_combined_chart):
        os.remove(old_combined_chart)

    for stale_part in glob.glob(os.path.join(output_dir, "swift_scenarios_part*.png")):
        os.remove(stale_part)

    target_parts = 3
    base_size, remainder = divmod(len(swift), target_parts)
    chunks: List[List[ScenarioResult]] = []
    start_index = 0
    for part_index in range(target_parts):
        chunk_size = base_size + (1 if part_index < remainder else 0)
        if chunk_size <= 0:
            continue
        chunks.append(swift[start_index : start_index + chunk_size])
        start_index += chunk_size

    all_names = [r.scenario for r in swift]
    all_colors = plt.get_cmap("viridis")(np.linspace(0.2, 0.8, len(all_names)))
    scenario_colors = dict(zip(all_names, all_colors))
    outputs = []

    metrics = [
        (
            "throughput",
            "Throughput (Mbps)",
            "TcpSwift Throughput by Scenario",
            lambda r: r.total_throughput_mbps,
        ),
        (
            "delay",
            "Average Delay (ms)",
            "TcpSwift Delay by Scenario",
            lambda r: r.avg_delay_ms,
        ),
        (
            "jitter",
            "Average Jitter (ms)",
            "TcpSwift Jitter by Scenario",
            lambda r: r.avg_jitter_ms,
        ),
    ]

    for part_index, chunk in enumerate(chunks, start=1):
        names = [r.scenario for r in chunk]
        colors = [scenario_colors[name] for name in names]
        figure_height = max(9, len(chunk) * 0.55 + 4)
        fig, axes = plt.subplots(3, 1, figsize=(14, figure_height))
        fig.suptitle(
            f"TcpSwift Scenario Metrics (Part {part_index}/{len(chunks)})",
            fontsize=14,
            fontweight="bold",
        )

        for ax, (_, xlabel, title, getter) in zip(axes, metrics):
            vals = [getter(r) for r in chunk]
            ax.barh(names, vals, color=colors)
            ax.invert_yaxis()
            ax.set_xlabel(xlabel)
            ax.set_title(title)
            ax.grid(axis="x", alpha=0.3)

            fmt = ".1f" if "Throughput" in xlabel else ".4f"
            max_value = max(vals) if vals else 1
            if max_value <= 0:
                max_value = 1
            ax.set_xlim(0, max_value * 1.15)
            for row_index, value in enumerate(vals):
                ax.text(
                    value + max_value * 0.01,
                    row_index,
                    f"{value:{fmt}}",
                    va="center",
                    fontsize=8,
                )

        plt.tight_layout(rect=(0, 0, 1, 0.96))
        output_path = os.path.join(output_dir, f"swift_scenarios_part{part_index}.png")
        plt.savefig(output_path, dpi=180)
        plt.close()
        outputs.append(output_path)
        print(f"Swift scenario chart page saved to: {output_path}")

    print(
        "Swift scenario chart pages saved to: "
        + ", ".join(os.path.basename(path) for path in outputs)
    )


def plot_radar_chart(results: List[ScenarioResult], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    scenario_map: Dict[str, Dict[str, ScenarioResult]] = {}
    for r in results:
        scenario_map.setdefault(r.scenario, {})[r.protocol] = r

    available_protocols = sorted({r.protocol for r in results})
    if len(available_protocols) < 2:
        print("At least 2 protocols required for radar chart")
        return

    common_scenarios = [
        s
        for s, protocol_map in sorted(scenario_map.items())
        if all(p in protocol_map for p in available_protocols)
    ]
    if not common_scenarios:
        print("Warning: No common scenarios across all protocols for radar chart")
        return
    excluded = sorted(set(scenario_map.keys()) - set(common_scenarios))
    if excluded:
        print(
            "Warning: Radar chart excluded non-intersection scenarios -> "
            f"{_format_missing_list(excluded)}"
        )

    metrics = ["Throughput", "Low Delay", "Low Jitter", "Low Loss"]
    protos = available_protocols

    raw = {}
    for p in protos:
        pdata = {"throughput": [], "delay": [], "jitter": [], "loss": []}
        for scenario in common_scenarios:
            r = scenario_map[scenario][p]
            pdata["throughput"].append(r.total_throughput_mbps)
            pdata["delay"].append(r.avg_delay_ms)
            pdata["jitter"].append(r.avg_jitter_ms)
            pdata["loss"].append(r.total_loss_rate)
        raw[p] = [
            float(np.mean(pdata["throughput"])),
            1 / (float(np.mean(pdata["delay"])) + 0.001),
            1 / (float(np.mean(pdata["jitter"])) + 0.001),
            100 - float(np.mean(pdata["loss"])),
        ]

    all_v = np.array([raw[p] for p in protos])
    mx, mn = np.max(all_v, axis=0), np.min(all_v, axis=0)
    rng = mx - mn + 1e-10
    norm = {p: [(v - mn[i]) / rng[i] for i, v in enumerate(raw[p])] for p in protos}

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for p in protos:
        v = norm[p] + norm[p][:1]
        c = PROTOCOL_COLORS_MAP.get(p, "#333333")
        ax.plot(angles, v, "o-", linewidth=2, label=p, color=c)
        ax.fill(angles, v, alpha=0.25, color=c)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))
    ax.set_title("Protocol Performance Radar Chart", y=1.08)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "radar_comparison.png"), dpi=150)
    plt.close()
    print(f"Radar chart saved to: {output_dir}")


def generate_summary_table(results: List[ScenarioResult], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    if not results:
        return
    rows = [
        {
            "Scenario": r.scenario,
            "Protocol": r.protocol,
            "Throughput (Mbps)": f"{r.total_throughput_mbps:.2f}",
            "Delay (ms)": f"{r.avg_delay_ms:.4f}",
            "Jitter (ms)": f"{r.avg_jitter_ms:.4f}",
            "Loss (%)": f"{r.total_loss_rate:.2f}",
        }
        for r in results
    ]
    csv_path = os.path.join(output_dir, "summary.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Summary table saved to: {csv_path}")


def plot_flow_throughput_comparison(log_dir: str, output_dir: str):
    flowmonitor_files = glob.glob(os.path.join(log_dir, "*.flowmonitor"))
    if not flowmonitor_files:
        print(f"No flowmonitor files found in: {log_dir}")
        return

    data: Dict[str, Dict[str, Dict[int, float]]] = {}
    samples: Dict[str, Dict[str, Dict[int, List[float]]]] = {}
    for fp in flowmonitor_files:
        name = os.path.basename(fp).replace(".flowmonitor", "")
        parsed = parse_run_name(name)
        if not parsed:
            continue
        scenario, proto, _seed = parsed
        flows = parse_flowmonitor(fp)
        proto_samples = samples.setdefault(scenario, {}).setdefault(proto, {})
        for flow in flows:
            if flow.protocol == 6 and flow.flow_id in {1, 3, 5}:
                proto_samples.setdefault(flow.flow_id, []).append(flow.throughput_mbps)
    for scenario, proto_map in samples.items():
        for proto, flow_samples in proto_map.items():
            data.setdefault(scenario, {})[proto] = {
                fid: float(np.mean(vals)) for fid, vals in flow_samples.items()
            }

    scenarios = sorted(data.keys())
    protos = ["TcpNewReno", "TcpCubic", "TcpBbr", "TcpSwift"]
    avail = set()
    for s in scenarios:
        avail.update(data[s].keys())
    protos = [p for p in protos if p in avail]
    flows = [1, 3, 5]

    if not scenarios or not protos:
        print("No valid throughput data found for plotting")
        return
    _warn_missing_flow_entries(data, protos, flows)

    x = np.arange(len(protos))
    os.makedirs(output_dir, exist_ok=True)
    scenarios_per_page = 4
    total_pages = (len(scenarios) + scenarios_per_page - 1) // scenarios_per_page
    outputs = []

    for page_idx in range(total_pages):
        page_scenarios = scenarios[
            page_idx * scenarios_per_page : (page_idx + 1) * scenarios_per_page
        ]
        fig, axes = plt.subplots(
            len(page_scenarios),
            len(flows),
            figsize=(13, 3.4 * len(page_scenarios) + 1.4),
        )
        fig.suptitle(
            f"TCP Flow Throughput Comparison (Page {page_idx + 1}/{total_pages})",
            fontsize=14,
            fontweight="bold",
        )

        if len(page_scenarios) == 1:
            axes = np.array([axes])

        for i, sc in enumerate(page_scenarios):
            for j, fid in enumerate(flows):
                ax = axes[i, j]
                tps = [
                    data[sc][p][fid] if p in data[sc] and fid in data[sc][p] else np.nan
                    for p in protos
                ]
                bars = []
                for xpos, proto, val in zip(x, protos, tps):
                    if np.isnan(val):
                        _annotate_missing(ax, float(xpos))
                        continue
                    bar_container = ax.bar(
                        xpos,
                        val,
                        0.6,
                        color=FLOW_COLORS[proto],
                        edgecolor="black",
                        linewidth=0.5,
                    )
                    bars.extend(bar_container)
                for bar, val in zip(bars, [v for v in tps if not np.isnan(v)]):
                    if val > 0:
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 5,
                            f"{val:.1f}",
                            ha="center",
                            va="bottom",
                            fontsize=8,
                        )
                ax.set_xticks(x)
                ax.set_xticklabels([p.replace("Tcp", "") for p in protos], fontsize=9)
                ax.set_ylabel("Throughput (Mbps)", fontsize=9)
                if i == 0:
                    ax.set_title(f"Flow {fid}", fontsize=11, fontweight="bold")
                if j == 0:
                    ax.annotate(
                        sc.replace("_", " ").title(),
                        xy=(-0.32, 0.5),
                        xycoords="axes fraction",
                        fontsize=10,
                        fontweight="bold",
                        rotation=90,
                        va="center",
                        ha="center",
                    )
                ax.grid(axis="y", linestyle="--", alpha=0.3)
                valid_tps = [float(v) for v in tps if not np.isnan(v)]
                ax.set_ylim(0, max(valid_tps) * 1.2 if valid_tps else 100)

        fig.subplots_adjust(
            left=0.14,
            right=0.98,
            bottom=0.08,
            top=0.90,
            wspace=0.28,
            hspace=0.42,
        )
        out = os.path.join(
            output_dir, f"flow_throughput_comparison_part{page_idx + 1}.png"
        )
        plt.savefig(out, dpi=200)
        plt.close()
        outputs.append(out)
        print(f"Flow throughput comparison page saved to: {out}")

    if outputs:
        print(
            "Flow throughput comparison pages saved to: "
            + ", ".join(os.path.basename(p) for p in outputs)
        )


def cmd_draw(args):
    """Generate plots."""
    datasets = [
        ("./logs/comparison", "./logs/plots"),
        ("./logs/comparison-udp", "./logs/plots-udp"),
    ]
    if args.comparison_dir:
        out = args.output_dir or (
            "./logs/plots-udp"
            if "udp" in args.comparison_dir.lower()
            else "./logs/plots"
        )
        datasets = [(args.comparison_dir, out)]

    print("=" * 60)
    print("NS-3 FlowMonitor Data Visualization")
    print("=" * 60)

    ok = 0
    for cdir, odir in datasets:
        if not os.path.isdir(cdir):
            print(f"Warning: Directory not found: {cdir}")
            continue
        results = aggregate_results(load_all_results(cdir))
        print(f"\n--- Processing: {cdir} -> {odir} ---")
        print(f"Loaded {len(results)} (scenario, protocol) results from {cdir}")
        if not results:
            print(f"Warning: No flowmonitor files found in {cdir}")
            continue
        plot_swift_scenarios(results, odir)
        plot_protocol_comparison(results, odir)
        plot_radar_chart(results, odir)
        generate_summary_table(results, odir)
        plot_flow_throughput_comparison(cdir, odir)
        ok += 1

    print(f"\nAll charts generated! ({ok}/{len(datasets)} datasets processed)")


# =============================================================================
# CLI Entry Point
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="NS-3 Swift TCP Simulation Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Usage examples:
  python main.py sim                        # Run all pure TCP simulations
  python main.py sim --udp                  # Run all TCP+UDP simulations
  python main.py sim --scenario wifi_ac     # Run only the wifi_ac scenario
  python main.py sim --num-seeds 10         # 10 RngRun repetitions per config
  python main.py draw                       # Generate all plots
  python main.py draw --comparison-dir ./logs/comparison
  python main.py summary                    # Generate summary CSV (TCP + UDP)
""",
    )
    sub = parser.add_subparsers(dest="command", help="subcommand")

    # --- sim ---
    p_sim = sub.add_parser("sim", help="Run simulations")
    p_sim.add_argument(
        "--udp", action="store_true", help="Enable UDP burst interference"
    )
    p_sim.add_argument(
        "--scenario", nargs="+", help="Run only specified scenarios (space-separated)"
    )
    p_sim.add_argument(
        "--protocols",
        nargs="+",
        default=None,
        help="Protocol list (default: TcpSwift TcpNewReno TcpCubic TcpBbr)",
    )
    p_sim.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help="Simulation duration (seconds)",
    )
    p_sim.add_argument(
        "--n-leaf",
        type=int,
        default=DEFAULT_N_LEAF,
        help="Number of leaf nodes per side",
    )
    p_sim.add_argument(
        "--sim-seed", type=int, default=DEFAULT_SIM_SEED, help="Base random seed"
    )
    p_sim.add_argument(
        "--num-seeds",
        type=int,
        default=1,
        help="Number of RngRun repetitions per scenario/protocol "
        "(seeds sim-seed .. sim-seed+N-1)",
    )

    # --- draw ---
    p_draw = sub.add_parser("draw", help="Generate plots")
    p_draw.add_argument(
        "--comparison-dir", default=None, help="Specify a single data directory"
    )
    p_draw.add_argument("--output-dir", default=None, help="Specify output directory")

    # --- summary ---
    sub.add_parser(
        "summary", help="Generate summary CSV report (includes both TCP and UDP)"
    )

    args = parser.parse_args()

    if args.command == "sim":
        cmd_sim(args)
    elif args.command == "draw":
        cmd_draw(args)
    elif args.command == "summary":
        cmd_summary(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
