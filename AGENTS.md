<!-- intent-skills:start -->

Swifty Intents - before editing files under flowmonitor/, run the matching guidance command.

swiftyIntents

- id: "@swifty.js/lit-jsx#swifty-lit-jsx"
  run: "npx @tanstack/intent load @swifty.js/lit-jsx#swifty-lit-jsx"
  for: "Authoritative reference for @swifty.js/lit-jsx (lit-jsx/ in this repo), a
  JSX runtime for Lit (lit@3.x only — no older-Lit compatibility). Write
  Lit/web-component applications with React-style JSX instead of html``
  string templates. Covers the automatic JSX runtime (jsx/jsxs/jsxDEV,
  Fragment/<>), createElement's JSX-prop → Lit-expression semantics (onXxx →
  @event listeners on primitives, class/className → .className property,
  style → styleMap, ref → lit ref directive, hyphenated props → attributes,
  booleans → ?boolean-attribute plus property, everything else → property
  assignment even when undefined, key stripped, false/null/undefined children
  skipped), createRoot/Root (render/unmount/duplicate-container warning),
  the element registry (assignElements/resetElements tag overrides accepting
  plain strings or Lit StaticValues, default div fallback), the local
  customElement decorator that registers tag names for class-component JSX,
  re-exported Lit decorators (property, state, query, queryAll, queryAsync,
  queryAssignedElements, queryAssignedNodes, eventOptions), the spread
  directive, the full JSX→DOM event-name map, and the JSX type layer
  (JSX.IntrinsicElements over HTMLElementTagNameMap). Testing setup:
  vitest + jsdom (tests/). Trigger tokens: @swifty.js/lit-jsx, lit-jsx,
  jsxImportSource "@swifty.js/lit-jsx", jsx-runtime, createRoot,
  assignElements, resetElements, customElementRegistry, jsx",
  Fragment, swifty-lit-jsx. Use whenever a file in this repo uses JSX with
  LitElement/web components, configures jsxImportSource, or when the user
  mentions lit-jsx, JSX props not applying, onXxx handlers not firing on
  custom elements, tag overrides, or lit-jsx tests."

<!-- intent-skills:end -->
