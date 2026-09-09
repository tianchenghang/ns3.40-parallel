---
name: update-ns3-docs
description: Guide an agent through the ordered refresh of the TcpSwift ns-3.40 / ns3-gym documentation artifacts, the CCF Class-A style conference paper at `docs/thesis.tex`, the NJUPT graduate thesis project at `docs/NJUPT_Professional_Thesis_draft1`, and the Chinese invention patent at `docs/patent.md`. Use this skill whenever the user asks to update, synchronize, rewrite, validate, or polish TcpSwift documentation, experiment tables, motivation, claims, patent language, or thesis sections based on ns-3.40 simulations, ns3-gym reinforcement learning, `contrib/opengym/examples/swift-tcp`, `Gemini.pdf`, or `logs/`. This skill must be used proactively for requests involving TcpSwift vs. TcpCubic/TcpNewReno/TcpBbr results, anomaly filtering in logs, or removal of the incorrect data-center-only motivation.
---

# update-ns3-docs

You are a senior computer-networking and congestion-control research assistant. Your job is to help an agent update the TcpSwift documentation artifacts in a rigorous, reproducible, and publication-ready manner.

The skill itself is written in professional English. The target artifacts may be Chinese academic or patent documents; preserve the language, tone, format, and local conventions of each artifact unless the user explicitly requests otherwise.

## Execution model

This skill uses a coordinated delegation model:

- The main agent performs the shared research pass, anomaly filtering, and directly updates the graduate thesis (`docs/NJUPT_Professional_Thesis_draft1`).
- The conference paper (`docs/thesis.tex`) is delegated to a subagent via the Agent tool.
- The invention patent (`docs/patent.md`) is delegated to a second subagent via the Agent tool, after the paper subagent completes and its output is verified.

This division exists because the graduate thesis is the most context-heavy artifact — it requires deep familiarity with the simulation code, experiment results, and iterative refinement that benefits from the main agent's accumulated context. The paper and patent are more bounded: they follow the same narrative constraints but need less iterative back-and-forth, making them well-suited to focused subagent execution.

## Project context

TcpSwift is a new TCP congestion-control protocol built on:

- ns-3 version 3.40: `https://www.nsnam.org/releases/ns-3-40/`
- ns-3.40 source tree: `https://gitlab.com/nsnam/ns-3-dev/-/tree/ns-3.40?ref_type=tags`
- ns3-gym reinforcement-learning integration: `https://github.com/tkn-tub/ns3-gym`

TcpSwift is benchmarked against:

- `TcpCubic`
- `TcpNewReno`
- `TcpBbr`

Important local inputs:

- TcpSwift implementation: `contrib/opengym/examples/swift-tcp`
- Primary reference paper: `Gemini.pdf`
- Experimental results: `logs/`
- Conference paper: `docs/thesis.tex`
- Chinese invention patent: `docs/patent.md`
- NJUPT graduate thesis project: `docs/NJUPT_Professional_Thesis_draft1`

All repository paths in this skill are relative to the repository root. Do not hard-code absolute local paths.

## Non-negotiable requirements

Apply these requirements before editing any artifact. Every subagent prompt must include these constraints verbatim.

### Correct the motivation

The current motivation in the conference paper, graduate thesis, and patent is wrong if it states or implies that TcpSwift is designed specifically for data-center networks.

TcpSwift must be framed as a congestion-control method for broader end-to-end network transmission scenarios, especially:

- long-distance transmission;
- heterogeneous terminal devices, including phones, laptops, desktops, and other endpoint classes;
- diverse access and path conditions where endpoints, links, RTTs, and traffic conditions vary.

Remove or rewrite claims such as:

- designed specifically for data-center networks;
- data-center-only congestion control;
- a protocol whose primary purpose is a data-center network deployment.

If a data-center-like scenario appears in experiments, describe it only as one evaluated network condition, not as the design motivation.

### Limit the core innovations to 2-3 points

Every artifact must present the same concise innovation story. Do not scatter many independent innovation claims across the documents.

Derive the final 2-3 innovations from the implementation, `Gemini.pdf`, and the simulation evidence. A strong candidate structure is:

1. multi-signal congestion-state perception for long-distance and heterogeneous endpoint scenarios;
2. ns3-gym-based reinforcement-learning decision support for adaptive congestion-window or sending-behavior adjustment;
3. stability and safety mechanisms that prevent aggressive degradation under uncertain RTT, loss, ECN, timeout, or bandwidth-delay conditions.

Treat the list above as a candidate framing, not a license to invent features. Verify each claim against `contrib/opengym/examples/swift-tcp` before using it.

### Preserve scientific integrity

- Never invent experimental data.
- Never promote a number unless it can be traced to `logs/` or a verified post-processing output.
- Prefer scenarios where TcpSwift performs better, but describe mixed or negative results honestly.
- If a result is anomalous, missing, contradictory, or untraceable, exclude it from headline claims and record the exclusion in `logs/error.txt`.
- Patent text must not expose concrete experimental data unless the user explicitly asks for data-bearing patent examples.

## Phase 1 — Shared research pass (main agent)

Before any artifact is updated, the main agent collects enough context to understand the protocol, simulation environment, and current documents. This context is later passed to subagents in summarized form.

Read or inspect these sources as needed:

1. ns-3.40 references:
   - the local ns-3 source tree;
   - `.github/skills/ns3.40/SKILL.md` if available;
   - `.github/skills/ns3.40/reference/ns-3-tutorial.md` when tutorial-level details are needed.
2. ns3-gym integration:
   - how observations, actions, rewards, and environment stepping are implemented;
   - how the Python training or evaluation scripts interact with the ns-3 simulation.
3. TcpSwift code under `contrib/opengym/examples/swift-tcp`:
   - scenario driver, usually `sim.cc`;
   - congestion-control implementation, commonly `tcp-swift.h` and `tcp-swift.cc`;
   - ns3-gym environment files, commonly `tcp-swift-env.h` and `tcp-swift-env.cc`;
   - Python helpers such as `tcp_base.py`, `tcp_swift.py`, and `test_swift.py` when present.
4. Experiments under `logs/`:
   - summary CSV files;
   - raw FlowMonitor XML files;
   - generated figures;
   - batch summaries or per-run dumps.
5. Primary reference material:
   - `Gemini.pdf`;
   - the current `docs/thesis.tex`.
6. Target artifacts:
   - `docs/thesis.tex`;
   - `docs/NJUPT_Professional_Thesis_draft1` main file, chapters, figures, and bibliography files;
   - `docs/patent.md`.

Do not assume file names beyond the paths listed above. If the local tree differs, inspect it and adapt.

After the research pass, prepare a concise research brief (in working memory or notes) that captures:

- the verified 2-3 innovation points with code-level evidence;
- the corrected motivation framing;
- key simulation parameters and scenario configurations;
- which protocols are compared and under what conditions.

This brief is passed to subagents so they do not need to re-read the entire codebase.

## Phase 2 — Data hygiene and anomaly filtering (main agent)

Run anomaly filtering before any artifact update. Reuse the same cleaned dataset across all three artifacts, but do not duplicate existing `logs/error.txt` entries for the same anomaly.

### What to inspect

Prioritize these files when present:

- `logs/plots/summary.csv`
- `logs/plots-udp/summary.csv`
- `logs/summary/results_*.csv`
- `logs/comparison/*.flowmonitor`
- `logs/comparison-udp/*.flowmonitor`
- generated figures under `logs/plots*/`

### Anomaly criteria

Flag a data point or scenario as anomalous when any of the following applies:

- throughput is missing, negative, zero when traffic should exist, or exceeds the configured bottleneck in an impossible way;
- delay is missing, non-positive, `NaN`, infinite, or close to the whole simulation duration in a way that invalidates the metric;
- loss rate is missing, `NaN`, negative, or greater than 1 when represented as a fraction;
- Jain fairness is outside `[0, 1]`;
- a `(scenario, protocol)` pair is missing for one of the compared protocols;
- a paired no-UDP/UDP-burst comparison is incomplete;
- the corresponding FlowMonitor file is missing, empty, malformed, or inconsistent with the summary CSV;
- duplicate rows disagree on key metrics without a documented reason;
- the scenario configuration cannot be traced back to the simulation driver or batch script.

### Recording anomalies

Append anomalies to `logs/error.txt`. Preserve existing content.

Use a deterministic line format:

```text
<ISO-8601 timestamp> | <source path> | <scenario> | <protocol> | <reason> | <excluded metrics>
```

If the same anomaly is already recorded, do not append a duplicate. If new evidence changes the reason, append a clarifying line rather than modifying historical records.

### Cleaned view

After filtering:

- build a cleaned KPI view for the remaining updates;
- identify scenarios where TcpSwift clearly outperforms at least one baseline on throughput, delay, loss, fairness, robustness, or stability;
- identify scenarios where TcpSwift does not win or has mixed behavior;
- use winning or representative scenarios for headline narrative;
- keep mixed scenarios in extended discussion only when they improve scientific honesty.

The cleaned KPI view is passed to subagents alongside the research brief.

## Phase 3 — Parallel execution

After Phases 1-2 are complete, launch the conference-paper subagent and begin the graduate-thesis work in parallel.

### 3a. Spawn the conference-paper subagent

Use the Agent tool to spawn a subagent for `docs/thesis.tex`. The subagent prompt must include:

1. The non-negotiable requirements (motivation correction, 2-3 innovations, scientific integrity) — copied verbatim from this skill.
2. The research brief from Phase 1.
3. The cleaned KPI view from Phase 2.
4. The full conference-paper instructions below.

#### Conference-paper subagent instructions

Include the following in the subagent prompt:

---

Target artifact: `docs/thesis.tex`.

Target standard: a precise, rigorous, and well-scoped Chinese computer-science conference paper suitable for submission to a China Computer Federation Class-A venue.

Required actions:

1. Read `docs/thesis.tex` before editing.
2. Read `Gemini.pdf` enough to understand the comparison point, algorithmic framing, and terminology that may influence TcpSwift's presentation.
3. Inspect `contrib/opengym/examples/swift-tcp` for any claims that need code-level verification.
4. Remove or rewrite the incorrect data-center-only motivation throughout the paper.
5. Reframe the motivation around long-distance transmission and heterogeneous terminal devices.
6. Consolidate the core innovations into 2-3 points and use them consistently in the abstract, introduction, method, and conclusion.
7. Update the experimental section from the cleaned KPI view provided:
   - throughput;
   - delay;
   - loss;
   - fairness;
   - robustness under UDP burst or other stress conditions when available;
   - representative scenarios where TcpSwift is better than one or more baselines.
8. Prefer TcpSwift-favorable experiment groups in headline tables and narrative, while keeping claims truthful and traceable.
9. Keep LaTeX layout safe for conference format:
   - avoid over-wide tables;
   - reuse existing packages when possible;
   - preserve labels and references unless a rename is necessary and all references are updated.
10. Use precise academic language. Avoid exaggerated claims, marketing phrasing, and unsupported generalization.

The paper should answer:

- What network problem does TcpSwift address outside a data-center-only framing?
- Why do long-distance transmission and heterogeneous endpoints make congestion control difficult?
- How does TcpSwift use ns3-gym reinforcement learning and ns-3.40 simulation evidence?
- What are the 2-3 core technical contributions?
- Under which scenarios does TcpSwift outperform TcpCubic, TcpNewReno, and/or TcpBbr?
- Which scenarios are mixed, and what do they imply for future work?

Validation before completion:

- search the edited paper for data-center-only motivation and remove it;
- verify all quoted numbers against the cleaned results provided;
- verify that every headline table uses non-anomalous data;
- verify that the contribution list has no more than 3 core innovation points;
- run `python docs/build.py zh` when feasible; otherwise explain why it was not run.

---

#### Subagent configuration

- Use `mode: "bypassPermissions"` or an appropriate mode so the subagent can edit files and run build commands.
- Set a descriptive name such as `"paper-writer"` for reference.
- Run this subagent in the foreground if you need its output before spawning the patent subagent; run it in the background if you want to work on the graduate thesis simultaneously and check results later.

Recommended approach: run the paper subagent in the background while the main agent works on the graduate thesis. Check and verify the paper subagent's output before spawning the patent subagent.

### 3b. Main agent updates the graduate thesis

While the paper subagent runs, the main agent directly updates `docs/NJUPT_Professional_Thesis_draft1`.

Target standard: a coherent, detailed, and professionally written graduate thesis suitable for an excellent NJUPT graduate-thesis evaluation.

#### Required actions

1. Locate the thesis entry file and chapter structure before editing. Common files may include a main `.tex` file and chapter files under a `chapters/` directory.
2. Read the chapters that discuss background, motivation, method design, experiment setup, evaluation, and conclusion.
3. Apply the corrected motivation:
   - long-distance transmission;
   - heterogeneous terminal devices;
   - diverse network access and path conditions.
4. Remove data-center-only positioning throughout the thesis.
5. Keep the same 2-3 core innovations as the conference paper, but explain them with thesis-level depth.
6. Verify anomaly filtering is complete before propagating experimental claims. Append only newly discovered anomalies to `logs/error.txt`.
7. Synchronize all experiment tables, figure references, scenario descriptions, and conclusion claims with the cleaned KPI view.
8. Expand explanations where appropriate:
   - ns-3.40 simulation model and assumptions;
   - ns3-gym observation/action/reward loop;
   - TcpSwift design rationale;
   - comparison protocols;
   - experiment scenarios and metrics;
   - limitations and failure modes.
9. Preserve the thesis template, class file, bibliography style, figure paths, labels, and cross-references.
10. Do not introduce unnecessary packages or template-level changes.

#### Thesis-specific guidance

The thesis should be more explanatory than the conference paper. It should provide enough detail for a committee reader to understand:

- why the problem matters;
- how TcpSwift is implemented in ns-3.40;
- how reinforcement learning is connected through ns3-gym;
- why the selected state/action/reward design is reasonable;
- how scenarios map to long-distance and heterogeneous endpoint conditions;
- how experimental evidence supports the selected 2-3 innovations;
- what limitations remain.

#### Graduate-thesis validation

Before leaving this phase:

- search the thesis project for data-center-only motivation and remove it;
- verify that the contribution list remains aligned with the conference paper;
- verify that all tables and figures are traceable to non-anomalous results;
- verify that references, labels, and figure paths are still valid;
- run `python docs/build.py njupt` when feasible; otherwise explain why it was not run.

## Phase 4 — Spawn the patent subagent

After the paper subagent completes and its output is verified (and ideally after the graduate thesis is also in good shape), spawn a second subagent for `docs/patent.md`.

The patent subagent runs after the paper because the patent translates the stabilized scientific narrative into legal-technical language. Running it earlier risks divergence.

### Patent subagent prompt contents

Include in the subagent prompt:

1. The non-negotiable requirements — copied verbatim.
2. The research brief and cleaned KPI view (for technical accuracy, though the patent does not expose numbers).
3. A summary of the final 2-3 innovations as expressed in the completed paper and thesis.
4. The full patent instructions below.

#### Patent subagent instructions

Include the following in the subagent prompt:

---

Target artifact: `docs/patent.md`.

Target standard: a professional Chinese mainland invention patent draft with clear technical problem, technical solution, beneficial effects, embodiments, and claims.

Required actions:

1. Read `docs/patent.md` before editing.
2. Reuse the corrected technical story from the paper and thesis, but translate it into patent language rather than academic paper language.
3. Do not identify the protocol as Swift or TcpSwift in the patent body unless the user explicitly requests it.
4. Use neutral phrasing such as:
   - the proposed congestion-control protocol;
   - the proposed TCP congestion-control method;
   - the congestion-control method provided by the present invention.
5. Do not expose concrete experimental data in the patent. Describe beneficial effects qualitatively, such as improved adaptability, improved transmission stability, reduced congestion response lag, or better robustness under heterogeneous endpoint and long-distance transmission conditions.
6. Remove data-center-only motivation. If a data-center term appears, rewrite it into a broader network-transmission context unless it is strictly part of a background comparison and not the invention's design target.
7. Keep the core invention points limited to the same 2-3 ideas used in the academic artifacts, but express them as claimable technical features.
8. Ensure the claims are layered:
   - one independent claim covering the overall congestion-control method;
   - dependent claims for state acquisition, reinforcement-learning decision logic, congestion-window adjustment, stability safeguards, and implementation details verified in the code.
9. Keep the patent concise, formal, and defensible. Avoid academic citations, unnecessary experiment tables, and brand-like terminology.

The patent should answer:

- What technical problem is solved?
- What technical means solve it?
- How does the method acquire congestion-state information?
- How does the method produce or apply a control decision?
- How does the method improve robustness for long-distance and heterogeneous endpoint transmission?
- Which parts should be claimed broadly, and which parts should be dependent refinements?

Validation before completion:

- search `docs/patent.md` for `Swift`, `TcpSwift`, and similar brand identifiers and remove them;
- search for concrete experiment numbers and remove them unless explicitly requested;
- search for data-center-only positioning and remove it;
- verify that the claims reflect no more than 2-3 central invention ideas;
- verify Markdown formatting and heading structure.

---

#### Subagent configuration

- Same mode considerations as the paper subagent.
- Set a descriptive name such as `"patent-writer"`.
- This subagent can run in the foreground (the main agent is likely done with the thesis by now) or in the background if there is other work to do.

## Phase 5 — Cross-artifact verification (main agent)

After all three artifacts are updated, the main agent performs a final consistency check.

### Verify subagent outputs

For each subagent-produced artifact:

1. Read the modified file and confirm the non-negotiable requirements are satisfied.
2. Check that the 2-3 innovation points match across all three artifacts in substance (wording may differ by register — academic vs. patent — but the technical content must align).
3. Confirm no data-center-only motivation survives in any artifact.
4. Confirm the paper's experimental numbers trace to the cleaned KPI view.
5. Confirm the patent does not expose the Swift/TcpSwift name or concrete data (unless the user explicitly requested otherwise).

If a subagent's output fails verification, either fix the issue directly or send a follow-up message to the subagent with specific corrections.

### Final verification checklist

Before reporting completion, verify:

1. The conference paper, graduate thesis, and patent no longer claim TcpSwift is designed specifically for data-center networks.
2. The motivation consistently emphasizes long-distance transmission and heterogeneous terminal devices.
3. The core innovations are limited to 2-3 points and are consistent across artifacts.
4. Conference-paper and graduate-thesis numbers are traceable to cleaned `logs/` data.
5. Anomalies are appended to `logs/error.txt` without deleting historical records.
6. TcpSwift-favorable experiment groups are highlighted without fabricating or overstating results.
7. The patent does not expose the Swift/TcpSwift name unless explicitly requested.
8. The patent does not expose concrete experimental data unless explicitly requested.
9. Build or validation commands were run where feasible, and any skipped validation is explained.
10. The final response lists changed files, anomaly count, promoted scenarios, validation commands, and remaining assumptions.

## Changelog handling

If matching changelog files already exist, update them. Do not create new changelog files unless the user asks or the repository already clearly uses them for this workflow.

Common changelog files may include:

- `CHANGELOG_thesis.md` for `docs/thesis.tex`;
- `CHANGELOG.md` for the graduate thesis or project-level documentation;
- `CHANGELOG_patent.md` for `docs/patent.md`.

When updating changelogs:

- use the artifact's existing language and style;
- record the date;
- summarize motivation correction, contribution consolidation, anomaly filtering, result updates, and validation;
- include the number of newly recorded anomalies in `logs/error.txt`;
- cross-reference related artifact updates when appropriate.

## Guardrails

- Do not commit automatically.
- Do not delete raw logs or overwrite `logs/error.txt`.
- Do not fabricate missing results.
- Do not silently ignore anomalous or contradictory data.
- Do not introduce a data-center-only motivation.
- Do not expand the innovation list beyond 3 core points.
- Do not rename LaTeX labels unless all references are updated.
- Do not change thesis or patent templates unnecessarily.
- Do not use absolute local paths in deliverables.
- Do not add emojis or informal language to repository documentation.
