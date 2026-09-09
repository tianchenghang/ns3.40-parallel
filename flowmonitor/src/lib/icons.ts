import activity from "lucide-static/icons/activity.svg?raw";
import arrowLeft from "lucide-static/icons/arrow-left.svg?raw";
import arrowUpRight from "lucide-static/icons/arrow-up-right.svg?raw";
import server from "lucide-static/icons/server.svg?raw";
import network from "lucide-static/icons/network.svg?raw";
import globe from "lucide-static/icons/globe.svg?raw";
import signal from "lucide-static/icons/signal.svg?raw";
import wifi from "lucide-static/icons/wifi.svg?raw";
import satellite from "lucide-static/icons/satellite.svg?raw";
import zap from "lucide-static/icons/zap.svg?raw";
import layers from "lucide-static/icons/layers.svg?raw";

function icon(svg: string, size = 18): string {
  return svg
    .replace(/width="24"/, `width="${size}"`)
    .replace(/height="24"/, `height="${size}"`)
    .replace(/<!--[^>]*-->\s*/g, "");
}

export const icons = {
  activity: icon(activity),
  arrowLeft: icon(arrowLeft, 16),
  arrowUpRight: icon(arrowUpRight, 14),
};

export const categoryIcons: Record<string, string> = {
  "Data Center": icon(server, 14),
  "DC Fabric": icon(network, 14),
  WAN: icon(globe, 14),
  Cellular: icon(signal, 14),
  WiFi: icon(wifi, 14),
  Satellite: icon(satellite, 14),
  RDMA: icon(zap, 14),
  Mixed: icon(layers, 14),
};
