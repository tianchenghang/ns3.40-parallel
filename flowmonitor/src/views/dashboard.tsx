import { LitElement, customElement, state } from "@swifty.js/lit-jsx";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import gsap from "gsap";
import {
  loadIndex,
  ALGO_COLORS,
  ALGO_LABELS,
  formatThroughput,
  formatDelay,
  formatLoss,
  scenarioCategory,
} from "../lib/data";
import { icons, categoryIcons } from "../lib/icons";
import type { ScenarioIndex } from "../lib/data";

const base = import.meta.env.BASE_URL.replace(/\/+$/, "");

interface AlgoPill {
  algo: string;
  label: string;
  color: string;
  bg: string;
  borderColor: string;
  active: boolean;
}

interface AlgoDot {
  color: string;
  label: string;
}

interface CardVM {
  scenario: string;
  dataset: string;
  displayName: string;
  category: string;
  categoryIcon: string;
  hasSummary: boolean;
  throughputText: string;
  throughputWidth: number;
  delayText: string;
  delayWidth: number;
  lossText: string;
  lossWidth: number;
  algoColor: string;
  algoDots: AlgoDot[];
  algoCountText: string;
}

function pillClass(active: boolean): string {
  return active
    ? "bg-accent/10 text-accent-soft border border-accent/30"
    : "bg-surface-2 text-gray-500 border border-transparent hover:text-gray-700";
}

@customElement("fm-dashboard")
export class Dashboard extends LitElement {
  @state() private scenarios: ScenarioIndex[] = [];
  @state() private filter = "All";
  @state() private datasetName = "All";
  @state() private loading = true;
  @state() private bestAlgo = "TcpSwift";
  @state() private algos: string[] = [];

  protected override createRenderRoot() {
    return this;
  }

  override firstUpdated() {
    gsap.fromTo(
      this.querySelector(".dash-header"),
      { opacity: 0, y: -20 },
      { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" },
    );
    gsap.fromTo(
      this.querySelectorAll(".stat-ring"),
      { scale: 0.8, opacity: 0 },
      {
        scale: 1,
        opacity: 1,
        duration: 0.5,
        stagger: 0.1,
        ease: "back.out(1.7)",
        delay: 0.2,
      },
    );
    (async () => {
      const data = await loadIndex();
      this.scenarios = data.scenarios;
      this.algos = data.algorithms;
      this.loading = false;
    })();
  }

  protected override updated() {
    gsap.fromTo(
      this.querySelectorAll(".scenario-card"),
      { opacity: 0, y: 24, scale: 0.97 },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.45,
        stagger: 0.04,
        ease: "power2.out",
      },
    );
  }

  private get categories(): string[] {
    return [
      ...new Set(this.scenarios.map((s) => scenarioCategory(s.scenario))),
    ].sort();
  }

  private get datasets(): string[] {
    return [...new Set(this.scenarios.map((s) => s.dataset))].sort();
  }

  private get algoPills(): AlgoPill[] {
    const best = this.bestAlgo;
    return this.algos.map((algo) => ({
      algo,
      label: ALGO_LABELS[algo] || algo,
      color: ALGO_COLORS[algo] || "#888",
      bg: best === algo ? `${ALGO_COLORS[algo]}22` : "transparent",
      borderColor: best === algo ? `${ALGO_COLORS[algo]}55` : "transparent",
      active: best === algo,
    }));
  }

  private get cards(): CardVM[] {
    const f = this.filter;
    const ds = this.datasetName;
    const best = this.bestAlgo;
    let list = this.scenarios;
    if (f !== "All") {
      list = list.filter((s) => scenarioCategory(s.scenario) === f);
    }
    if (ds !== "All") {
      list = list.filter((s) => s.dataset === ds);
    }
    return list.map((s) => {
      const sum = s.summaries[best];
      const hasSummary = !!sum;
      const cat = scenarioCategory(s.scenario);
      return {
        scenario: s.scenario,
        dataset: s.dataset,
        displayName: s.scenario.replace(/_/g, " "),
        category: cat,
        categoryIcon: categoryIcons[cat] || categoryIcons["Mixed"],
        hasSummary,
        throughputText: hasSummary ? formatThroughput(sum.throughputMbps) : "",
        throughputWidth: hasSummary
          ? Math.min(100, (sum.throughputMbps / 100000) * 100)
          : 0,
        delayText: hasSummary ? formatDelay(sum.avgDelayUs) : "",
        delayWidth: hasSummary
          ? Math.min(100, (sum.avgDelayUs / 1000) * 100)
          : 0,
        lossText: hasSummary ? formatLoss(sum.lossRate) : "",
        lossWidth: hasSummary ? Math.min(100, sum.lossRate * 10000) : 0,
        algoColor: ALGO_COLORS[best] || "#888",
        algoDots: s.algorithms.map((a) => ({
          color: ALGO_COLORS[a] || "#888",
          label: ALGO_LABELS[a] || a,
        })),
        algoCountText: `${s.algorithms.length} algorithms`,
      };
    });
  }

  protected override render() {
    const cards = this.cards;
    return (
      <div class="min-h-screen">
        <header class="dash-header sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-2xl">
          <div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div class="flex items-center gap-3">
              <div class="from-accent flex h-9 w-9 items-center justify-center rounded-xl bg-linear-to-br to-cyan-400 text-white">
                {unsafeHTML(icons.activity)}
              </div>
              <div>
                <h1 class="text-base font-semibold tracking-tight text-gray-900">
                  FlowMonitor
                </h1>
                <p class="font-mono text-[11px] text-gray-400">
                  ns-3.40 TCP Congestion Control Comparison
                </p>
              </div>
            </div>
            <div class="flex items-center gap-6">
              <div class="stat-ring text-center">
                <div class="font-mono text-lg font-semibold text-gray-900">
                  {cards.length}
                </div>
                <div class="text-[10px] tracking-wider text-gray-400 uppercase">
                  Scenarios
                </div>
              </div>
              <div class="stat-ring text-center">
                <div class="text-algo-swift font-mono text-lg font-semibold">
                  {this.algos.length}
                </div>
                <div class="text-[10px] tracking-wider text-gray-400 uppercase">
                  Algorithms
                </div>
              </div>
              <div class="stat-ring text-center">
                <div class="text-algo-bbr font-mono text-lg font-semibold">
                  {this.datasets.length}
                </div>
                <div class="text-[10px] tracking-wider text-gray-400 uppercase">
                  Datasets
                </div>
              </div>
            </div>
          </div>
        </header>

        <main class="mx-auto max-w-7xl px-6 py-8">
          {this.loading && (
            <div class="flex items-center justify-center py-32">
              <div class="flex flex-col items-center gap-4">
                <div class="border-accent/30 border-t-accent h-10 w-10 animate-spin rounded-full border-2"></div>
                <p class="text-sm text-gray-400">Loading flow data...</p>
              </div>
            </div>
          )}
          {!this.loading && (
            <div>
              <div class="mb-8 space-y-4">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="mr-1 text-xs tracking-wider text-gray-400 uppercase">
                    Category
                  </span>
                  <button
                    class={`inline-flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium tracking-wide ${pillClass(this.filter === "All")}`}
                    onClick={() => {
                      this.filter = "All";
                    }}
                  >
                    All
                  </button>
                  {this.categories.map((cat) => (
                    <button
                      class={`inline-flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium tracking-wide ${pillClass(this.filter === cat)}`}
                      onClick={() => {
                        this.filter = cat;
                      }}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                <div class="flex flex-wrap items-center justify-between gap-4">
                  <div class="flex items-center gap-2">
                    <span class="mr-1 text-xs tracking-wider text-gray-400 uppercase">
                      Dataset
                    </span>
                    <button
                      class={`inline-flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium tracking-wide ${pillClass(this.datasetName === "All")}`}
                      onClick={() => {
                        this.datasetName = "All";
                      }}
                    >
                      All
                    </button>
                    {this.datasets.map((ds) => (
                      <button
                        class={`inline-flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium tracking-wide ${pillClass(this.datasetName === ds)}`}
                        onClick={() => {
                          this.datasetName = ds;
                        }}
                      >
                        {ds}
                      </button>
                    ))}
                  </div>

                  <div class="flex items-center gap-2">
                    <span class="mr-1 text-xs tracking-wider text-gray-400 uppercase">
                      Metric by
                    </span>
                    {this.algoPills.map((pill) => (
                      <button
                        class={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium tracking-wide ${
                          !pill.active
                            ? "border-transparent opacity-50 hover:opacity-100"
                            : ""
                        }`}
                        style={{
                          background: pill.bg,
                          color: pill.color,
                          ...(pill.active
                            ? { borderColor: pill.borderColor }
                            : {}),
                        }}
                        onClick={() => {
                          this.bestAlgo = pill.algo;
                        }}
                      >
                        <span
                          class="h-2 w-2 rounded-full"
                          style={{ background: pill.color }}
                        ></span>
                        {pill.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {cards.map((c) => (
                  <a
                    href={`${base}/scenario?scenario=${encodeURIComponent(c.scenario)}&dataset=${encodeURIComponent(c.dataset)}`}
                    class="scenario-card hover:border-accent/40 group cursor-pointer rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <div class="mb-4 flex items-start justify-between">
                      <div class="flex items-start gap-2.5">
                        <div class="bg-surface-2 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-gray-400">
                          {unsafeHTML(c.categoryIcon)}
                        </div>
                        <div>
                          <h3 class="font-mono text-sm font-semibold text-gray-800 transition-colors group-hover:text-gray-900">
                            {c.displayName}
                          </h3>
                          <span class="text-[10px] tracking-wider text-gray-400 uppercase">
                            {c.category} / {c.dataset}
                          </span>
                        </div>
                      </div>
                      <div class="bg-surface-2 group-hover:text-accent flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 transition-colors">
                        {unsafeHTML(icons.arrowUpRight)}
                      </div>
                    </div>

                    {c.hasSummary && (
                      <div class="space-y-3">
                        <div>
                          <div class="mb-1 flex justify-between text-[11px]">
                            <span class="text-gray-400">Throughput</span>
                            <span class="font-mono text-gray-700">
                              {c.throughputText}
                            </span>
                          </div>
                          <div class="bg-surface-3 h-1.5 overflow-hidden rounded-full">
                            <div
                              class="h-full rounded-full transition-all duration-700"
                              style={{
                                width: `${c.throughputWidth}%`,
                                background: c.algoColor,
                              }}
                            ></div>
                          </div>
                        </div>
                        <div>
                          <div class="mb-1 flex justify-between text-[11px]">
                            <span class="text-gray-400">Avg Delay</span>
                            <span class="font-mono text-gray-700">
                              {c.delayText}
                            </span>
                          </div>
                          <div class="bg-surface-3 h-1.5 overflow-hidden rounded-full">
                            <div
                              class="h-full rounded-full bg-amber-500/70 transition-all duration-700"
                              style={{ width: `${c.delayWidth}%` }}
                            ></div>
                          </div>
                        </div>
                        <div>
                          <div class="mb-1 flex justify-between text-[11px]">
                            <span class="text-gray-400">Packet Loss</span>
                            <span class="font-mono text-gray-700">
                              {c.lossText}
                            </span>
                          </div>
                          <div class="bg-surface-3 h-1.5 overflow-hidden rounded-full">
                            <div
                              class="h-full rounded-full bg-red-500/60 transition-all duration-700"
                              style={{ width: `${c.lossWidth}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div class="mt-4 flex items-center gap-1.5 border-t border-gray-100 pt-3">
                      {c.algoDots.map((dot) => (
                        <span
                          class="h-2 w-2 rounded-full"
                          style={{ background: dot.color }}
                          title={dot.label}
                        ></span>
                      ))}
                      <span class="ml-1 text-[10px] text-gray-400">
                        {c.algoCountText}
                      </span>
                    </div>
                  </a>
                ))}
              </div>

              {cards.length === 0 && (
                <div class="py-20 text-center">
                  <p class="text-sm text-gray-400">
                    No scenarios match the current filters.
                  </p>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "fm-dashboard": Dashboard;
  }
}
