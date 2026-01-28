#!/usr/bin/env python3
"""
NS-3 FlowMonitor Data Visualization Script
Parse .flowmonitor XML files and generate charts
"""

import argparse
import os
import re
import glob
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


@dataclass
class FlowData:
    """Single flow data"""

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
        """Calculate throughput (Mbps)"""
        if self.duration_ns > 0:
            return (self.rx_bytes * 8) / (self.duration_ns / 1e9) / 1e6
        return 0.0

    @property
    def avg_delay_ms(self) -> float:
        """Calculate average delay (ms)"""
        if self.rx_packets > 0:
            return (self.delay_sum_ns / self.rx_packets) / 1e6
        return 0.0

    @property
    def avg_jitter_ms(self) -> float:
        """Calculate average jitter (ms)"""
        if self.rx_packets > 1:
            return (self.jitter_sum_ns / (self.rx_packets - 1)) / 1e6
        return 0.0

    @property
    def loss_rate(self) -> float:
        """Calculate packet loss rate (%)"""
        if self.tx_packets > 0:
            return (self.lost_packets / self.tx_packets) * 100
        return 0.0


@dataclass
class ScenarioResult:
    """Scenario test result"""

    scenario: str
    protocol: str
    flows: List[FlowData]

    @property
    def total_throughput_mbps(self) -> float:
        """Total throughput"""
        return sum(f.throughput_mbps for f in self.flows if f.protocol == 6)  # TCP only

    @property
    def avg_delay_ms(self) -> float:
        """Average delay"""
        tcp_flows = [f for f in self.flows if f.protocol == 6 and f.rx_packets > 0]
        if tcp_flows:
            return np.mean([f.avg_delay_ms for f in tcp_flows])
        return 0.0

    @property
    def avg_jitter_ms(self) -> float:
        """Average jitter"""
        tcp_flows = [f for f in self.flows if f.protocol == 6 and f.rx_packets > 1]
        if tcp_flows:
            return np.mean([f.avg_jitter_ms for f in tcp_flows])
        return 0.0

    @property
    def total_loss_rate(self) -> float:
        """Total packet loss rate"""
        tcp_flows = [f for f in self.flows if f.protocol == 6]
        total_tx = sum(f.tx_packets for f in tcp_flows)
        total_lost = sum(f.lost_packets for f in tcp_flows)
        if total_tx > 0:
            return (total_lost / total_tx) * 100
        return 0.0


def parse_ns_time(time_str: str) -> float:
    """Parse ns-3 time string (e.g. '+1.5e+09ns') to nanoseconds"""
    if not time_str:
        return 0.0
    # Remove '+' prefix and 'ns' suffix
    time_str = time_str.strip("+").replace("ns", "")
    try:
        return float(time_str)
    except ValueError:
        return 0.0


def parse_flowmonitor(filepath: str) -> List[FlowData]:
    """Parse flowmonitor XML file"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Parse flow classifier to get IP info
    flow_info = {}
    for classifier in root.findall(".//Ipv4FlowClassifier/Flow"):
        flow_id = int(classifier.get("flowId"))
        flow_info[flow_id] = {
            "src_addr": classifier.get("sourceAddress"),
            "dst_addr": classifier.get("destinationAddress"),
            "protocol": int(classifier.get("protocol")),
        }

    # Parse flow stats
    flows = []
    for flow in root.findall(".//FlowStats/Flow"):
        flow_id = int(flow.get("flowId"))
        info = flow_info.get(flow_id, {"src_addr": "", "dst_addr": "", "protocol": 0})

        first_tx = parse_ns_time(flow.get("timeFirstTxPacket"))
        last_rx = parse_ns_time(flow.get("timeLastRxPacket"))
        duration = last_rx - first_tx if last_rx > first_tx else 0

        flows.append(
            FlowData(
                flow_id=flow_id,
                src_addr=info["src_addr"],
                dst_addr=info["dst_addr"],
                protocol=info["protocol"],
                tx_bytes=int(flow.get("txBytes", 0)),
                rx_bytes=int(flow.get("rxBytes", 0)),
                tx_packets=int(flow.get("txPackets", 0)),
                rx_packets=int(flow.get("rxPackets", 0)),
                lost_packets=int(flow.get("lostPackets", 0)),
                delay_sum_ns=parse_ns_time(flow.get("delaySum")),
                jitter_sum_ns=parse_ns_time(flow.get("jitterSum")),
                duration_ns=duration,
            )
        )

    return flows


def load_all_results(logs_dir: str = "./logs") -> List[ScenarioResult]:
    """Load all flowmonitor files"""
    results = []
    pattern = os.path.join(logs_dir, "**", "*.flowmonitor")

    for filepath in glob.glob(pattern, recursive=True):
        filename = os.path.basename(filepath)
        # Parse filename: scenario_protocol.flowmonitor
        match = re.match(r"(.+)_(Tcp\w+)\.flowmonitor", filename)
        if match:
            scenario = match.group(1)
            protocol = match.group(2)
            flows = parse_flowmonitor(filepath)
            results.append(ScenarioResult(scenario, protocol, flows))

    return results


def plot_protocol_comparison(
    results: List[ScenarioResult], output_dir: str = "./logs/plots"
):
    """Plot protocol comparison charts"""
    os.makedirs(output_dir, exist_ok=True)

    # Group by scenario
    scenarios = {}
    for r in results:
        if r.scenario not in scenarios:
            scenarios[r.scenario] = {}
        scenarios[r.scenario][r.protocol] = r

    # Select scenarios with multiple protocols for comparison
    comparison_scenarios = {k: v for k, v in scenarios.items() if len(v) > 1}

    if not comparison_scenarios:
        print("No multi-protocol comparison data found")
        return

    # 1. Throughput comparison
    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(comparison_scenarios))
    width = 0.2
    protocols = ["TcpGemini", "TcpNewReno", "TcpCubic", "TcpBbr"]
    colors = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6"]

    for i, protocol in enumerate(protocols):
        throughputs = []
        for scenario in comparison_scenarios:
            if protocol in comparison_scenarios[scenario]:
                throughputs.append(
                    comparison_scenarios[scenario][protocol].total_throughput_mbps
                )
            else:
                throughputs.append(0)
        ax.bar(x + i * width, throughputs, width, label=protocol, color=colors[i])

    ax.set_ylabel("Throughput (Mbps)")
    ax.set_title("Protocol Throughput Comparison")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(list(comparison_scenarios.keys()), rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "throughput_comparison.png"), dpi=150)
    plt.close()

    # 2. Delay comparison
    fig, ax = plt.subplots(figsize=(14, 6))
    for i, protocol in enumerate(protocols):
        delays = []
        for scenario in comparison_scenarios:
            if protocol in comparison_scenarios[scenario]:
                delays.append(comparison_scenarios[scenario][protocol].avg_delay_ms)
            else:
                delays.append(0)
        ax.bar(x + i * width, delays, width, label=protocol, color=colors[i])

    ax.set_ylabel("Average Delay (ms)")
    ax.set_title("Protocol Delay Comparison")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(list(comparison_scenarios.keys()), rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "delay_comparison.png"), dpi=150)
    plt.close()

    # 3. Packet loss comparison
    fig, ax = plt.subplots(figsize=(14, 6))
    for i, protocol in enumerate(protocols):
        loss_rates = []
        for scenario in comparison_scenarios:
            if protocol in comparison_scenarios[scenario]:
                loss_rates.append(
                    comparison_scenarios[scenario][protocol].total_loss_rate
                )
            else:
                loss_rates.append(0)
        ax.bar(x + i * width, loss_rates, width, label=protocol, color=colors[i])

    ax.set_ylabel("Packet Loss Rate (%)")
    ax.set_title("Protocol Packet Loss Comparison")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(list(comparison_scenarios.keys()), rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "loss_comparison.png"), dpi=150)
    plt.close()

    print(f"Protocol comparison charts saved to: {output_dir}")


def plot_gemini_scenarios(
    results: List[ScenarioResult], output_dir: str = "./logs/plots"
):
    """Plot Gemini performance across scenarios"""
    os.makedirs(output_dir, exist_ok=True)

    gemini_results = [r for r in results if r.protocol == "TcpGemini"]
    if not gemini_results:
        print("No TcpGemini data found")
        return

    # Sort by scenario
    gemini_results.sort(key=lambda x: x.scenario)

    scenarios = [r.scenario for r in gemini_results]
    throughputs = [r.total_throughput_mbps for r in gemini_results]
    delays = [r.avg_delay_ms for r in gemini_results]
    jitters = [r.avg_jitter_ms for r in gemini_results]

    # Combined performance chart
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    # Throughput
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(scenarios)))
    axes[0].barh(scenarios, throughputs, color=colors)
    axes[0].set_xlabel("Throughput (Mbps)")
    axes[0].set_title("TcpGemini Throughput by Scenario")
    axes[0].grid(axis="x", alpha=0.3)
    for i, v in enumerate(throughputs):
        axes[0].text(
            v + max(throughputs) * 0.01, i, f"{v:.1f}", va="center", fontsize=8
        )

    # Delay
    axes[1].barh(scenarios, delays, color=colors)
    axes[1].set_xlabel("Average Delay (ms)")
    axes[1].set_title("TcpGemini Delay by Scenario")
    axes[1].grid(axis="x", alpha=0.3)
    for i, v in enumerate(delays):
        axes[1].text(v + max(delays) * 0.01, i, f"{v:.4f}", va="center", fontsize=8)

    # Jitter
    axes[2].barh(scenarios, jitters, color=colors)
    axes[2].set_xlabel("Average Jitter (ms)")
    axes[2].set_title("TcpGemini Jitter by Scenario")
    axes[2].grid(axis="x", alpha=0.3)
    for i, v in enumerate(jitters):
        axes[2].text(
            v + max(jitters) * 0.01 if max(jitters) > 0 else 0.001,
            i,
            f"{v:.4f}",
            va="center",
            fontsize=8,
        )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gemini_scenarios.png"), dpi=150)
    plt.close()

    print(f"Gemini scenario charts saved to: {output_dir}")


def plot_radar_chart(results: List[ScenarioResult], output_dir: str = "./logs/plots"):
    """Plot protocol performance radar chart"""
    os.makedirs(output_dir, exist_ok=True)

    # Aggregate data by protocol
    protocol_data = {}
    for r in results:
        if r.protocol not in protocol_data:
            protocol_data[r.protocol] = {
                "throughput": [],
                "delay": [],
                "jitter": [],
                "loss": [],
            }
        protocol_data[r.protocol]["throughput"].append(r.total_throughput_mbps)
        protocol_data[r.protocol]["delay"].append(r.avg_delay_ms)
        protocol_data[r.protocol]["jitter"].append(r.avg_jitter_ms)
        protocol_data[r.protocol]["loss"].append(r.total_loss_rate)

    if len(protocol_data) < 2:
        print("At least 2 protocols required for radar chart")
        return

    # Calculate averages and normalize
    metrics = ["Throughput", "Low Delay", "Low Jitter", "Low Loss"]
    protocols = list(protocol_data.keys())
    colors = {
        "TcpGemini": "#2ecc71",
        "TcpNewReno": "#3498db",
        "TcpCubic": "#e74c3c",
        "TcpBbr": "#9b59b6",
    }

    # Normalize data (higher is better)
    raw_data = {}
    for p in protocols:
        raw_data[p] = [
            np.mean(protocol_data[p]["throughput"]),
            1 / (np.mean(protocol_data[p]["delay"]) + 0.001),  # Lower delay is better
            1 / (np.mean(protocol_data[p]["jitter"]) + 0.001),  # Lower jitter is better
            100 - np.mean(protocol_data[p]["loss"]),  # Lower loss is better
        ]

    # Normalize to 0-1
    all_values = [raw_data[p] for p in protocols]
    max_vals = np.max(all_values, axis=0)
    min_vals = np.min(all_values, axis=0)
    range_vals = max_vals - min_vals + 1e-10

    normalized = {}
    for p in protocols:
        normalized[p] = [
            (v - min_vals[i]) / range_vals[i] for i, v in enumerate(raw_data[p])
        ]

    # Draw radar chart
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for protocol in protocols:
        values = normalized[protocol] + normalized[protocol][:1]
        color = colors.get(protocol, "#333333")
        ax.plot(angles, values, "o-", linewidth=2, label=protocol, color=color)
        ax.fill(angles, values, alpha=0.25, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))
    ax.set_title("Protocol Performance Radar Chart", y=1.08)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "radar_comparison.png"), dpi=150)
    plt.close()

    print(f"Radar chart saved to: {output_dir}")


def generate_summary_table(
    results: List[ScenarioResult], output_dir: str = "./logs/plots"
):
    """Generate summary table"""
    os.makedirs(output_dir, exist_ok=True)

    # Create summary data
    summary = []
    for r in results:
        summary.append(
            {
                "Scenario": r.scenario,
                "Protocol": r.protocol,
                "Throughput (Mbps)": f"{r.total_throughput_mbps:.2f}",
                "Delay (ms)": f"{r.avg_delay_ms:.4f}",
                "Jitter (ms)": f"{r.avg_jitter_ms:.4f}",
                "Loss (%)": f"{r.total_loss_rate:.2f}",
            }
        )

    # Save as CSV
    import csv

    csv_path = os.path.join(output_dir, "summary.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)

    print(f"Summary table saved to: {csv_path}")


def plot_flow_throughput_comparison(log_dir: str, output_dir: str):
    """Plot flow throughput comparison from ns3.log files"""
    log_files = glob.glob(os.path.join(log_dir, "*_ns3.log"))
    if not log_files:
        print(f"No ns3.log files found in: {log_dir}")
        return

    data: Dict[str, Dict[str, Dict[int, float]]] = {}

    for log_file in log_files:
        basename = os.path.basename(log_file)
        name = basename.replace("_ns3.log", "")
        match = re.match(r"(.+)_(Tcp\w+)$", name)
        if not match:
            continue
        scenario, protocol = match.group(1), match.group(2)

        with open(log_file, "r") as f:
            content = f.read()

        pattern = r"TCP Flow (\d+).*?Throughput:\s+([\d.]+)\s+Mbps"
        matches = re.findall(pattern, content, re.DOTALL)
        throughputs = {int(flow_id): float(tp) for flow_id, tp in matches}

        data.setdefault(scenario, {})[protocol] = throughputs

    scenarios = sorted(data.keys())
    protocols = ["TcpNewReno", "TcpCubic", "TcpBbr", "TcpGemini"]
    flows = [1, 3, 5]

    available_protocols = set()
    for scenario in scenarios:
        available_protocols.update(data[scenario].keys())
    protocols = [p for p in protocols if p in available_protocols]

    if not scenarios or not protocols:
        print("No valid throughput data found for plotting")
        return

    colors = {
        "TcpNewReno": "#1f77b4",
        "TcpCubic": "#ff7f0e",
        "TcpBbr": "#2ca02c",
        "TcpGemini": "#d62728",
    }

    fig, axes = plt.subplots(
        len(scenarios), len(flows), figsize=(14, 4 * len(scenarios))
    )
    fig.suptitle(
        "TCP Flow Throughput Comparison (Flow 1, 3, 5)", fontsize=14, fontweight="bold"
    )

    if len(scenarios) == 1:
        axes = axes.reshape(1, -1)

    x = np.arange(len(protocols))
    bar_width = 0.6

    for i, scenario in enumerate(scenarios):
        for j, flow_id in enumerate(flows):
            ax = axes[i, j]
            throughputs = [
                data[scenario].get(protocol, {}).get(flow_id, 0)
                for protocol in protocols
            ]

            bars = ax.bar(
                x,
                throughputs,
                bar_width,
                color=[colors[p] for p in protocols],
                edgecolor="black",
                linewidth=0.5,
            )

            for bar, val in zip(bars, throughputs):
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
            ax.set_xticklabels([p.replace("Tcp", "") for p in protocols], fontsize=9)
            ax.set_ylabel("Throughput (Mbps)", fontsize=9)

            if i == 0:
                ax.set_title(f"Flow {flow_id}", fontsize=11, fontweight="bold")

            if j == 0:
                ax.annotate(
                    scenario.replace("_", " ").title(),
                    xy=(-0.4, 0.5),
                    xycoords="axes fraction",
                    fontsize=10,
                    fontweight="bold",
                    rotation=90,
                    va="center",
                    ha="center",
                )

            ax.grid(axis="y", linestyle="--", alpha=0.3)
            ax.set_ylim(0, max(throughputs) * 1.2 if max(throughputs) > 0 else 100)

    plt.tight_layout(rect=[0.05, 0, 1, 0.96])
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "flow_throughput_comparison.png")
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Flow throughput comparison saved to: {output_file}")


def process_single_dataset(comparison_dir: str, output_dir: str):
    """Process a single dataset (comparison directory) and generate plots"""
    print(f"\n--- Processing: {comparison_dir} -> {output_dir} ---")

    results = load_all_results(comparison_dir)
    print(f"Loaded {len(results)} test results from {comparison_dir}")

    if not results:
        print(f"Warning: No flowmonitor files found in {comparison_dir}")
        return False

    plot_gemini_scenarios(results, output_dir)
    plot_protocol_comparison(results, output_dir)
    plot_radar_chart(results, output_dir)
    generate_summary_table(results, output_dir)
    plot_flow_throughput_comparison(comparison_dir, output_dir)

    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="NS-3 FlowMonitor Data Visualization")
    parser.add_argument(
        "--comparison-dir",
        default=None,
        help="Single comparison directory (if specified, only process this one)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for plots (used with --comparison-dir)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("NS-3 FlowMonitor Data Visualization")
    print("=" * 60)

    # 定义要处理的数据集：(comparison_dir, output_dir)
    datasets = [
        ("./logs/comparison", "./logs/plots"),
        ("./logs/comparison-udp", "./logs/plots-udp"),
    ]

    # 如果指定了单个目录，只处理该目录
    if args.comparison_dir:
        output_dir = args.output_dir or (
            "./logs/plots-udp"
            if "udp" in args.comparison_dir.lower()
            else "./logs/plots"
        )
        datasets = [(args.comparison_dir, output_dir)]

    success_count = 0
    for comparison_dir, output_dir in datasets:
        if os.path.isdir(comparison_dir):
            if process_single_dataset(comparison_dir, output_dir):
                success_count += 1
        else:
            print(f"Warning: Directory not found: {comparison_dir}")

    print("\n" + "=" * 60)
    print(f"All charts generated! ({success_count}/{len(datasets)} datasets processed)")
    print("=" * 60)


if __name__ == "__main__":
    main()
