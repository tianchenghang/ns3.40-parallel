import {
  LitElement,
  customElement,
  state,
  property,
  query,
} from "@swifty.js/lit-jsx";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import gsap from "gsap";
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  RadarController,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import {
  loadScenario,
  ALGO_COLORS,
  ALGO_LABELS,
  formatThroughput,
  formatDelay,
  formatBytes,
  formatLoss,
  scenarioCategory,
} from "../lib/data";
import { icons } from "../lib/icons";
import type { ScenarioDetail } from "../lib/data";

const base = import.meta.env.BASE_URL.replace(/\/+$/, "");

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  RadarController,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
);

interface AlgoCardVM {
  algo: string;
  label: string;
  color: string;
  throughput: string;
  delay: string;
  jitter: string;
  loss: string;
  totalRx: string;
}

interface FlowRowVM {
  flowId: number;
  src: string;
  srcPort: number;
  throughput: string;
  delay: string;
  jitter: string;
  loss: string;
  hasLoss: boolean;
}

interface FlowTableVM {
  algo: string;
  label: string;
  color: string;
  flowCountText: string;
  flows: FlowRowVM[];
}

const METRICS = [
  { key: "throughput", label: "Throughput" },
  { key: "delay", label: "Delay" },
  { key: "jitter", label: "Jitter" },
  { key: "loss", label: "Loss" },
];

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function getMetricValue(
  d: ScenarioDetail,
  algo: string,
  metric: string,
): number {
  if (!d.algorithms[algo]) return 0;
  const s = d.algorithms[algo].summary;
  if (metric === "throughput") return s.throughputMbps;
  if (metric === "delay") return s.avgDelayUs;
  if (metric === "jitter") return s.avgJitterUs;
  if (metric === "loss") return s.lossRate * 100;
  return 0;
}

function formatMetricValue(
  d: ScenarioDetail,
  algo: string,
  metric: string,
): string {
  const v = getMetricValue(d, algo, metric);
  if (metric === "throughput") return formatThroughput(v);
  if (metric === "delay") return formatDelay(v);
  if (metric === "jitter") return formatDelay(v);
  if (metric === "loss") return formatLoss(v / 100);
  return String(v);
}

function metricUnit(metric: string): string {
  if (metric === "throughput") return "Mbps";
  if (metric === "delay") return "us";
  if (metric === "jitter") return "us";
  if (metric === "loss") return "%";
  return "";
}

@customElement("fm-scenario")
export class Scenario extends LitElement {
  @property() scenario = "";
  @property() datasetName = "comparison-udp";
  @state() private data: ScenarioDetail | null = null;
  @state() private loading = true;
  @state() private metric = "throughput";

  @query("#barChart") private barCanvas!: HTMLCanvasElement;
  @query("#radarChart") private radarCanvas!: HTMLCanvasElement;
  @query("#delayChart") private delayCanvas!: HTMLCanvasElement;

  private barChart: Chart | null = null;
  private radarChart: Chart | null = null;
  private delayChart: Chart | null = null;

  protected override createRenderRoot() {
    return this;
  }

  override firstUpdated() {
    gsap.fromTo(
      this.querySelector(".sc-header"),
      { opacity: 0, y: -16 },
      { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" },
    );
    (async () => {
      const d = await loadScenario(this.datasetName, this.scenario);
      this.data = d;
      this.loading = false;
    })();
  }

  protected override updated(changed: Map<string | number | symbol, unknown>) {
    if (!this.data) return;
    if (changed.has("data")) {
      gsap.fromTo(
        this.querySelectorAll(".algo-summary-card"),
        { opacity: 0, y: 20, scale: 0.96 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.4,
          stagger: 0.08,
          ease: "power2.out",
          delay: 0.15,
        },
      );
      gsap.fromTo(
        this.querySelectorAll(".chart-section"),
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.4, stagger: 0.1, delay: 0.25 },
      );
    }
    if (changed.has("data") || changed.has("metric")) {
      this.renderBarChart();
      this.renderRadarChart();
      this.renderDelayChart();
    }
  }

  override disconnectedCallback() {
    this.barChart?.destroy();
    this.radarChart?.destroy();
    this.delayChart?.destroy();
    this.barChart = this.radarChart = this.delayChart = null;
    super.disconnectedCallback();
  }

  private get algoCards(): AlgoCardVM[] {
    const d = this.data;
    if (!d) return [];
    return Object.keys(d.algorithms).map((algo) => {
      const s = d.algorithms[algo].summary;
      return {
        algo,
        label: ALGO_LABELS[algo] || algo,
        color: ALGO_COLORS[algo] || "#888",
        throughput: formatThroughput(s.throughputMbps),
        delay: formatDelay(s.avgDelayUs),
        jitter: formatDelay(s.avgJitterUs),
        loss: formatLoss(s.lossRate),
        totalRx: formatBytes(s.totalRxGB * 1e9),
      };
    });
  }

  private get flowTables(): FlowTableVM[] {
    const d = this.data;
    if (!d) return [];
    return Object.keys(d.algorithms).map((algo) => {
      const tcpFlows = d.algorithms[algo].flows.filter(
        (f) => f.type === "tcp-data",
      );
      return {
        algo,
        label: ALGO_LABELS[algo] || algo,
        color: ALGO_COLORS[algo] || "#888",
        flowCountText: `${tcpFlows.length} flows`,
        flows: tcpFlows.map((f) => ({
          flowId: f.flowId,
          src: f.src || "",
          srcPort: f.srcPort || 0,
          throughput: formatThroughput(f.throughputMbps),
          delay: formatDelay(f.avgDelayUs),
          jitter: formatDelay(f.avgJitterUs),
          loss: formatLoss(f.lossRate),
          hasLoss: f.lossRate > 0,
        })),
      };
    });
  }

  private get metricLabel(): string {
    return METRICS.find((m) => m.key === this.metric)?.label || "Throughput";
  }

  private renderBarChart() {
    const d = this.data;
    const canvas = this.barCanvas;
    if (!d || !canvas) return;
    const m = this.metric;

    const algos = Object.keys(d.algorithms);
    const labels = algos.map((a) => ALGO_LABELS[a] || a);
    const values = algos.map((a) => getMetricValue(d, a, m));
    const colors = algos.map((a) => ALGO_COLORS[a] || "#888");

    this.barChart?.destroy();
    this.barChart = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: METRICS.find((x) => x.key === m)?.label || m,
            data: values,
            backgroundColor: colors.map((c) => hexToRgba(c, 0.7)),
            borderColor: colors,
            borderWidth: 1.5,
            borderRadius: 6,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: "easeOutQuart" },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#1e293b",
            titleFont: { family: "Geist Mono, monospace", size: 11 },
            bodyFont: { family: "Geist Mono, monospace", size: 11 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (item) => formatMetricValue(d, algos[item.dataIndex], m),
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              font: { family: "Geist Mono, monospace", size: 11 },
              color: "#64748b",
            },
          },
          y: {
            grid: { color: "#f1f5f9" },
            ticks: {
              font: { family: "Geist Mono, monospace", size: 10 },
              color: "#94a3b8",
            },
            title: {
              display: true,
              text: metricUnit(m),
              font: { size: 10 },
              color: "#94a3b8",
            },
          },
        },
      },
    });
  }

  private renderRadarChart() {
    const d = this.data;
    const canvas = this.radarCanvas;
    if (!d || !canvas) return;

    const algos = Object.keys(d.algorithms);
    const metrics = ["throughput", "delay", "jitter", "loss"];
    const metricLabels = ["Throughput", "Delay", "Jitter", "Loss"];

    const maxVals = metrics.map((m) =>
      Math.max(...algos.map((a) => getMetricValue(d, a, m)), 0.001),
    );

    this.radarChart?.destroy();
    this.radarChart = new Chart(canvas, {
      type: "radar",
      data: {
        labels: metricLabels,
        datasets: algos.map((algo) => {
          const color = ALGO_COLORS[algo] || "#888";
          return {
            label: ALGO_LABELS[algo] || algo,
            data: metrics.map(
              (m, i) => getMetricValue(d, algo, m) / maxVals[i],
            ),
            borderColor: color,
            backgroundColor: hexToRgba(color, 0.08),
            pointBackgroundColor: color,
            pointRadius: 3,
            borderWidth: 2,
          };
        }),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: "easeOutQuart" },
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              font: { family: "Geist Mono, monospace", size: 10 },
              color: "#64748b",
              boxWidth: 12,
              padding: 12,
            },
          },
          tooltip: {
            backgroundColor: "#1e293b",
            titleFont: { family: "Geist Mono, monospace", size: 11 },
            bodyFont: { family: "Geist Mono, monospace", size: 11 },
            padding: 10,
            cornerRadius: 8,
          },
        },
        scales: {
          r: {
            grid: { color: "#e2e8f0" },
            angleLines: { color: "#e2e8f0" },
            pointLabels: {
              font: { family: "Geist Mono, monospace", size: 10 },
              color: "#64748b",
            },
            ticks: { display: false },
            suggestedMin: 0,
            suggestedMax: 1,
          },
        },
      },
    });
  }

  private renderDelayChart() {
    const d = this.data;
    const canvas = this.delayCanvas;
    if (!d || !canvas) return;

    const algos = Object.keys(d.algorithms);

    const allBins = new Set<number>();
    for (const algo of algos) {
      const tcpFlows = d.algorithms[algo].flows.filter(
        (f) => f.type === "tcp-data",
      );
      for (const flow of tcpFlows) {
        for (const bin of flow.delayHist) {
          allBins.add(bin.start);
        }
      }
    }
    const sortedBins = [...allBins].sort((a, b) => a - b);
    if (sortedBins.length === 0) return;

    const labels = sortedBins.map((b) => {
      if (b >= 1) return `${b.toFixed(2)}s`;
      if (b >= 0.001) return `${(b * 1000).toFixed(1)}ms`;
      if (b > 0) return `${(b * 1e6).toFixed(0)}us`;
      return "0";
    });

    this.delayChart?.destroy();
    this.delayChart = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: algos.map((algo) => {
          const color = ALGO_COLORS[algo] || "#888";
          const tcpFlows = d.algorithms[algo].flows.filter(
            (f) => f.type === "tcp-data",
          );
          const binCounts = sortedBins.map((binStart) => {
            let total = 0;
            for (const flow of tcpFlows) {
              const bin = flow.delayHist.find((h) => h.start === binStart);
              if (bin) total += bin.count;
            }
            return total;
          });
          return {
            label: ALGO_LABELS[algo] || algo,
            data: binCounts,
            backgroundColor: hexToRgba(color, 0.6),
            borderColor: color,
            borderWidth: 1,
            borderRadius: 3,
          };
        }),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: "easeOutQuart" },
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              font: { family: "Geist Mono, monospace", size: 10 },
              color: "#64748b",
              boxWidth: 12,
              padding: 12,
            },
          },
          tooltip: {
            backgroundColor: "#1e293b",
            titleFont: { family: "Geist Mono, monospace", size: 11 },
            bodyFont: { family: "Geist Mono, monospace", size: 11 },
            padding: 10,
            cornerRadius: 8,
            mode: "index",
            intersect: false,
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              font: { family: "Geist Mono, monospace", size: 9 },
              color: "#94a3b8",
              maxRotation: 45,
              maxTicksLimit: 20,
            },
            title: {
              display: true,
              text: "Delay bucket",
              font: { size: 10 },
              color: "#94a3b8",
            },
          },
          y: {
            grid: { color: "#f1f5f9" },
            ticks: {
              font: { family: "Geist Mono, monospace", size: 10 },
              color: "#94a3b8",
            },
            title: {
              display: true,
              text: "Packet count",
              font: { size: 10 },
              color: "#94a3b8",
            },
          },
        },
      },
    });
  }

  protected override render() {
    const scenarioName = this.scenario.replace(/_/g, " ");
    const category = scenarioCategory(this.scenario);
    return (
      <div class="min-h-screen">
        <header class="sc-header sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-2xl">
          <div class="mx-auto flex max-w-7xl items-center gap-4 px-6 py-4">
            <a
              href={`${base}/`}
              class="bg-surface-2 hover:bg-surface-3 flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-gray-500 transition-all hover:text-gray-900"
            >
              {unsafeHTML(icons.arrowLeft)}
            </a>
            <div>
              <h1 class="text-base font-semibold tracking-tight text-gray-900 capitalize">
                {scenarioName}
              </h1>
              <p class="text-[11px] text-gray-400">
                {category} / {this.datasetName}
              </p>
            </div>
          </div>
        </header>

        <main class="mx-auto max-w-7xl px-6 py-8">
          {this.loading && (
            <div class="flex items-center justify-center py-32">
              <div class="border-accent/30 border-t-accent h-10 w-10 animate-spin rounded-full border-2"></div>
            </div>
          )}
          {this.data && (
            <div>
              <div class="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {this.algoCards.map((card) => (
                  <div class="algo-summary-card relative overflow-hidden rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                    <div
                      class="absolute top-0 left-0 h-0.5 w-full"
                      style={{
                        background: `linear-gradient(90deg, ${card.color}, transparent)`,
                      }}
                    ></div>
                    <div class="mb-4 flex items-center gap-2">
                      <span
                        class="h-3 w-3 rounded-full"
                        style={{ background: card.color }}
                      ></span>
                      <span
                        class="text-sm font-semibold"
                        style={{ color: card.color }}
                      >
                        {card.label}
                      </span>
                    </div>
                    <div class="space-y-3">
                      <div class="flex items-baseline justify-between">
                        <span class="text-[11px] text-gray-400">
                          Throughput
                        </span>
                        <span class="font-mono text-sm text-gray-800">
                          {card.throughput}
                        </span>
                      </div>
                      <div class="flex items-baseline justify-between">
                        <span class="text-[11px] text-gray-400">Avg Delay</span>
                        <span class="font-mono text-sm text-gray-800">
                          {card.delay}
                        </span>
                      </div>
                      <div class="flex items-baseline justify-between">
                        <span class="text-[11px] text-gray-400">Jitter</span>
                        <span class="font-mono text-sm text-gray-800">
                          {card.jitter}
                        </span>
                      </div>
                      <div class="flex items-baseline justify-between">
                        <span class="text-[11px] text-gray-400">Loss Rate</span>
                        <span class="font-mono text-sm text-gray-800">
                          {card.loss}
                        </span>
                      </div>
                      <div class="flex items-baseline justify-between">
                        <span class="text-[11px] text-gray-400">Total RX</span>
                        <span class="font-mono text-sm text-gray-800">
                          {card.totalRx}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div class="chart-section mb-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                <div class="mb-6 flex items-center justify-between">
                  <h2 class="text-lg font-semibold tracking-tight text-gray-900">
                    Algorithm Comparison
                  </h2>
                  <div class="flex items-center gap-1.5">
                    {METRICS.map((m) => (
                      <button
                        class={`cursor-pointer rounded-lg px-3 py-1.5 text-xs transition-all ${
                          this.metric === m.key
                            ? "bg-accent/10 text-accent-soft"
                            : "text-gray-400 hover:text-gray-600"
                        }`}
                        onClick={() => {
                          this.metric = m.key;
                        }}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <div class="relative h-64">
                    <canvas id="barChart"></canvas>
                  </div>
                  <div class="relative h-64">
                    <canvas id="radarChart"></canvas>
                  </div>
                </div>
                <p class="mt-3 text-center text-[11px] text-gray-400">
                  {this.metricLabel} comparison across congestion control
                  algorithms
                </p>
              </div>

              <div class="chart-section mb-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 class="mb-5 text-lg font-semibold tracking-tight text-gray-900">
                  Delay Distribution
                </h2>
                <div class="relative h-72">
                  <canvas id="delayChart"></canvas>
                </div>
              </div>

              <div class="chart-section rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 class="mb-5 text-lg font-semibold tracking-tight text-gray-900">
                  TCP Flow Details
                </h2>
                <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
                  {this.flowTables.map((tbl) => (
                    <div class="bg-surface-0 overflow-hidden rounded-xl border border-gray-100">
                      <div class="flex items-center gap-2 border-b border-gray-100 px-4 py-3">
                        <span
                          class="h-2.5 w-2.5 rounded-full"
                          style={{ background: tbl.color }}
                        ></span>
                        <span
                          class="text-xs font-semibold"
                          style={{ color: tbl.color }}
                        >
                          {tbl.label}
                        </span>
                        <span class="ml-auto text-[10px] text-gray-400">
                          {tbl.flowCountText}
                        </span>
                      </div>
                      <div class="overflow-x-auto">
                        <table class="w-full text-[11px]">
                          <thead>
                            <tr class="border-b border-gray-100 text-gray-400">
                              <th class="px-4 py-2 text-left font-medium">
                                Flow
                              </th>
                              <th class="px-3 py-2 text-right font-medium">
                                Throughput
                              </th>
                              <th class="px-3 py-2 text-right font-medium">
                                Delay
                              </th>
                              <th class="px-3 py-2 text-right font-medium">
                                Jitter
                              </th>
                              <th class="px-4 py-2 text-right font-medium">
                                Loss
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {tbl.flows.map((flow) => (
                              <tr class="hover:bg-surface-2 border-b border-gray-50 transition-colors">
                                <td class="px-4 py-2.5">
                                  <span class="font-mono text-gray-700">
                                    #{flow.flowId}
                                  </span>
                                  <span class="ml-1 text-gray-400">
                                    {flow.src}:{flow.srcPort}
                                  </span>
                                </td>
                                <td class="px-3 py-2.5 text-right font-mono text-gray-700">
                                  {flow.throughput}
                                </td>
                                <td class="px-3 py-2.5 text-right font-mono text-gray-700">
                                  {flow.delay}
                                </td>
                                <td class="px-3 py-2.5 text-right font-mono text-gray-700">
                                  {flow.jitter}
                                </td>
                                <td
                                  class={`px-4 py-2.5 text-right font-mono ${
                                    flow.hasLoss
                                      ? "text-red-500"
                                      : "text-gray-400"
                                  }`}
                                >
                                  {flow.loss}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "fm-scenario": Scenario;
  }
}
