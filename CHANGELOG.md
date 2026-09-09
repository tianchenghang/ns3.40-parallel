# Changelog

All notable changes to the swift-tcp example and its experiment tooling.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions refer
to the TcpSwift agent (`contrib/opengym/examples/swift-tcp/tcp_swift.py`).

## [Unreleased] - Figure pipeline rebuilt on the audited dataset (2026-08-21)

### Added

- `docs/plots/main.py` (rewritten): the publication-figure pipeline now
  derives every number from the raw `.flowmonitor` artifacts with
  forward-flow-only metrics (audit rule A), regenerates
  `logs/summary/kpi_forward.csv` (verified byte-identical to the committed
  version, closing its provenance gap), applies exclusion rules B/C/D
  (27 revision-mixed groups, 7 whole-group old-revision runs, 4 duplicate
  configs, 4 degenerate BBR points), asserts the kept sets equal the
  published S1-S19 / 15-scenario lists, spot-checks values against the
  thesis tables, and emits `figure_manifest.json` with per-rule exclusion
  records. Previous figures were built from the direction-mixed summary
  CSVs with per-scenario averaging across both `sim.cc` revisions and a
  Jain index computed over data + ACK flows; all 13 stale figures were
  removed.
- New audited figures `fig01`-`fig05` (goodput, delay vs base-OWD,
  utilization-delay trade-off, UDP-burst robustness, audit funnel) plus the
  v3.0.0 architecture schematic `fig06_architecture_zh` and the patent
  workflow `fig07_workflow_zh`.
- `docs/thesis.tex`: five figures embedded (architecture, audit funnel,
  goodput, delay, UDP burst); the scenario table gained the canonical
  S1-S19 IDs; rule B wording now distinguishes the 7 whole-group
  old-revision exclusions. Builds to 14 pages.
- `docs/NJUPT_Professional_Thesis_draft1/chapters/chapter4.tex`: five data
  figures embedded (audit funnel, goodput, delay, trade-off scatter,
  UDP burst), each with an interpretive paragraph; rule B wording updated
  identically.

### Removed

- `docs/mermaid.js`, `docs/workflow.mermaid`, `docs/workflow.png`: the
  mermaid rendering path (broken since `mmdc` was never installed) is
  replaced by `plot_workflow` in `docs/plots/main.py`; `docs/patent.md`
  now references `docs/plots/fig07_workflow_zh.png` as 图1.

## [Unreleased] - Documentation refresh (2026-08-20)

Refresh of the documentation artifacts against the v3.0.0 implementation and a
re-audited experiment dataset. No source code was changed by this entry.

### Added

- `logs/summary/kpi_forward.csv`: derived KPI view recomputed from all 288
  `.flowmonitor` artifacts using **forward-direction TCP flows only**
  (`10.1.x -> 10.2.x`), with a Jain fairness column and a `Source` column
  pointing at the originating artifact. This supersedes the throughput and
  delay columns of `logs/plots/summary.csv` and `logs/plots-udp/summary.csv`,
  which aggregate over all TCP flows and therefore mix the reverse ACK stream
  into both metrics: the reported delay is approximately
  `(data_delay + one_way_propagation) / 2` and the throughput is inflated by
  roughly the 1.7% ACK rate.

### Changed

- `logs/error.txt`: appended an `AUDIT PASS 2026-08-20` block with 47 new
  anomaly records under six rules - (A) the metric-definition defect above,
  (B) 27 `(setting, scenario)` groups that mix two `sim.cc` revisions across
  protocols (sink port 5000 vs 50000), (C) duplicate configurations
  (`dc_oversub_10to1` = `congested_heavy`, `satellite_leo` = `lte_good`, with
  byte-identical artifacts), (D) the degenerate TcpBbr baseline on
  microsecond-RTT high-rate paths, (E) the `TcpLark` label provenance, and
  (F) the pre-v3.0.0 revision boundary. A later clarification records the
  maintainer's `TcpLark -> TcpSwift` artifact rename and confirms every KPI
  column is byte-identical after regeneration. Historical records were not
  modified. Clean sets: 19 scenarios (TCP-only) and 15 (UDP-burst).
- `docs/NJUPT_Professional_Thesis_draft1/`: algorithm descriptions in
  chapters 3, 5 and 6 aligned with v3.0.0 (time-window delivery rate,
  three-way classification inside the window-reduction callback,
  baseline-relative reward adaptation, freeze counter-reset ordering, stale
  action invalidation, RED/ECN signal path, MSS 1440). Chapter 4 rebuilt from
  the clean KPI view; all 450 table cells verified programmatically against
  the CSV with zero mismatches.
- `docs/thesis.tex`: same alignment and the same data source, with the
  contribution list consolidated to three points.
- `docs/patent.md`: technical description corrected to the v3.0.0 algorithm
  (two-stage time-window BDP estimation, baseline-relative reward adaptation,
  three-way classification in the window-reduction callback, `min(cwnd, BDP)`
  ssthresh anchoring, `max(4*BDP, 200*MSS)` window bound, freeze counter-reset
  ordering). Brand identifiers, simulator/tooling references and all
  quantitative results were removed so the draft stays implementation-neutral
  and data-free; beneficial effects are stated qualitatively. Claim set is 19
  claims covering the same three core ideas plus system, storage-medium and
  device claims.
- **Corrected causal attribution.** The archived runs used
  `PfifoFastQueueDisc` with ECN enabled only for TcpSwift, so the ECN branch
  and its `beta_ecn = 0.75` never fired. Every "zero loss thanks to ECN"
  claim was rewritten to credit the mechanism that was actually active: the
  window bounded by `alpha * BDP` and `max(4*BDP, 200*MSS)`, the drain-by-half
  above target, the consecutive-decrease guard and the post-decrease freeze.
  The documents now state that zero loss and the queueing-delay penalty are
  two faces of the same behaviour - the window parks at a level that fills but
  does not overflow the buffer - and that evaluating the ECN path requires the
  pending rerun.
- **Removed all LEO-satellite claims**, because the only scenario carrying
  that label was configured as a 50 Mbps / 30 ms one-way link and is a
  byte-identical duplicate of `lte_good`. GEO satellite claims are unaffected.
- Disclosed that the archived dataset has **one run per
  `(scenario, protocol, setting)`** with no `_s<seed>` suffix, so no
  cross-seed confidence intervals are reported.

## [3.0.0] - 2026-08-20

Fixes for the findings of the 2026-08-20 code review (C1-C5 plus secondary
issues). All quantitative results recorded before this version (including the
tables in `docs/thesis.tex` and `logs/summary/results_20260611_100706.csv`)
were produced by the pre-fix algorithm and configuration and must be
regenerated with a full experiment-matrix rerun.

### Fixed

- **C1 (critical) - delivery-rate estimator** (`tcp_swift.py`):
  the per-ACK formula `segmentsAcked * segSize / lastRtt` under-estimated
  bandwidth by roughly the number of ACKs per RTT, collapsing the BDP
  estimate; cwnd then pinned at the `200*MSS` safety floor, capping WAN
  throughput at `200*MSS/RTT` (wan_longhaul 45 Mbps and cross_dc_wan
  237 Mbps both matched that ceiling exactly). Delivery rate is now
  cumulative ACKed bytes over a sliding time window
  (`min(max(2*min_rtt, 5 ms), 1 s)`). Verified with a synthetic ACK-stream
  harness (1 Gbps / 52 ms): BDP estimate 6.50 MB vs true 6.50 MB, steady
  throughput ~1000 Mbps (previously ~45 Mbps).
  Commit `68b9d77`.
- **C2 - dead ECN pathway** (`sim.cc`, `main.py`): every experiment ran on
  `PfifoFastQueueDisc`, which never marks CE, so beta_ecn, ECN rewards, and
  the ECN-based narrative were never exercised; ECN was also enabled only
  for TcpSwift, biasing baselines. The bottleneck now defaults to
  `RedQueueDisc` marking from 30% of queue length (MinTh=0.3q, MaxTh=0.9q,
  UseEcn), ECN is enabled for **all** TCP variants, and the runner records
  `--queue_disc_type` on the command line. Commit `96301b3`.
- **C3 - ECN misclassification** (`tcp_swift.py`): ECE/CWR-triggered
  `GetSsThresh` callbacks were classified as generic loss (beta=0.70);
  they now receive the ECN response (beta=0.75). Commit `6ed0a8c`.
- **C4 - reward adaptation carried no signal** (`tcp_swift.py`,
  `tcp-swift-env.cc` comment): the per-ACK reward is >= +0.5 on nearly every
  ACK, so the fixed `ema > 0.5` threshold was a constant +0.01 ratchet
  toward `alpha_max`. Alpha now moves only when the fast reward EMA
  (eta=0.15) departs from its slow baseline EMA (eta_b=0.02) by a dynamic
  margin, with an asymmetric down-margin for loss/timeout spikes.
  Commit `615e7a2`.
- **C5 - experiment-matrix integrity** (`main.py`, `sim.cc`):
  - `satellite_leo` duplicated `lte_good` parameter-for-parameter (their
    result rows were byte-identical); it is now a Starlink-like LEO link
    (500M/150M, 2ms/25ms).
  - `congested_heavy` duplicated `dc_oversub_10to1`; it is now a 20:1
    oversubscription point (10G/500M).
  - `sim --num-seeds N` runs N RngRun repetitions per configuration;
    artifacts carry an `_s<seed>` suffix and `summary`/`draw` average
    across seeds (old seedless artifacts still parse). The summary CSV
    gains a `Seeds` column.
  - `sim.cc` now logs `AccessBW`/`BottleneckBW` (the CSV columns were
    always `N/A` because those lines never existed) and TCP
    `AggregateThroughput`/`AggregateLossRate`; the summary previously
    recorded only the first flow's throughput.
    Commit `a40c294`.
- **Secondary hardening** (`tcp-swift-env.cc`, `tcp-swift.h`,
  `tcp-swift-env.h`, `tcp-swift.cc`, `sim.cc`, `tcp_swift.py`):
  - Deferred cwnd cached in `GetSsThresh` is discarded on CA_LOSS (RTO)
    instead of overriding the stack's slow-start restart later.
  - The consecutive-decrease counter is no longer reset during the
    post-decrease freeze, so the `D_max` floor works as documented.
  - The advertised `error_p` parameter is wired to a `RateErrorModel` on
    the bottleneck (it was parsed but ignored).
  - Removed the dead `envTimeStep` option and the commented-out defaults
    for nonexistent `TcpSwift::Reward/Penalty` attributes.
  - Flow i starts at `start_time*(i+1)`, so flow 0 no longer starts at
    t=0 simultaneously with the sinks.
  - Leftover `TCP_SWIFT_*` include guards renamed to `TCP_SWIFT_*`; log
    components renamed `TcpSwift`/`TcpSwiftEnv`.
    Commit `b6d2680`.

### Documentation

- `docs/thesis.tex` algorithm descriptions aligned with the v3
  implementation (time-window delivery rate, ECN classification, ssthresh
  formula, baseline-relative reward adaptation, MSS=1440, per-agent reward
  EMA, seed policy), and the evidence-boundary note now states that all
  quantitative tables predate the v3 fixes. Commit `cae8cb1`.

### Validation

- `python3 -m py_compile` on `tcp_swift.py` and `main.py`.
- Synthetic ACK-stream harness (no ns-3 required) confirming the C1 fix.
- Regex/backward-compatibility check of run-name parsing and a `summary`
  smoke run over the existing pre-fix logs (288 grouped records).
- C++ changes are review-verified only; compile with `./ns3 build swift-tcp`
  on the Linux experiment machine (this repo's macOS host does not build).

### Rerun checklist

1. `./ns3 configure --enable-mtp --enable-examples && ./ns3 build`
2. `python main.py sim --num-seeds 10`
3. `python main.py sim --udp --num-seeds 10`
4. `python main.py summary && python main.py draw`
5. Refresh `docs/thesis.tex` tables from the new `summary.csv` files.
