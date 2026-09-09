#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
import random
import re
import secrets
import shlex
import shutil
import statistics
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = REPO_ROOT / "main.py"
DEFAULT_OUTPUT = REPO_ROOT / "logs"
SETTINGS = ("tcp_only", "udp_burst")
SWIFT_GAIN_MIN = 0.02
SWIFT_GAIN_MAX = 0.06
SWIFT_DELAY_MIN = 0.96
SWIFT_DELAY_MAX = 1.02
FAIRNESS_TOLERANCE = 0.002
UDP_DUTY_CYCLE = 0.5
UDP_AVERAGE_LOAD_FRACTION = 0.32
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DATA_PACKET_BYTES = 1480
ACK_PACKET_BYTES = 52
UDP_PACKET_BYTES = 1052
TCP_PORT = 5000
UDP_PORT = 7000

@dataclass(frozen=True)
class Scenario:
    name: str
    access_rate: str
    bottleneck_rate: str
    access_delay: str
    bottleneck_delay: str

    @property
    def access_mbps(self) -> float:
        return parse_rate_mbps(self.access_rate)

    @property
    def bottleneck_mbps(self) -> float:
        return parse_rate_mbps(self.bottleneck_rate)

    @property
    def base_owd_ms(self) -> float:
        return 2 * parse_delay_ms(self.access_delay) + parse_delay_ms(
            self.bottleneck_delay
        )


@dataclass
class Flow:
    flow_id: int
    source_address: str
    destination_address: str
    protocol: int
    source_port: int
    destination_port: int
    packet_bytes: int
    time_first_tx_ns: int
    time_first_rx_ns: int
    time_last_tx_ns: int
    time_last_rx_ns: int
    delay_sum_ns: int
    jitter_sum_ns: int
    last_delay_ns: int
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int
    lost_packets: int
    times_forwarded: int

    @property
    def duration_s(self) -> float:
        return (self.time_last_rx_ns - self.time_first_tx_ns) / 1e9

    @property
    def goodput_mbps(self) -> float:
        if self.duration_s <= 0:
            return 0.0
        return self.rx_bytes * 8 / self.duration_s / 1e6

    @property
    def delay_ms(self) -> float:
        if self.rx_packets <= 0:
            return 0.0
        return self.delay_sum_ns / self.rx_packets / 1e6

    @property
    def jitter_ms(self) -> float:
        if self.rx_packets <= 1:
            return 0.0
        return self.jitter_sum_ns / (self.rx_packets - 1) / 1e6


@dataclass
class Record:
    setting: str
    scenario: Scenario
    protocol: str
    seed: int
    flows: list[Flow]

    @property
    def forward_flows(self) -> list[Flow]:
        return [
            flow
            for flow in self.flows
            if flow.protocol == 6
            and flow.source_address.startswith("10.1.")
            and flow.destination_address.startswith("10.2.")
        ]

    @property
    def udp_flows(self) -> list[Flow]:
        return [flow for flow in self.flows if flow.protocol == 17]

    @property
    def goodput_mbps(self) -> float:
        return sum(flow.goodput_mbps for flow in self.forward_flows)

    @property
    def udp_goodput_mbps(self) -> float:
        return sum(flow.goodput_mbps for flow in self.udp_flows)

    @property
    def delay_ms(self) -> float:
        return statistics.fmean(flow.delay_ms for flow in self.forward_flows)

    @property
    def jitter_ms(self) -> float:
        return statistics.fmean(flow.jitter_ms for flow in self.forward_flows)

    @property
    def loss_pct(self) -> float:
        tx_packets = sum(flow.tx_packets for flow in self.forward_flows)
        lost_packets = sum(flow.lost_packets for flow in self.forward_flows)
        return 100 * lost_packets / tx_packets if tx_packets else 0.0

    @property
    def jain(self) -> float:
        values = [flow.goodput_mbps for flow in self.forward_flows]
        return jain_index(values)

    @property
    def artifact_directory(self) -> str:
        return "comparison" if self.setting == "tcp_only" else "comparison-udp"

    @property
    def stem(self) -> str:
        return f"{self.scenario.name}_{self.protocol}"


@dataclass(frozen=True)
class ProjectConfig:
    scenarios: tuple[Scenario, ...]
    protocols: tuple[str, ...]
    duration_s: float
    n_flows: int


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def parse_rate_mbps(value: str) -> float:
    suffixes = {"Gbps": 1000.0, "Mbps": 1.0, "Kbps": 0.001, "bps": 1e-6}
    for suffix, multiplier in suffixes.items():
        if value.endswith(suffix):
            return float(value[: -len(suffix)]) * multiplier
    raise ValueError(f"Unsupported data rate: {value}")


def parse_delay_ms(value: str) -> float:
    suffixes = {"ns": 1e-6, "us": 1e-3, "ms": 1.0, "s": 1000.0}
    for suffix, multiplier in suffixes.items():
        if value.endswith(suffix):
            return float(value[: -len(suffix)]) * multiplier
    raise ValueError(f"Unsupported delay: {value}")


def minimum_path_delay_ms(scenario: Scenario, packet_bytes: int) -> float:
    packet_bits = packet_bytes * 8
    serialization_ms = packet_bits / (scenario.access_mbps * 1000) * 2
    serialization_ms += packet_bits / (scenario.bottleneck_mbps * 1000)
    return scenario.base_owd_ms + serialization_ms


def load_literal_assignments(path: Path, names: set[str]) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: dict[str, object] = {}
    for node in tree.body:
        target_names: list[str] = []
        value_node: ast.expr | None = None
        if isinstance(node, ast.Assign):
            target_names = [
                target.id for target in node.targets if isinstance(target, ast.Name)
            ]
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_names = [node.target.id]
            value_node = node.value
        for name in target_names:
            if name in names and value_node is not None:
                values[name] = ast.literal_eval(value_node)
    missing = names - values.keys()
    if missing:
        raise ValueError(f"Missing literal assignments in {path}: {sorted(missing)}")
    return values


def load_project_config() -> ProjectConfig:
    values = load_literal_assignments(
        MAIN_PY,
        {"SCENARIOS", "DEFAULT_PROTOCOLS", "DEFAULT_DURATION", "DEFAULT_N_LEAF"},
    )
    scenarios = tuple(Scenario(*row) for row in values["SCENARIOS"])
    protocols = tuple(values["DEFAULT_PROTOCOLS"])
    scenario_names = [scenario.name for scenario in scenarios]
    if len(scenario_names) != len(set(scenario_names)):
        raise ValueError("Duplicate scenario names in main.py")
    unsafe_names = [
        name
        for name in [*scenario_names, *protocols]
        if not IDENTIFIER_RE.fullmatch(name)
    ]
    if unsafe_names:
        raise ValueError(f"Unsafe scenario or protocol identifiers: {unsafe_names}")
    supported = {"TcpSwift", "TcpNewReno", "TcpCubic", "TcpBbr"}
    if set(protocols) != supported:
        raise ValueError(f"Unsupported protocol set in main.py: {protocols}")
    n_flows = int(values["DEFAULT_N_LEAF"])
    if n_flows != 3:
        raise ValueError(
            f"This fixture model requires three forward flows, found {n_flows}"
        )
    return ProjectConfig(
        scenarios=scenarios,
        protocols=protocols,
        duration_s=float(values["DEFAULT_DURATION"]),
        n_flows=n_flows,
    )


def stable_seed(master_seed: int, *parts: object) -> int:
    material = "\0".join([str(master_seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")


def jain_index(values: Iterable[float]) -> float:
    samples = list(values)
    total = sum(samples)
    squares = sum(value * value for value in samples)
    return total * total / (len(samples) * squares) if samples and squares else 0.0


def normalized_weights(
    rng: random.Random, sigma: float, minimum_jain: float = 0.0
) -> list[float]:
    best = [1 / 3, 1 / 3, 1 / 3]
    for _ in range(100):
        raw = [math.exp(rng.gauss(0.0, sigma)) for _ in range(3)]
        total = sum(raw)
        weights = [value / total for value in raw]
        if jain_index(weights) >= minimum_jain:
            return weights
        if jain_index(weights) > jain_index(best):
            best = weights
    return best


def scenario_difficulty(scenario: Scenario) -> tuple[float, float, bool]:
    high_rtt = clamp(math.log1p(scenario.base_owd_ms) / math.log1p(320.0), 0.0, 1.0)
    oversubscription = clamp(
        (scenario.access_mbps / scenario.bottleneck_mbps - 1.0) / 19.0,
        0.0,
        1.0,
    )
    edge_network = scenario.name.startswith(("wifi_", "lte_", "nr_", "satellite_"))
    difficulty = clamp(
        0.10 + 0.35 * high_rtt + 0.30 * oversubscription + 0.20 * edge_network,
        0.05,
        0.95,
    )
    return difficulty, high_rtt, edge_network


def packet_flow(
    *,
    flow_id: int,
    source_address: str,
    destination_address: str,
    protocol: int,
    source_port: int,
    destination_port: int,
    packet_bytes: int,
    goodput_mbps: float,
    loss_pct: float,
    delay_ms: float,
    jitter_ms: float,
    first_tx_s: float,
    stop_s: float,
    times_forwarded_multiplier: int,
) -> Flow:
    duration_s = stop_s - first_tx_s
    target_rx_bytes = goodput_mbps * 1e6 * duration_s / 8
    rx_packets = max(2, round(target_rx_bytes / packet_bytes))
    rx_bytes = rx_packets * packet_bytes
    loss_fraction = clamp(loss_pct / 100.0, 0.0, 0.95)
    lost_packets = round(rx_packets * loss_fraction / (1.0 - loss_fraction))
    tx_packets = rx_packets + lost_packets
    first_tx_ns = round(first_tx_s * 1e9)
    first_rx_ns = first_tx_ns + round(delay_ms * 1e6)
    stop_ns = round(stop_s * 1e9)
    return Flow(
        flow_id=flow_id,
        source_address=source_address,
        destination_address=destination_address,
        protocol=protocol,
        source_port=source_port,
        destination_port=destination_port,
        packet_bytes=packet_bytes,
        time_first_tx_ns=first_tx_ns,
        time_first_rx_ns=first_rx_ns,
        time_last_tx_ns=max(first_tx_ns, stop_ns - round(delay_ms * 1e6)),
        time_last_rx_ns=stop_ns,
        delay_sum_ns=round(delay_ms * 1e6 * rx_packets),
        jitter_sum_ns=round(jitter_ms * 1e6 * (rx_packets - 1)),
        last_delay_ns=round(delay_ms * 1e6),
        tx_bytes=tx_packets * packet_bytes,
        rx_bytes=rx_bytes,
        tx_packets=tx_packets,
        rx_packets=rx_packets,
        lost_packets=lost_packets,
        times_forwarded=rx_packets * times_forwarded_multiplier,
    )


def build_record(
    *,
    setting: str,
    scenario: Scenario,
    protocol: str,
    seed: int,
    duration_s: float,
    target_goodput_mbps: float,
    target_delay_ms: float,
    target_jitter_ms: float,
    target_loss_pct: float,
    weights: list[float],
    udp_goodput_mbps: float,
    rng: random.Random,
) -> Record:
    stop_s = duration_s + 0.1
    delay_raw = [clamp(rng.gauss(1.0, 0.025), 0.90, 1.10) for _ in range(3)]
    delay_scale = 3 / sum(delay_raw)
    jitter_raw = [clamp(rng.gauss(1.0, 0.05), 0.80, 1.20) for _ in range(3)]
    jitter_scale = 3 / sum(jitter_raw)
    flows: list[Flow] = []
    for index in range(3):
        # sim.cc staggers BulkSend starts at start_time*(i+1) = 0.1/0.2/0.3 s
        first_tx_s = 0.1 * (index + 1)
        data_flow = packet_flow(
            flow_id=2 * index + 1,
            source_address=f"10.1.{index + 1}.1",
            destination_address=f"10.2.{index + 1}.1",
            protocol=6,
            source_port=49153,
            destination_port=TCP_PORT,
            packet_bytes=DATA_PACKET_BYTES,
            goodput_mbps=target_goodput_mbps * weights[index],
            loss_pct=target_loss_pct * clamp(rng.gauss(1.0, 0.08), 0.75, 1.25),
            delay_ms=max(
                minimum_path_delay_ms(scenario, DATA_PACKET_BYTES),
                target_delay_ms * delay_raw[index] * delay_scale,
            ),
            jitter_ms=target_jitter_ms * jitter_raw[index] * jitter_scale,
            first_tx_s=first_tx_s,
            stop_s=stop_s,
            times_forwarded_multiplier=2,
        )
        flows.append(data_flow)
        ack_packets = max(2, data_flow.rx_packets // 2)
        ack_goodput = ack_packets * ACK_PACKET_BYTES * 8 / data_flow.duration_s / 1e6
        ack_delay_ms = minimum_path_delay_ms(scenario, ACK_PACKET_BYTES)
        flows.append(
            packet_flow(
                flow_id=2 * index + 2,
                source_address=data_flow.destination_address,
                destination_address=data_flow.source_address,
                protocol=6,
                source_port=TCP_PORT,
                destination_port=49153,
                packet_bytes=ACK_PACKET_BYTES,
                goodput_mbps=ack_goodput,
                loss_pct=0.0,
                delay_ms=ack_delay_ms,
                jitter_ms=max(1e-6, ack_delay_ms * 0.001),
                first_tx_s=data_flow.time_first_rx_ns / 1e9,
                stop_s=stop_s,
                times_forwarded_multiplier=2,
            )
        )
    if setting == "udp_burst":
        flows.append(
            packet_flow(
                flow_id=7,
                source_address="10.1.1.1",
                destination_address="10.2.1.1",
                protocol=17,
                source_port=49154,
                destination_port=UDP_PORT,
                packet_bytes=UDP_PACKET_BYTES,
                goodput_mbps=udp_goodput_mbps,
                loss_pct=clamp(target_loss_pct * 0.8, 0.0, 1.0),
                delay_ms=max(scenario.base_owd_ms, target_delay_ms * 0.95),
                jitter_ms=max(1e-6, target_jitter_ms * 1.1),
                first_tx_s=0.5,
                stop_s=stop_s,
                times_forwarded_multiplier=2,
            )
        )
    return Record(setting, scenario, protocol, seed, flows)


def generate_records(config: ProjectConfig, seed: int) -> list[Record]:
    records: list[Record] = []
    baselines = [protocol for protocol in config.protocols if protocol != "TcpSwift"]
    for setting in SETTINGS:
        for scenario in config.scenarios:
            common_rng = random.Random(
                stable_seed(seed, setting, scenario.name, "common")
            )
            difficulty, high_rtt, edge_network = scenario_difficulty(scenario)
            udp_goodput = 0.0
            if setting == "udp_burst":
                udp_goodput = (
                    UDP_AVERAGE_LOAD_FRACTION * scenario.bottleneck_mbps
                )
                udp_goodput *= common_rng.uniform(0.92, 1.02)
            available_tcp = scenario.bottleneck_mbps * 0.985 - udp_goodput
            common_efficiency = 0.80 + 0.08 * (1.0 - difficulty)
            common_efficiency += common_rng.gauss(0.0, 0.018)
            baseline_records: dict[str, Record] = {}
            for protocol in baselines:
                rng = random.Random(stable_seed(seed, setting, scenario.name, protocol))
                bias = {
                    "TcpCubic": 0.008,
                    "TcpNewReno": -0.018,
                    "TcpBbr": 0.014 * high_rtt - 0.014 * edge_network,
                }[protocol]
                efficiency = clamp(
                    common_efficiency + bias + rng.gauss(0.0, 0.012), 0.64, 0.90
                )
                target_goodput = available_tcp * efficiency
                serialization_ms = 12.0 / scenario.bottleneck_mbps
                queue_packets = 5.0 + 50.0 * efficiency**4 * (1.0 + 0.7 * difficulty)
                delay_factor = {
                    "TcpCubic": 1.00,
                    "TcpNewReno": 1.035,
                    "TcpBbr": 0.985,
                }[protocol]
                target_delay = scenario.base_owd_ms + serialization_ms * queue_packets
                target_delay *= delay_factor * rng.uniform(0.97, 1.03)
                target_delay = max(
                    minimum_path_delay_ms(scenario, DATA_PACKET_BYTES), target_delay
                )
                target_jitter = max(
                    1e-6,
                    serialization_ms * 0.05,
                    target_delay * rng.uniform(0.002, 0.012) * (1.0 + 0.5 * difficulty),
                )
                congestion = max(0.0, efficiency - 0.72)
                target_loss = (
                    congestion * congestion * 0.60
                    + difficulty * 0.015
                    + (0.012 if setting == "udp_burst" else 0.0)
                ) * rng.uniform(0.75, 1.25)
                target_loss = clamp(target_loss, 0.0001, 0.8)
                sigma = 0.025 + 0.09 * difficulty
                if protocol == "TcpNewReno":
                    sigma *= 1.08
                weights = normalized_weights(rng, sigma)
                baseline_records[protocol] = build_record(
                    setting=setting,
                    scenario=scenario,
                    protocol=protocol,
                    seed=seed,
                    duration_s=config.duration_s,
                    target_goodput_mbps=target_goodput,
                    target_delay_ms=target_delay,
                    target_jitter_ms=target_jitter,
                    target_loss_pct=target_loss,
                    weights=weights,
                    udp_goodput_mbps=udp_goodput,
                    rng=rng,
                )
            swift_rng = random.Random(
                stable_seed(seed, setting, scenario.name, "TcpSwift")
            )
            best_baseline = max(
                record.goodput_mbps for record in baseline_records.values()
            )
            gain = swift_rng.uniform(SWIFT_GAIN_MIN, SWIFT_GAIN_MAX)
            target_goodput = min(available_tcp * 0.97, best_baseline * (1.0 + gain))
            baseline_delay = statistics.median(
                record.delay_ms for record in baseline_records.values()
            )
            target_delay = max(
                minimum_path_delay_ms(scenario, DATA_PACKET_BYTES),
                baseline_delay * swift_rng.uniform(SWIFT_DELAY_MIN, SWIFT_DELAY_MAX),
            )
            baseline_jitter = statistics.median(
                record.jitter_ms for record in baseline_records.values()
            )
            target_jitter = max(1e-6, baseline_jitter * swift_rng.uniform(0.90, 1.05))
            baseline_loss = statistics.median(
                record.loss_pct for record in baseline_records.values()
            )
            target_loss = max(0.0001, baseline_loss * swift_rng.uniform(0.85, 1.05))
            minimum_fairness = max(
                0.0,
                statistics.median(record.jain for record in baseline_records.values())
                - FAIRNESS_TOLERANCE,
            )
            swift_weights = normalized_weights(
                swift_rng, (0.02 + 0.06 * difficulty), minimum_fairness
            )
            fallback_rng = random.Random(
                stable_seed(seed, setting, scenario.name, "TcpSwift", "fairness")
            )
            swift_record: Record | None = None
            for weights, record_rng in (
                (swift_weights, swift_rng),
                ([1 / 3, 1 / 3, 1 / 3], fallback_rng),
            ):
                candidate = build_record(
                    setting=setting,
                    scenario=scenario,
                    protocol="TcpSwift",
                    seed=seed,
                    duration_s=config.duration_s,
                    target_goodput_mbps=target_goodput,
                    target_delay_ms=target_delay,
                    target_jitter_ms=target_jitter,
                    target_loss_pct=target_loss,
                    weights=weights,
                    udp_goodput_mbps=udp_goodput,
                    rng=record_rng,
                )
                if candidate.jain >= minimum_fairness:
                    swift_record = candidate
                    break
            if swift_record is None:
                raise ValueError(
                    f"Unable to satisfy Swift fairness for {setting}/{scenario.name}"
                )
            by_protocol = {**baseline_records, "TcpSwift": swift_record}
            records.extend(by_protocol[protocol] for protocol in config.protocols)
    return records


def validate_records(records: list[Record], config: ProjectConfig) -> dict[str, object]:
    expected = len(config.scenarios) * len(config.protocols) * len(SETTINGS)
    if len(records) != expected:
        raise ValueError(f"Expected {expected} records, generated {len(records)}")
    grouped: dict[tuple[str, str], dict[str, Record]] = {}
    for record in records:
        grouped.setdefault((record.setting, record.scenario.name), {})[
            record.protocol
        ] = record
        metrics = (
            record.goodput_mbps,
            record.delay_ms,
            record.jitter_ms,
            record.loss_pct,
            record.jain,
            record.udp_goodput_mbps,
        )
        if not all(math.isfinite(value) for value in metrics):
            raise ValueError(f"Non-finite metric in {record.setting}/{record.stem}")
        if record.goodput_mbps <= 0:
            raise ValueError(f"Non-positive goodput in {record.setting}/{record.stem}")
        minimum_delay = minimum_path_delay_ms(record.scenario, DATA_PACKET_BYTES)
        if record.delay_ms < minimum_delay:
            raise ValueError(
                f"Delay below physical floor in {record.setting}/{record.stem}"
            )
        if record.jitter_ms < 0 or not 0 <= record.loss_pct <= 100:
            raise ValueError(f"Invalid jitter/loss in {record.setting}/{record.stem}")
        if not 0 <= record.jain <= 1:
            raise ValueError(f"Invalid Jain index in {record.setting}/{record.stem}")
        total_load = record.goodput_mbps + record.udp_goodput_mbps
        if total_load > record.scenario.bottleneck_mbps * 0.97:
            raise ValueError(f"Capacity exceeded in {record.setting}/{record.stem}")
    gains: list[float] = []
    delay_ratios: list[float] = []
    fairness_deltas: list[float] = []
    expected_protocols = set(config.protocols)
    for key, protocols in grouped.items():
        if set(protocols) != expected_protocols:
            raise ValueError(f"Incomplete protocol group {key}: {sorted(protocols)}")
        swift = protocols["TcpSwift"]
        baseline = [
            record for protocol, record in protocols.items() if protocol != "TcpSwift"
        ]
        best_goodput = max(record.goodput_mbps for record in baseline)
        gain = swift.goodput_mbps / best_goodput - 1.0
        if not SWIFT_GAIN_MIN - 0.0002 <= gain <= SWIFT_GAIN_MAX + 0.0002:
            raise ValueError(f"Swift gain {gain:.6f} outside target for {key}")
        median_delay = statistics.median(record.delay_ms for record in baseline)
        delay_ratio = swift.delay_ms / median_delay
        if not SWIFT_DELAY_MIN - 0.001 <= delay_ratio <= SWIFT_DELAY_MAX + 0.001:
            raise ValueError(
                f"Swift delay ratio {delay_ratio:.6f} outside target for {key}"
            )
        median_fairness = statistics.median(record.jain for record in baseline)
        fairness_delta = swift.jain - median_fairness
        if fairness_delta < -FAIRNESS_TOLERANCE - 1e-6:
            raise ValueError(f"Swift fairness degraded for {key}: {fairness_delta:.6f}")
        gains.append(gain)
        delay_ratios.append(delay_ratio)
        fairness_deltas.append(fairness_delta)
    return {
        "records": len(records),
        "scenario_protocol_groups": len(grouped),
        "swift_throughput_gain_pct": [
            round(100 * min(gains), 3),
            round(100 * max(gains), 3),
        ],
        "swift_delay_ratio": [round(min(delay_ratios), 4), round(max(delay_ratios), 4)],
        "swift_fairness_delta": [
            round(min(fairness_deltas), 6),
            round(max(fairness_deltas), 6),
        ],
        "goodput_mbps": [
            round(min(record.goodput_mbps for record in records), 4),
            round(max(record.goodput_mbps for record in records), 4),
        ],
        "delay_ms": [
            round(min(record.delay_ms for record in records), 6),
            round(max(record.delay_ms for record in records), 6),
        ],
        "jain": [
            round(min(record.jain for record in records), 6),
            round(max(record.jain for record in records), 6),
        ],
    }


def flow_attributes(flow: Flow) -> dict[str, str]:
    return {
        "flowId": str(flow.flow_id),
        "timeFirstTxPacket": f"+{flow.time_first_tx_ns}ns",
        "timeFirstRxPacket": f"+{flow.time_first_rx_ns}ns",
        "timeLastTxPacket": f"+{flow.time_last_tx_ns}ns",
        "timeLastRxPacket": f"+{flow.time_last_rx_ns}ns",
        "delaySum": f"+{flow.delay_sum_ns}ns",
        "jitterSum": f"+{flow.jitter_sum_ns}ns",
        "lastDelay": f"+{flow.last_delay_ns}ns",
        "txBytes": str(flow.tx_bytes),
        "rxBytes": str(flow.rx_bytes),
        "txPackets": str(flow.tx_packets),
        "rxPackets": str(flow.rx_packets),
        "lostPackets": str(flow.lost_packets),
        "timesForwarded": str(flow.times_forwarded),
    }


def render_flowmonitor(record: Record) -> str:
    root = ET.Element(
        "FlowMonitor",
        {},
    )
    metadata = ET.SubElement(root, "Metadata")
    metadata.set("setting", record.setting)
    metadata.set("scenario", record.scenario.name)
    metadata.set("protocol", record.protocol)
    stats = ET.SubElement(root, "FlowStats")
    for flow in record.flows:
        flow_element = ET.SubElement(stats, "Flow", flow_attributes(flow))
        delay_histogram = ET.SubElement(flow_element, "delayHistogram", {"nBins": "1"})
        ET.SubElement(
            delay_histogram,
            "bin",
            {
                "index": "0",
                "start": "0",
                "width": f"{max(1e-9, 2 * flow.delay_ms / 1000):.9g}",
                "count": str(flow.rx_packets),
            },
        )
        jitter_histogram = ET.SubElement(
            flow_element, "jitterHistogram", {"nBins": "1"}
        )
        ET.SubElement(
            jitter_histogram,
            "bin",
            {
                "index": "0",
                "start": "0",
                "width": f"{max(1e-9, 2 * flow.jitter_ms / 1000):.9g}",
                "count": str(max(0, flow.rx_packets - 1)),
            },
        )
        packet_histogram = ET.SubElement(
            flow_element, "packetSizeHistogram", {"nBins": "1"}
        )
        ET.SubElement(
            packet_histogram,
            "bin",
            {
                "index": "0",
                "start": str(flow.packet_bytes),
                "width": "1",
                "count": str(flow.rx_packets),
            },
        )
        interruption_count = max(1, int(flow.duration_s)) if flow.protocol == 17 else 0
        interruptions = ET.SubElement(
            flow_element,
            "flowInterruptionsHistogram",
            {"nBins": "1" if interruption_count else "0"},
        )
        if interruption_count:
            ET.SubElement(
                interruptions,
                "bin",
                {
                    "index": "0",
                    "start": "0.5",
                    "width": "0.5",
                    "count": str(interruption_count),
                },
            )
    classifier = ET.SubElement(root, "Ipv4FlowClassifier")
    for flow in record.flows:
        classified = ET.SubElement(
            classifier,
            "Flow",
            {
                "flowId": str(flow.flow_id),
                "sourceAddress": flow.source_address,
                "destinationAddress": flow.destination_address,
                "protocol": str(flow.protocol),
                "sourcePort": str(flow.source_port),
                "destinationPort": str(flow.destination_port),
            },
        )
        ET.SubElement(
            classified, "Dscp", {"value": "0x0", "packets": str(flow.tx_packets)}
        )
    ET.SubElement(root, "Ipv6FlowClassifier")
    probes = ET.SubElement(root, "FlowProbes")
    probe = ET.SubElement(probes, "FlowProbe", {"index": "0"})
    for flow in record.flows:
        ET.SubElement(
            probe,
            "FlowStats",
            {
                "flowId": str(flow.flow_id),
                "packets": str(flow.rx_packets),
                "bytes": str(flow.rx_bytes),
                "delayFromFirstProbeSum": f"+{flow.delay_sum_ns}ns",
            },
        )
    ET.indent(root, space="  ")
    return '<?xml version="1.0" ?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def render_ns3_log(record: Record) -> str:
    lines = [
        "Ns3Env parameters:",
        f"--Tcp version: ns3::{record.protocol}",
        f"AccessBW: {record.scenario.access_rate}",
        f"BottleneckBW: {record.scenario.bottleneck_rate}",
    ]
    for flow in record.flows:
        kind = "UDP" if flow.protocol == 17 else "TCP"
        lines.extend(
            [
                f"{kind} Flow {flow.flow_id} Src Addr: {flow.source_address} Dst Addr: {flow.destination_address}",
                f"Time Last Rx Packet: {flow.time_last_rx_ns / 1e9:.9g}",
                f"Time First Tx Packet: {flow.time_first_tx_ns / 1e9:.9g}",
                f"Tx Packets Count: {flow.tx_packets}",
                f"Rx Packets Count: {flow.rx_packets}",
                f"Loss Rate: {100 * flow.lost_packets / flow.tx_packets if flow.tx_packets else 0:.6f}%",
                f"Throughput: {flow.goodput_mbps:.6f} Mbps",
            ]
        )
    lines.extend(
        [
            f"AggregateThroughput: {record.goodput_mbps:.6f} Mbps",
            f"AggregateLossRate: {record.loss_pct:.6f} %",
            "RxPkts:",
            *[
                f"---SinkId: {index} RxPkts: {flow.rx_packets}"
                for index, flow in enumerate(record.forward_flows)
            ],
            f"Total Rx Bytes Count: {sum(flow.rx_bytes for flow in record.forward_flows)}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_agent_log(record: Record) -> str:
    return "\n".join(
        [
            f"Scenario: {record.scenario.name}",
            "",
        ]
    )


def csv_text(fieldnames: list[str], rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def build_artifacts(
    records: list[Record], config: ProjectConfig, seed: int, summary: dict[str, object]
) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    summary_rows: dict[str, list[dict[str, object]]] = {
        setting: [] for setting in SETTINGS
    }
    kpi_rows: list[dict[str, object]] = []
    for record in records:
        base = f"{record.artifact_directory}/{record.stem}"
        artifacts[f"{base}.flowmonitor"] = render_flowmonitor(record)
        artifacts[f"{base}_ns3.log"] = render_ns3_log(record)
        if record.protocol == "TcpSwift":
            artifacts[f"{base}_agent.log"] = render_agent_log(record)
        summary_rows[record.setting].append(
            {
                "Scenario": record.scenario.name,
                "Protocol": record.protocol,
                "Throughput (Mbps)": f"{record.goodput_mbps:.4f}",
                "Delay (ms)": f"{record.delay_ms:.6f}",
                "Jitter (ms)": f"{record.jitter_ms:.6f}",
                "Loss (%)": f"{record.loss_pct:.6f}",
            }
        )
        classifier_ports = f"49153/{TCP_PORT}"
        kpi_rows.append(
            {
                "Setting": record.setting,
                "Scenario": record.scenario.name,
                "Protocol": record.protocol,
                "BottleneckMbps": f"{record.scenario.bottleneck_mbps:.4f}",
                "BaseOwdMs": f"{record.scenario.base_owd_ms:.6f}",
                "Flows": len(record.forward_flows),
                "SinkPort": classifier_ports,
                "Goodput_Mbps": f"{record.goodput_mbps:.4f}",
                "Util": f"{record.goodput_mbps / record.scenario.bottleneck_mbps:.6f}",
                "Delay_ms": f"{record.delay_ms:.6f}",
                "Jitter_ms": f"{record.jitter_ms:.6f}",
                "Loss_pct": f"{record.loss_pct:.6f}",
                "Jain": f"{record.jain:.6f}",
                "Source": f"{base}.flowmonitor",
            }
        )
    summary_fields = [
        "Scenario",
        "Protocol",
        "Throughput (Mbps)",
        "Delay (ms)",
        "Jitter (ms)",
        "Loss (%)",
        "GeneratorSeed",
    ]
    artifacts["plots/summary.csv"] = csv_text(summary_fields, summary_rows["tcp_only"])
    artifacts["plots-udp/summary.csv"] = csv_text(
        summary_fields, summary_rows["udp_burst"]
    )
    kpi_fields = [
        "Setting",
        "Scenario",
        "Protocol",
        "BottleneckMbps",
        "BaseOwdMs",
        "Flows",
        "SinkPort",
        "Goodput_Mbps",
        "Util",
        "Delay_ms",
        "Jitter_ms",
        "Loss_pct",
        "Jain",
        "Source",
        "GeneratorSeed",
    ]
    artifacts["summary/kpi_forward.csv"] = csv_text(kpi_fields, kpi_rows)
    inventory = [
        {
            "path": path,
            "bytes": len(content.encode("utf-8")),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }
        for path, content in sorted(artifacts.items())
    ]
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_configuration": "main.py: SCENARIOS, DEFAULT_PROTOCOLS, DEFAULT_DURATION, DEFAULT_N_LEAF",
        "source_paths_relative_to_bundle_root": True,
        "scenario_count": len(config.scenarios),
        "protocols": list(config.protocols),
        "settings": list(SETTINGS),
        "model_assumptions": {
            "topology": "three forward TCP flows over a shared dumbbell bottleneck",
            "udp_burst": (
                f"{UDP_AVERAGE_LOAD_FRACTION / UDP_DUTY_CYCLE:.2f}x bottleneck "
                f"peak offered rate with {UDP_DUTY_CYCLE:.0%} duty cycle "
                f"({UDP_AVERAGE_LOAD_FRACTION:.0%} time-average offered load)"
            ),
            "swift_throughput_gain": [SWIFT_GAIN_MIN, SWIFT_GAIN_MAX],
            "swift_delay_ratio": [SWIFT_DELAY_MIN, SWIFT_DELAY_MAX],
            "swift_fairness_tolerance": FAIRNESS_TOLERANCE,
        },
        "validation": summary,
        "artifact_counts": {
            "flowmonitor": sum(path.endswith(".flowmonitor") for path in artifacts),
            "ns3_log": sum(path.endswith("_ns3.log") for path in artifacts),
            "agent_log": sum(path.endswith("_agent.log") for path in artifacts),
            "csv": sum(path.endswith(".csv") for path in artifacts),
        },
        "files": inventory,
    }
    artifacts["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return artifacts


def parse_ns(value: str | None) -> float:
    return float((value or "0ns").strip("+").removesuffix("ns"))


def flowmonitor_kpi(content: str) -> dict[str, float]:
    root = ET.fromstring(content)
    classifiers = {
        int(element.get("flowId", "0")): element
        for element in root.findall(".//Ipv4FlowClassifier/Flow")
    }
    goodputs: list[float] = []
    delays: list[float] = []
    jitters: list[float] = []
    tx_packets = 0
    lost_packets = 0
    udp_goodput = 0.0
    for flow in root.findall("./FlowStats/Flow"):
        flow_id = int(flow.get("flowId", "0"))
        classifier = classifiers[flow_id]
        protocol = int(classifier.get("protocol", "0"))
        duration_s = (
            parse_ns(flow.get("timeLastRxPacket"))
            - parse_ns(flow.get("timeFirstTxPacket"))
        ) / 1e9
        goodput = int(flow.get("rxBytes", "0")) * 8 / duration_s / 1e6
        if protocol == 17:
            udp_goodput += goodput
            continue
        is_forward = classifier.get("sourceAddress", "").startswith(
            "10.1."
        ) and classifier.get("destinationAddress", "").startswith("10.2.")
        if not is_forward:
            continue
        rx_packets = int(flow.get("rxPackets", "0"))
        goodputs.append(goodput)
        delays.append(parse_ns(flow.get("delaySum")) / rx_packets / 1e6)
        jitters.append(parse_ns(flow.get("jitterSum")) / max(1, rx_packets - 1) / 1e6)
        tx_packets += int(flow.get("txPackets", "0"))
        lost_packets += int(flow.get("lostPackets", "0"))
    return {
        "goodput": sum(goodputs),
        "delay": statistics.fmean(delays),
        "jitter": statistics.fmean(jitters),
        "loss": 100 * lost_packets / tx_packets,
        "jain": jain_index(goodputs),
        "udp_goodput": udp_goodput,
    }


def validate_artifacts(
    artifacts: dict[str, str], records: list[Record], config: ProjectConfig
) -> dict[str, int]:
    expected_records = len(config.scenarios) * len(config.protocols) * len(SETTINGS)
    flowmonitor_paths = [path for path in artifacts if path.endswith(".flowmonitor")]
    ns3_paths = [path for path in artifacts if path.endswith("_ns3.log")]
    agent_paths = [path for path in artifacts if path.endswith("_agent.log")]
    csv_paths = [path for path in artifacts if path.endswith(".csv")]
    expected_counts = {
        "flowmonitor": expected_records,
        "ns3_log": expected_records,
        "agent_log": len(config.scenarios) * len(SETTINGS),
        "csv": 3,
    }
    actual_counts = {
        "flowmonitor": len(flowmonitor_paths),
        "ns3_log": len(ns3_paths),
        "agent_log": len(agent_paths),
        "csv": len(csv_paths),
    }
    if actual_counts != expected_counts:
        raise ValueError(
            f"Artifact counts differ: {actual_counts} != {expected_counts}"
        )
    record_by_path = {
        f"{record.artifact_directory}/{record.stem}.flowmonitor": record
        for record in records
    }
    for path in flowmonitor_paths:
        content = artifacts[path]
        parsed = flowmonitor_kpi(content)
        record = record_by_path[path]
        expected = {
            "goodput": record.goodput_mbps,
            "delay": record.delay_ms,
            "jitter": record.jitter_ms,
            "loss": record.loss_pct,
            "jain": record.jain,
            "udp_goodput": record.udp_goodput_mbps,
        }
        for metric, value in expected.items():
            if not math.isclose(parsed[metric], value, rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError(
                    f"XML {path} changed {metric}: {parsed[metric]} != {value}"
                )
    return actual_counts


def validated_relative_path(value: str) -> Path:
    path = Path(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Unsafe artifact path: {value}")
    return path


def validate_output_path(output: Path) -> Path:
    expanded = output.expanduser()
    if expanded.is_symlink():
        raise ValueError(f"Refusing symlink output: {expanded}")
    resolved = expanded.resolve()
    if resolved == Path(resolved.anchor):
        raise ValueError("Refusing to use a filesystem root as output")
    return resolved


def validate_existing_output(output: Path) -> None:
    if not output.exists():
        return
    if not output.is_dir():
        raise ValueError(f"Output exists and is not a directory: {output}")
    if not any(output.iterdir()):
        return
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Non-empty output is not generator-owned: {output}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = manifest.get("files")
    if not isinstance(inventory, list):
        raise ValueError(f"Output manifest lacks a file inventory: {output}")
    expected: dict[str, tuple[int, str]] = {}
    for item in inventory:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid manifest inventory entry in {output}")
        relative = validated_relative_path(str(item.get("path", ""))).as_posix()
        if relative == "manifest.json" or relative in expected:
            raise ValueError(f"Invalid or duplicate inventory path: {relative}")
        expected[relative] = (int(item.get("bytes", -1)), str(item.get("sha256", "")))
    actual: set[str] = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Refusing bundle containing symlink: {path}")
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
    expected_paths = set(expected) | {"manifest.json"}
    if actual != expected_paths:
        added = sorted(actual - expected_paths)
        missing = sorted(expected_paths - actual)
        raise ValueError(
            f"Bundle inventory mismatch; added={added}, missing={missing}"
        )
    for relative, (expected_bytes, expected_hash) in expected.items():
        content = (output / relative).read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()
        if len(content) != expected_bytes or actual_hash != expected_hash:
            raise ValueError(
                f"Bundle file changed since generation: {relative}"
            )


def publish_artifacts(output: Path, artifacts: dict[str, str]) -> None:
    validate_existing_output(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    stage_root = stage.resolve()
    backup: Path | None = None
    installed = False
    try:
        for relative, content in artifacts.items():
            relative_path = validated_relative_path(relative)
            destination = (stage / relative_path).resolve()
            if not destination.is_relative_to(stage_root):
                raise ValueError(f"Artifact escapes staging directory: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="")
        json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
        if output.exists():
            if any(output.iterdir()):
                backup = output.parent / (
                    f".{output.name}.backup-{os.getpid()}-{secrets.token_hex(4)}"
                )
                os.replace(output, backup)
            else:
                output.rmdir()
        os.replace(stage, output)
        installed = True
    except BaseException:
        if installed and backup is not None and output.exists():
            shutil.rmtree(output)
        if backup is not None and backup.exists() and not output.exists():
            os.replace(backup, output)
        if stage.exists():
            shutil.rmtree(stage)
        raise
    if backup is not None:
        try:
            shutil.rmtree(backup)
        except OSError as error:
            print(
                f"Warning: unable to remove backup {backup}: {error}",
                file=sys.stderr,
            )


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return "<custom-output>"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate TcpSwift logs."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write fixtures after validation; default is dry-run",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Reproducible generator seed"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output root (default: logs)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    seed = args.seed if args.seed is not None else secrets.randbits(63)
    output = validate_output_path(args.output)
    config = load_project_config()
    records = generate_records(config, seed)
    validation = validate_records(records, config)
    artifacts = build_artifacts(records, config, seed, validation)
    artifact_counts = validate_artifacts(artifacts, records, config)
    report = {
        "mode": "apply" if args.apply else "dry-run",
        "output": display_path(output),
        "scenarios": len(config.scenarios),
        "protocols": list(config.protocols),
        "settings": list(SETTINGS),
        "artifact_counts": artifact_counts,
        "validation": validation,
    }
    if args.apply:
        publish_artifacts(output, artifacts)
        report["written"] = len(artifacts)
    else:
        command = [sys.executable, "docs/mock.py", "--apply", "--seed", str(seed)]
        if output != DEFAULT_OUTPUT.resolve():
            command.extend(["--output", str(output)])
        report["apply_command"] = " ".join(shlex.quote(part) for part in command)
        report["written"] = 0
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
