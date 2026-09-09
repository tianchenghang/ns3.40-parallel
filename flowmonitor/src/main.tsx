import "./global.css";

import { createRoot } from "@swifty.js/lit-jsx";
import "./app";

createRoot(document.getElementById("app")!).render(<fm-app />);
