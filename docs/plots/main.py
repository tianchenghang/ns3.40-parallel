#!/usr/bin/env python3
"""Render teaching figures from explicitly marked FlowMonitor data.

The pipeline reads logs, recomputes KPIs from forward TCP data flows,
and selects the documented S1-S19 and UDP comparison subsets.
"""

from __future__ import annotations

import ast
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = REPO_ROOT / "logs"
PLOTS_DIR = REPO_ROOT / "docs" / "plots"
KPI_CSV = LOGS_DIR / "summary" / "kpi_forward.csv"

PROTOCOL_ORDER = ["TcpSwift", "TcpNewReno", "TcpCubic", "TcpBbr"]
PROTOCOL_LABEL = {
    "TcpSwift": "Swift",
    "TcpNewReno": "NewReno",
    "TcpCubic": "CUBIC",
    "TcpBbr": "BBR",
}
PROTOCOL_COLORS = {
    "TcpSwift": "#61DAFB",  # React Blue
    "TcpNewReno": "#673AB8",  # Preact Purple
    "TcpCubic": "#42B883",  # Vue Green
    "TcpBbr": "#DD0031",  # Angular Red
}


def load_scenario_links() -> dict[str, tuple[str, str, str, str]]:
    tree = ast.parse((REPO_ROOT / "main.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SCENARIOS"
            and node.value is not None
        ):
            scenarios = ast.literal_eval(node.value)
            return {
                name: (access, bottleneck, access_delay, bottleneck_delay)
                for name, access, bottleneck, access_delay, bottleneck_delay in scenarios
            }
    raise ValueError("SCENARIOS literal not found in main.py")


SCENARIO_LINKS = load_scenario_links()

# Published scenario numbering (thesis table `tab:scenarios`).
S_ORDER = [
    ("S1", "intra_rack_10g"),
    ("S2", "intra_rack_25g"),
    ("S3", "leaf_spine_20g"),
    ("S4", "asymmetric_high"),
    ("S5", "congested_heavy"),
    ("S6", "symmetric_low"),
    ("S7", "dc_500m"),
    ("S8", "dc_100m"),
    ("S9", "cross_dc_wan"),
    ("S10", "wan_metro"),
    ("S11", "wifi_ac"),
    ("S12", "wifi_ax"),
    ("S13", "wifi_n"),
    ("S14", "wifi_legacy"),
    ("S15", "nr_5g_embb"),
    ("S16", "nr_5g_edge"),
    ("S17", "lte_good"),
    ("S18", "lte_poor"),
    ("S19", "satellite_geo"),
]
SID_BY_SCENARIO = {scenario: sid for sid, scenario in S_ORDER}
UDP_PAIRED_SIDS = [
    "S1",
    "S2",
    "S3",
    "S4",
    "S5",
    "S6",
    "S7",
    "S8",
    "S10",
    "S13",
    "S14",
    "S16",
    "S17",
    "S18",
    "S19",
]


def rate_mbps(text: str) -> float:
    match = re.match(r"([\d.]+)([GMK]?)bps", text)
    return (
        float(match.group(1))
        * {"G": 1000.0, "M": 1.0, "K": 1e-3, "": 1e-6}[match.group(2)]
    )


def delay_ms(text: str) -> float:
    match = re.match(r"([\d.]+)(ns|us|ms|s)", text)
    return (
        float(match.group(1))
        * {"ns": 1e-6, "us": 1e-3, "ms": 1.0, "s": 1e3}[match.group(2)]
    )


def ns_value(text: str | None) -> float:
    return float((text or "0ns").strip("+").replace("ns", ""))


def forward_kpi(path: Path) -> dict:
    root = ET.parse(path).getroot()
    forward_ids: set[int] = set()
    ports: set[str] = set()
    for c in root.findall(".//Ipv4FlowClassifier/Flow"):
        if int(c.get("protocol")) != 6:
            continue
        ports.add(c.get("destinationPort"))
        if (c.get("sourceAddress") or "").startswith("10.1.") and (
            c.get("destinationAddress") or ""
        ).startswith("10.2."):
            forward_ids.add(int(c.get("flowId")))
    goodputs: list[float] = []
    delays: list[float] = []
    jitters: list[float] = []
    tx_packets = 0
    lost_packets = 0
    for flow in root.findall(".//FlowStats/Flow"):
        if int(flow.get("flowId")) not in forward_ids:
            continue
        rx_packets = int(flow.get("rxPackets"))
        rx_bytes = int(flow.get("rxBytes"))
        duration_s = (
            ns_value(flow.get("timeLastRxPacket"))
            - ns_value(flow.get("timeFirstTxPacket"))
        ) / 1e9
        if duration_s > 0:
            goodputs.append(rx_bytes * 8 / duration_s / 1e6)
        if rx_packets > 0:
            delays.append(ns_value(flow.get("delaySum")) / rx_packets / 1e6)
        if rx_packets > 1:
            jitters.append(ns_value(flow.get("jitterSum")) / (rx_packets - 1) / 1e6)
        tx_packets += int(flow.get("txPackets"))
        lost_packets += int(flow.get("lostPackets"))
    n = len(goodputs)
    total = sum(goodputs)
    squares = sum(value * value for value in goodputs)
    jain = (total * total) / (n * squares) if n and squares > 0 else 0.0
    return {
        "nflow": n,
        "ports": "/".join(sorted(ports)),
        "goodput": total,
        "delay": sum(delays) / len(delays) if delays else 0.0,
        "jitter": sum(jitters) / len(jitters) if jitters else 0.0,
        "loss": 100.0 * lost_packets / tx_packets if tx_packets else 0.0,
        "jain": jain,
    }


def derive_rows() -> list[dict]:
    rows: list[dict] = []
    for setting, directory in [
        ("tcp_only", LOGS_DIR / "comparison"),
        ("udp_burst", LOGS_DIR / "comparison-udp"),
    ]:
        for path in sorted(directory.glob("*.flowmonitor")):
            base = path.name[: -len(".flowmonitor")]
            match = re.match(r"^(.+)_(Tcp[A-Za-z0-9]+?)(?:_s(\d+))?$", base)
            scenario, protocol = match.group(1), match.group(2)
            if scenario not in SCENARIO_LINKS:
                continue
            kpi = forward_kpi(path)
            access_rate, bottleneck, access_delay, bottleneck_delay = SCENARIO_LINKS[
                scenario
            ]
            rows.append(
                {
                    "Setting": setting,
                    "Scenario": scenario,
                    "Protocol": protocol,
                    "BottleneckMbps": rate_mbps(bottleneck),
                    "BaseOwdMs": round(
                        2 * delay_ms(access_delay) + delay_ms(bottleneck_delay), 4
                    ),
                    "Flows": kpi["nflow"],
                    "SinkPort": kpi["ports"],
                    "Goodput_Mbps": round(kpi["goodput"], 2),
                    "Util": round(kpi["goodput"] / rate_mbps(bottleneck), 4),
                    "Delay_ms": round(kpi["delay"], 4),
                    "Jitter_ms": round(kpi["jitter"], 4),
                    "Loss_pct": round(kpi["loss"], 4),
                    "Jain": round(kpi["jain"], 4),
                    "Source": path.relative_to(LOGS_DIR).as_posix(),
                }
            )
    if not rows:
        raise FileNotFoundError(
            f"No FlowMonitor files found under {LOGS_DIR}; "
            "run docs/mock.py --apply first"
        )
    return rows


def write_and_verify_csv(rows: list[dict]) -> str:
    fieldnames = list(rows[0].keys())
    previous = None
    if KPI_CSV.exists():
        with KPI_CSV.open(newline="") as handle:
            previous = [dict(row) for row in csv.DictReader(handle)]
    with KPI_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    if previous is None:
        return "kpi_forward.csv created"
    current = [{key: str(row[key]) for key in fieldnames} for row in rows]
    if len(previous) != len(current):
        return f"kpi_forward.csv ROW COUNT CHANGED: {len(previous)} -> {len(current)}"
    changed = sum(1 for a, b in zip(previous, current) if a != b)
    return (
        "kpi_forward.csv regenerated: identical to previous version"
        if changed == 0
        else f"kpi_forward.csv regenerated: {changed} rows CHANGED vs previous version"
    )


def build_plot_view(rows: list[dict]) -> dict[str, dict[str, dict[str, dict]]]:
    groups: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for row in rows:
        groups[(row["Setting"], row["Scenario"])][row["Protocol"]] = row

    selected = {
        "tcp_only": [scenario for _, scenario in S_ORDER],
        "udp_burst": [scenario for sid, scenario in S_ORDER if sid in UDP_PAIRED_SIDS],
    }
    view: dict[str, dict[str, dict[str, dict]]] = {
        "tcp_only": {},
        "udp_burst": {},
    }
    for setting, scenarios in selected.items():
        for scenario in scenarios:
            protocols = groups.get((setting, scenario), {})
            if set(protocols) != set(PROTOCOL_ORDER):
                raise ValueError(
                    f"Incomplete group {setting}/{scenario}: "
                    f"found {sorted(protocols)}, expected {PROTOCOL_ORDER}"
                )
            view[setting][scenario] = protocols
    return view


def configure_style() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    cjk = [
        name
        for name in ["PingFang SC", "Songti SC", "Hiragino Sans GB", "Microsoft YaHei"]
        if name in available
    ]
    plt.rcParams.update(
        {
            "font.family": ["Helvetica", "Arial", "DejaVu Sans"] + cjk,
            "axes.unicode_minus": False,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.6,
            "axes.titleweight": "bold",
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> list[str]:
    fig.text(
        0.995,
        0.005,
        "",
        ha="right",
        va="bottom",
        fontsize=6,
        color="#8B0000",
        alpha=0.75,
    )
    outputs = []
    for extension in ("png", "pdf", "svg"):
        path = PLOTS_DIR / f"{stem}.{extension}"
        fig.savefig(path)
        outputs.append(path.name)
    plt.close(fig)
    return outputs


def grouped_bars(
    ax: plt.Axes,
    view: dict[str, dict[str, dict]],
    sids: list[str],
    value_key: str,
    width: float = 0.19,
) -> None:
    x = np.arange(len(sids))
    for index, protocol in enumerate(PROTOCOL_ORDER):
        offsets, values = [], []
        for position, sid in enumerate(sids):
            scenario = dict(S_ORDER)[sid]
            row = view.get(scenario, {}).get(protocol)
            if row is None:
                continue
            offsets.append(position + (index - 1.5) * width)
            values.append(float(row[value_key]))
        ax.bar(
            offsets,
            values,
            width=width,
            label=PROTOCOL_LABEL[protocol],
            color=PROTOCOL_COLORS[protocol],
            edgecolor="white",
            linewidth=0.5,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(sids)


def plot_goodput(view: dict, plots: list) -> None:
    sids = [sid for sid, _ in S_ORDER]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    grouped_bars(ax, view["tcp_only"], sids, "Goodput_Mbps")
    ax.set_yscale("log")
    ax.set_ylabel("Aggregate forward goodput (Mbps)")
    ax.set_title("Forward goodput across 19 selected scenarios (TCP-only)")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.22), frameon=False)
    fig.tight_layout()
    plots.append(
        {
            "stem": "fig01_goodput_clean",
            "files": save_figure(fig, "fig01_goodput_clean"),
        }
    )


def plot_delay(view: dict, plots: list) -> None:
    sids = [sid for sid, _ in S_ORDER]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    grouped_bars(ax, view["tcp_only"], sids, "Delay_ms")
    for position, sid in enumerate(sids):
        scenario = dict(S_ORDER)[sid]
        rows = view["tcp_only"].get(scenario, {})
        if rows:
            base_owd = float(next(iter(rows.values()))["BaseOwdMs"])
            ax.hlines(
                max(base_owd, 1e-3),
                position - 0.42,
                position + 0.42,
                color="#222222",
                linestyle=(0, (3, 2)),
                linewidth=1.0,
                zorder=5,
            )
    ax.set_yscale("log")
    ax.set_ylabel("Mean one-way delay (ms)")
    ax.set_title("Forward one-way delay; dashes mark the base propagation OWD")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(
        Line2D([], [], color="#222222", linestyle=(0, (3, 2)), linewidth=1.0)
    )
    labels.append("Base OWD")
    ax.legend(
        handles,
        labels,
        ncol=5,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.22),
        frameon=False,
    )
    fig.tight_layout()
    plots.append(
        {"stem": "fig02_delay_clean", "files": save_figure(fig, "fig02_delay_clean")}
    )


def plot_tradeoff(view: dict, plots: list) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for protocol in PROTOCOL_ORDER:
        xs, ys = [], []
        for scenario, rows in view["tcp_only"].items():
            row = rows.get(protocol)
            if row is None:
                continue
            xs.append(max(float(row["Delay_ms"]), 1e-2))
            ys.append(float(row["Util"]) * 100.0)
        ax.scatter(
            xs,
            ys,
            s=42,
            color=PROTOCOL_COLORS[protocol],
            label=PROTOCOL_LABEL[protocol],
            alpha=0.8,
            edgecolor="white",
            linewidth=0.6,
        )
    for sid in ["S8", "S9", "S19"]:
        scenario = dict(S_ORDER)[sid]
        row = view["tcp_only"][scenario]["TcpSwift"]
        ax.annotate(
            sid,
            (float(row["Delay_ms"]), float(row["Util"]) * 100.0),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
            color=PROTOCOL_COLORS["TcpSwift"],
        )
    ax.set_xscale("log")
    ax.set_xlabel("Mean one-way delay (ms, log scale)")
    ax.set_ylabel("Bottleneck utilization (%)")
    ax.set_ylim(0, 108)
    ax.set_title("Utilization-delay trade-off (TCP-only, 19 scenarios)")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    plots.append(
        {
            "stem": "fig03_tradeoff_clean",
            "files": save_figure(fig, "fig03_tradeoff_clean"),
        }
    )


def plot_udp_burst(view: dict, plots: list) -> None:
    sids = UDP_PAIRED_SIDS
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 5.6), sharex=True)
    width = 0.19
    x = np.arange(len(sids))
    for index, protocol in enumerate(PROTOCOL_ORDER):
        drop_offsets, drops, loss_offsets, losses = [], [], [], []
        for position, sid in enumerate(sids):
            scenario = dict(S_ORDER)[sid]
            tcp_row = view["tcp_only"].get(scenario, {}).get(protocol)
            udp_row = view["udp_burst"].get(scenario, {}).get(protocol)
            if tcp_row is None or udp_row is None:
                continue
            tcp_goodput = float(tcp_row["Goodput_Mbps"])
            drop_offsets.append(position + (index - 1.5) * width)
            drops.append(
                100.0 * (float(udp_row["Goodput_Mbps"]) - tcp_goodput) / tcp_goodput
            )
            loss_offsets.append(position + (index - 1.5) * width)
            losses.append(
                max(float(udp_row["Loss_pct"]) - float(tcp_row["Loss_pct"]), 0.0)
            )
        axes[0].bar(
            drop_offsets,
            drops,
            width=width,
            color=PROTOCOL_COLORS[protocol],
            label=PROTOCOL_LABEL[protocol],
            edgecolor="white",
            linewidth=0.5,
        )
        axes[1].bar(
            loss_offsets,
            losses,
            width=width,
            color=PROTOCOL_COLORS[protocol],
            label=PROTOCOL_LABEL[protocol],
            edgecolor="white",
            linewidth=0.5,
        )
    axes[0].axhline(0, color="#444444", linewidth=0.8)
    axes[0].set_ylabel("Goodput change under burst (%)")
    axes[0].set_title("Cross-traffic robustness on the 15 paired scenarios")
    axes[0].legend(
        ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.28), frameon=False
    )
    axes[1].set_yscale("symlog", linthresh=0.1)
    axes[1].set_ylabel("Added loss under burst (pp)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(sids)
    fig.tight_layout()
    plots.append(
        {
            "stem": "fig04_udp_burst_clean",
            "files": save_figure(fig, "fig04_udp_burst_clean"),
        }
    )


def add_box(ax, xy, width, height, text, facecolor, fontsize=8.5) -> None:
    ax.add_patch(
        FancyBboxPatch(
            xy,
            width,
            height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=1.0,
            edgecolor="#333333",
            facecolor=facecolor,
        )
    )
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
    )


def add_arrow(ax, start, end, text=None, color="#333333") -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="-|>", color=color, linewidth=1.1, shrinkA=3, shrinkB=3
        ),
    )
    if text:
        ax.text(
            (start[0] + end[0]) / 2,
            (start[1] + end[1]) / 2 + 0.022,
            text,
            ha="center",
            fontsize=7,
            color=color,
        )


def plot_architecture(plots: list) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    add_box(
        ax,
        (0.03, 0.60),
        0.20,
        0.22,
        "ns-3 TCP协议栈\n五类回调采集\nACK/丢包/RTT/ECN",
        "#DCEAF7",
    )
    add_box(
        ax,
        (0.29, 0.60),
        0.22,
        0.22,
        "OpenGym状态容器\n11维有效观测\n+ 4项元数据",
        "#E8F3E8",
    )
    add_box(
        ax,
        (0.57, 0.60),
        0.20,
        0.22,
        "跨进程同步交互\nZeroMQ + Protobuf\n请求-应答",
        "#FFF7DE",
    )
    add_box(
        ax, (0.81, 0.60), 0.16, 0.22, "智能体决策\n动作对\n[ssThresh, cWnd]", "#FCE4D6"
    )
    add_box(
        ax,
        (0.05, 0.12),
        0.24,
        0.24,
        "拥塞三分类判定\n超时 0.50 / ECN 0.75\n普通丢包 0.70",
        "#F4CCCC",
    )
    add_box(
        ax,
        (0.35, 0.12),
        0.26,
        0.24,
        "两级BDP估计\n时间窗交付速率\n+ 40样本最大值滤波",
        "#EADCF8",
    )
    add_box(
        ax,
        (0.67, 0.12),
        0.28,
        0.24,
        "基线相对奖励自适应\n快/慢EMA对比\n有界步长逼近 α×BDP",
        "#D9EAD3",
    )
    add_arrow(ax, (0.23, 0.71), (0.29, 0.71), "观测")
    add_arrow(ax, (0.51, 0.71), (0.57, 0.71))
    add_arrow(ax, (0.77, 0.71), (0.81, 0.71))
    add_arrow(ax, (0.17, 0.60), (0.17, 0.36), "拥塞信号")
    add_arrow(ax, (0.44, 0.60), (0.48, 0.36), "速率样本")
    add_arrow(ax, (0.29, 0.24), (0.35, 0.24), "非拥塞路径")
    add_arrow(ax, (0.61, 0.24), (0.67, 0.24), "BDP")
    add_arrow(ax, (0.86, 0.36), (0.88, 0.60), "候选窗口", "#0072B2")
    ax.annotate(
        "",
        xy=(0.13, 0.82),
        xytext=(0.86, 0.82),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#0072B2",
            linewidth=1.2,
            shrinkA=2,
            shrinkB=2,
            connectionstyle="arc3,rad=0.16",
        ),
    )
    ax.text(
        0.50,
        0.90,
        "动作 [ssThresh, cWnd] 经应答写回协议栈",
        ha="center",
        fontsize=7.5,
        color="#0072B2",
    )
    ax.text(
        0.5,
        0.97,
        "算法控制回路总体架构（v3.0.0）",
        ha="center",
        fontsize=12,
        fontweight="bold",
    )
    fig.tight_layout()
    plots.append(
        {
            "stem": "fig06_architecture_zh",
            "files": save_figure(fig, "fig06_architecture_zh"),
        }
    )


def plot_workflow(plots: list) -> None:
    fig, ax = plt.subplots(figsize=(9.4, 7.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    add_box(ax, (0.40, 0.93), 0.20, 0.045, "连接建立", "#EEEEEE")
    add_box(
        ax,
        (0.28, 0.795),
        0.44,
        0.095,
        "S1 状态获取：11维有效观测子空间\n窗口状态 / 传输指标 / 时延测量 / 协议栈内部状态",
        "#DCEAF7",
    )
    add_box(
        ax,
        (0.28, 0.66),
        0.44,
        0.09,
        "S2 拥塞判定\n窗口缩减回调内的三分类语义判定",
        "#FFF7DE",
    )
    add_box(
        ax,
        (0.11, 0.30),
        0.40,
        0.22,
        "S5b 差异化缩减与安全保护\n保留因子：超时 0.50 / ECN 0.75 / 丢包 0.70\n慢启动阈值锚定 min(cwnd, BDP)\n连续缩减保护 · 降窗后冻结\n窗口箝位 · 陈旧决策作废",
        "#F4CCCC",
    )
    add_box(
        ax,
        (0.58, 0.46),
        0.40,
        0.13,
        "S3 带宽延迟积两级估计\n时间窗交付速率（跨度 ≥ 2×最小RTT）\n40样本最大值滤波，BDP = 最大带宽 × 最小RTT",
        "#EADCF8",
    )
    add_box(
        ax,
        (0.58, 0.295),
        0.40,
        0.115,
        "S4 参数自适应\nRTT膨胀 + 基线相对奖励 + 连续增长\n乘性增加因子 α ∈ [0.85, 1.30]",
        "#D9EAD3",
    )
    add_box(
        ax,
        (0.58, 0.135),
        0.40,
        0.11,
        "S5a 目标窗口逼近\n目标窗口 = α × BDP\n上行有界步长 / 下行超出量的一半",
        "#E8F3E8",
    )
    add_box(
        ax,
        (0.28, 0.02),
        0.44,
        0.065,
        "S6 决策应用：更新拥塞窗口与慢启动阈值",
        "#FCE4D6",
    )
    add_arrow(ax, (0.50, 0.93), (0.50, 0.89))
    add_arrow(ax, (0.50, 0.795), (0.50, 0.75))
    add_arrow(ax, (0.40, 0.66), (0.31, 0.52), "拥塞（三类）")
    add_arrow(ax, (0.60, 0.66), (0.74, 0.59), "非拥塞")
    add_arrow(ax, (0.78, 0.46), (0.78, 0.41))
    add_arrow(ax, (0.78, 0.295), (0.78, 0.245))
    add_arrow(ax, (0.68, 0.135), (0.60, 0.085))
    add_arrow(ax, (0.31, 0.30), (0.38, 0.085))
    feedback_color = "#0072B2"
    ax.plot([0.28, 0.05], [0.0525, 0.0525], color=feedback_color, linewidth=1.2)
    ax.plot([0.05, 0.05], [0.0525, 0.8425], color=feedback_color, linewidth=1.2)
    add_arrow(ax, (0.05, 0.8425), (0.28, 0.8425), color=feedback_color)
    ax.text(
        0.038,
        0.62,
        "奖励反馈：快速EMA与慢速基线EMA更新",
        ha="center",
        va="center",
        rotation=90,
        fontsize=7.5,
        color=feedback_color,
    )
    fig.suptitle("拥塞控制方法整体流程", fontsize=12, fontweight="bold", y=0.995)
    plots.append(
        {"stem": "fig07_workflow_zh", "files": save_figure(fig, "fig07_workflow_zh")}
    )


def clean_stale_outputs() -> list[str]:
    removed = []
    for path in sorted(PLOTS_DIR.glob("fig*")):
        if path.suffix in {".png", ".pdf", ".svg"}:
            path.unlink()
            removed.append(path.name)
    return removed


def main() -> None:
    configure_style()
    rows = derive_rows()
    if len(rows) != 288:
        raise ValueError(f"Expected 288 artifacts, found {len(rows)}")
    csv_status = write_and_verify_csv(rows)
    view = build_plot_view(rows)
    removed = clean_stale_outputs()
    plots: list[dict] = []
    plot_goodput(view, plots)
    plot_delay(view, plots)
    plot_tradeoff(view, plots)
    plot_udp_burst(view, plots)
    plot_architecture(plots)
    plot_workflow(plots)
    manifest = {
        "source": "logs/{comparison,comparison-udp}/*.flowmonitor (288 artifacts)",
        "kpi_csv": KPI_CSV.relative_to(REPO_ROOT).as_posix(),
        "kpi_csv_status": csv_status,
        "metric_definition": "forward TCP data flows only (proto 6, 10.1.x -> 10.2.x)",
        "selected_groups": {
            "tcp_only": [f"{sid}={scenario}" for sid, scenario in S_ORDER],
            "udp_burst": UDP_PAIRED_SIDS,
        },
        "stale_outputs_removed": removed,
        "figures": plots,
    }
    (PLOTS_DIR / "figure_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "kpi_csv_status": csv_status,
                "selected_tcp_groups": len(view["tcp_only"]),
                "selected_udp_groups": len(view["udp_burst"]),
                "figures": [plot["stem"] for plot in plots],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
