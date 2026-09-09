# Swift — RL-Assisted Multi-Signal Congestion Control on ns-3.40

**Swift** (`TcpSwift`) is a reinforcement-learning-assisted, multi-signal fusion
TCP congestion control algorithm, implemented and evaluated on the
[ns-3.40](https://www.nsnam.org/) discrete-event network simulator through the
[ns3-gym](https://github.com/tkn-tub/ns3-gym) bridge. It targets long-distance
and heterogeneous access paths — data-center fabrics, WiFi, LTE/5G, metro/long-haul
WAN and satellite links — where fixed-parameter, single-signal algorithms struggle
to balance throughput, delay and loss simultaneously.

- Author: [Hang Tiancheng](https://github.com/hangtiancheng)
- Paper: _Swift: 基于强化学习的多信号融合自适应网络拥塞控制算法_ — see [`docs/thesis.tex`](docs/thesis.tex)

## Highlights

- **Multi-signal congestion awareness.** ECN negotiation/marking state, the
  congestion-avoidance state machine, congestion-event semantics, RTT vs. min-RTT
  and bytes-in-flight are organized into an 11-dimensional effective observation
  subspace (carried in a 15-element OpenGym container alongside socket/env routing
  metadata) and exposed to the Python agent over ZMQ.
- **RL-assisted adaptive fusion control.** A min-RTT-aware RTT-inflation ratio,
  the environment reward's offset from its own slow baseline, and consecutive-growth
  trends jointly tune a per-flow multiplicative factor α ∈ [0.85, 1.30]; cwnd
  converges toward the α × BDP target, where BDP comes from a windowed max-filter
  over a sliding-window delivery-rate estimate (BBR-style).
- **Stability and safety under uncertain signals.** Differentiated window-retention
  factors (loss ρ = 0.70, ECN ρ = 0.75, timeout ρ = 0.50), a consecutive-decrease
  floor, a post-decrease freeze window, queue-dwell-free slow-start threshold
  updates and hard window clamps.
- **Reproducible benchmark harness.** 36 link scenarios × 4 protocols
  (`TcpSwift`, `TcpNewReno`, `TcpCubic`, `TcpBbr`) × N seeds, with resume
  support, automated plotting and CSV reporting.

## Repository Layout

```
.
├── contrib/opengym/                  # ns3-gym (ZMQ + protobuf RL bridge)
│   ├── model/ns3gym/                 #   Python package installed into the venv
│   └── examples/
│       ├── swift-tcp/                # ★ Swift: algorithm, env, sim and agent
│       │   ├── tcp-swift.{h,cc}      #   TcpSwift congestion ops (C++)
│       │   ├── tcp-swift-env.{h,cc}  #   TcpSwiftEnv: 15-dim observation space
│       │   ├── sim.cc                #   dumbbell-topology simulation entry point
│       │   ├── tcp_swift.py          #   Python agent (v3.0 control law)
│       │   ├── tcp_base.py           #   shared event-based agent base class
│       │   └── test_swift.py         #   agent launcher
│       └── rl-tcp/                   # upstream RL-TCP example (baseline reference)
├── main.py                           # experiment runner / plotter / summarizer
├── Makefile                          # build, tcp, udp, gen, format, clean targets
├── ieg/                              # C++17 flowmonitor validator / encryptor / CSV tool
├── lark/                             # web dashboard for flowmonitor results (Vite + @lark.js/mvc)
├── docs/                             # thesis (tex/pdf), patent draft, plots
└── logs/                             # simulation artifacts, plots and summary CSVs
```

## Build

> System prerequisites (Debian/Ubuntu): ZMQ and Protocol Buffers for the
> ns3-gym bridge, plus [uv](https://docs.astral.sh/uv/) for the Python
> environment.

```bash
sudo apt update && sudo apt full-upgrade
sudo apt install libzmq5 libzmq3-dev libprotobuf-dev protobuf-compiler
sudo apt autoclean && sudo apt autoremove

uv sync --no-install-project
source .venv/bin/activate
./ns3 configure --enable-mtp --enable-examples
./ns3 build
uv pip install ./contrib/opengym/model/ns3gym
```

`make build` wraps the configure/build steps; `make clean` removes all build
artifacts and caches.

## Quick Start

Each RL run is a **two-process pair**: the ns-3 simulation listens on the
OpenGym ZMQ port and blocks until the Python agent connects, so launch the
simulator first and the agent second (in separate terminals).

```bash
# RL-TCP reference example
./ns3 run "rl-tcp --transport_prot=TcpRl" &> ./logs/rl-tcp-ns3.log
python ./contrib/opengym/examples/rl-tcp/test_tcp.py --start=0 &> ./logs/rl-tcp-agent.log

# Swift (RL agent driving TcpSwift)
./ns3 run "swift-tcp --transport_prot=TcpSwift" &> ./logs/swift-tcp-ns3.log
python ./contrib/opengym/examples/swift-tcp/test_swift.py --start=0 &> ./logs/swift-tcp-agent.log
python ./contrib/opengym/examples/swift-tcp/test_swift.py --start=0 --verbose &> ./logs/swift-tcp-agent.log

# Classic baselines run standalone (no agent needed)
./ns3 run "swift-tcp --transport_prot=TcpNewReno" &> ./logs/swift-tcp-new-reno.log
```

The `swift-tcp` binary accepts the full scenario parameter set:
`--transport_prot`, `--access_bandwidth`, `--bottleneck_bandwidth`,
`--access_delay`, `--bottleneck_delay`, `--duration`, `--nLeaf`, `--simSeed`,
`--enable_udp_burst`, `--openGymPort`, `--queue_disc_type` and `--prefix_name`
(see `contrib/opengym/examples/swift-tcp/sim.cc`).

## Benchmark Matrix

`main.py` drives the full evaluation. It defines **36 scenarios** across
11 categories — intra-rack and leaf-spine data center, oversubscription,
congestion gradients, cross-pod/cross-DC, RDMA-like ultra-low latency, mixed
and asymmetric traffic, bandwidth scaling, WiFi (802.11n/ac/ax/legacy),
cellular (LTE, 5G NR eMBB/edge) and WAN/satellite (metro, long-haul, LEO, GEO) —
and runs each against `TcpSwift`, `TcpNewReno`, `TcpCubic` and `TcpBbr`.
The optional `--udp` flag adds an 800 Mbps on/off UDP burst flow to stress the
protocols. Completed runs are skipped automatically (resume via existing
`.flowmonitor` files).

```bash
python main.py sim                          # all scenarios, pure TCP   -> logs/comparison
python main.py sim --udp                    # + UDP burst interference  -> logs/comparison-udp
python main.py sim --scenario wifi_ac       # single scenario
python main.py sim --num-seeds 10           # 10 RngRun repetitions per config
python main.py draw                         # plots -> logs/plots*
python main.py summary                      # CSV report -> logs/summary
```

Makefile shortcuts: `make tcp`, `make udp` (single quick run), `make gen`
(draw + summary), `make kill` (stop stray ns-3 processes).

## Results Dashboard

The [`lark/`](lark) app is a Vite + [@lark.js/mvc](https://github.com/hangtiancheng)
dashboard that renders the flowmonitor results (throughput, delay, jitter,
loss, per-flow breakdowns) from `logs/`. It is deployed to GitHub Pages at
<https://tianchenghang.github.io/ns3.40> via `.github/workflows/deploy.yml`.

```bash
pnpm install
pnpm --filter flowmonitor parse   # logs/*.flowmonitor -> lark/public/data
pnpm --filter flowmonitor dev     # local dev server
```

## ieg — Flowmonitor Tooling

[`ieg/`](ieg) is a standalone C++17 utility for post-processing simulation
output: validating `.flowmonitor`/XML files, encrypting/decrypting them and
exporting CSV.

```bash
cd ieg && cmake -B build && cmake --build build
./build/ieg validate ../logs     # also: encrypt | decrypt | csv
```

## Documentation Toolchain

For compiling the thesis and generating plots:

```bash
# Linux (Debian/Ubuntu)
sudo apt install -y texlive-full
# MacOS
brew install --cask mactex

# https://github.com/be5invis/Sarasa-Gothic
brew install gnuplot
```

## Development

```bash
make format    # clang-format (C/C++), ruff format (Python), shfmt (shell)
```

## License

Apache License 2.0 for the Swift additions (`contrib/opengym/examples/swift-tcp`,
`ieg`, tooling scripts); ns-3 itself is GPL-2.0-only — see
[LICENSE](LICENSE) and upstream ns-3 licensing for details.
