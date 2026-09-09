import { defineConfig, type Plugin } from "vite";
import tailwindcss from "@tailwindcss/vite";
import { execSync } from "node:child_process";
import { join } from "node:path";

function parseFlowmonitor(): Plugin {
  return {
    name: "parse-flowmonitor",
    buildStart() {
      execSync("node scripts/parse.mjs", {
        cwd: import.meta.dirname,
        stdio: "inherit",
      });
    },
  };
}

export default defineConfig({
  base: "/ns3.40/",
  plugins: [parseFlowmonitor(), tailwindcss()],
  resolve: {
    alias: {
      "@": join(import.meta.dirname, "src"),
    },
  },
});
