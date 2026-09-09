export interface FlowSummary {
  throughputMbps: number;
  avgDelayUs: number;
  avgJitterUs: number;
  lossRate: number;
  totalRxGB: number;
  tcpFlowCount: number;
  durationS: number;
}

export interface FlowDetail {
  flowId: number;
  txBytes: number;
  rxBytes: number;
  txPackets: number;
  rxPackets: number;
  lostPackets: number;
  durationS: number;
  throughputMbps: number;
  avgDelayUs: number;
  avgJitterUs: number;
  lossRate: number;
  lastDelayUs: number;
  type: string;
  src?: string;
  dst?: string;
  protocol?: string;
  srcPort?: number;
  dstPort?: number;
  delayHist: { start: number; width: number; count: number }[];
}

export interface ScenarioIndex {
  scenario: string;
  dataset: string;
  algorithms: string[];
  summaries: Record<string, FlowSummary>;
}

export interface ScenarioDetail {
  scenario: string;
  dataset: string;
  algorithms: Record<string, { flows: FlowDetail[]; summary: FlowSummary }>;
}

export interface DataIndex {
  scenarios: ScenarioIndex[];
  algorithms: string[];
  generatedAt: string;
}

let indexCache: DataIndex | null = null;
const detailCache = new Map<string, ScenarioDetail>();

const base = import.meta.env.BASE_URL;

export async function loadIndex(): Promise<DataIndex> {
  if (indexCache) return indexCache;
  const resp = await fetch(`${base}data/index.json`);
  indexCache = await resp.json();
  return indexCache!;
}

export async function loadScenario(
  dataset: string,
  scenario: string,
): Promise<ScenarioDetail> {
  const key = `${dataset}/${scenario}`;
  if (detailCache.has(key)) return detailCache.get(key)!;
  const safeName = key.replace(/\//g, "__");
  const resp = await fetch(`${base}data/${safeName}.json`);
  const data = await resp.json();
  detailCache.set(key, data);
  return data;
}

export const ALGO_COLORS: Record<string, string> = {
  TcpSwift: "#22d3ee",
  TcpBbr: "#a78bfa",
  TcpCubic: "#fb923c",
  TcpNewReno: "#4ade80",
};

export const ALGO_LABELS: Record<string, string> = {
  TcpSwift: "Swift",
  TcpBbr: "BBR",
  TcpCubic: "CUBIC",
  TcpNewReno: "NewReno",
};

export function formatThroughput(mbps: number): string {
  if (mbps >= 1000) return `${(mbps / 1000).toFixed(2)} Gbps`;
  if (mbps >= 1) return `${mbps.toFixed(1)} Mbps`;
  return `${(mbps * 1000).toFixed(0)} Kbps`;
}

export function formatDelay(us: number): string {
  if (us >= 1000) return `${(us / 1000).toFixed(2)} ms`;
  if (us >= 1) return `${us.toFixed(1)} us`;
  return `${(us * 1000).toFixed(0)} ns`;
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  return `${(bytes / 1e3).toFixed(0)} KB`;
}

export function formatLoss(rate: number): string {
  if (rate === 0) return "0%";
  if (rate < 0.0001) return `${(rate * 100).toExponential(1)}%`;
  return `${(rate * 100).toFixed(3)}%`;
}

export function scenarioCategory(name: string): string {
  if (name.startsWith("dc_") || name.startsWith("intra_rack"))
    return "Data Center";
  if (
    name.startsWith("leaf_spine") ||
    name.startsWith("oversub") ||
    name.startsWith("cross_pod")
  )
    return "DC Fabric";
  if (name.startsWith("wan_") || name.startsWith("cross_dc")) return "WAN";
  if (name.startsWith("lte_") || name.startsWith("nr_5g")) return "Cellular";
  if (name.startsWith("wifi_")) return "WiFi";
  if (name.startsWith("satellite_")) return "Satellite";
  if (name.startsWith("rdma_")) return "RDMA";
  return "Mixed";
}
