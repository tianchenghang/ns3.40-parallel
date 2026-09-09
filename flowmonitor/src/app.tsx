import { LitElement, customElement } from "@swifty.js/lit-jsx";
import { Router } from "@lit-labs/router";
import "./views/dashboard";
import "./views/scenario";

const base = import.meta.env.BASE_URL.replace(/\/+$/, "");

@customElement("fm-app")
export class App extends LitElement {
  private router = new Router(
    this,
    [
      {
        path: `${base}/scenario`,
        render: () => {
          const query = new URLSearchParams(location.search);
          return (
            <fm-scenario
              scenario={query.get("scenario") ?? ""}
              datasetName={query.get("dataset") ?? "comparison-udp"}
            />
          );
        },
      },
    ],
    { fallback: { render: () => <fm-dashboard /> } },
  );

  protected override createRenderRoot() {
    return this;
  }

  protected override render() {
    return this.router.outlet();
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "fm-app": App;
  }
}
