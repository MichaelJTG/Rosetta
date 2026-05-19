"""Dashboard HTML embebido — interfaz visual para auditor.

Panel único servido por FastAPI en GET /dashboard. Usa vis.js (CDN) para
el grafo y vanilla JS para el resto. Sin dependencias de npm.

Dirección visual: bone cálido + acento copper, tipografía Geist sans
(UI y display) y Geist Mono (datos). Sistema de design tokens; sin serif.
"""

from __future__ import annotations

HTML_DASHBOARD: str = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ROSETTA · Compliance Intelligence Platform</title>

  <!-- Tipografia: Geist (UI) + Geist Mono (data) - sans tecnico, sin serif -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap">
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

  <style>
    /* ════════════════════════════════════════════════════════════════════
       DESIGN TOKENS
       ════════════════════════════════════════════════════════════════════ */
    :root {
      /* Surfaces - warm bone palette (neutrales tintados, sin blanco puro) */
      --bg-0: #f5f2eb;
      --bg-1: #efebe2;
      --surface-1: #fffdf8;
      --surface-2: #faf7f0;
      --surface-3: #f0ece2;
      --surface-hi: #f7f3eb;

      /* Borders */
      --line-1: #ebe6d8;
      --line-2: #d8d2c0;
      --line-3: #a8a18d;

      /* Text — ink scale */
      --fg-1: #1a2030;
      --fg-2: #3a4254;
      --fg-3: #6b7280;
      --fg-4: #98a0ab;
      --fg-5: #c5c1b3;

      /* Brand — warm copper */
      --accent: #9a6635;
      --accent-hi: #b87f44;
      --accent-lo: #7a4f28;
      --accent-bg: #f5e9d6;
      --accent-glow: rgba(184, 127, 68, .35);

      /* Info — deep navy */
      --sky: #1e3a5f;
      --sky-hi: #2e5a8f;
      --sky-bg: #e6ecf5;

      /* Severity — printed-paper aesthetic */
      --sev-critica: #a8312a;
      --sev-critica-bg: #fbe9e7;
      --sev-alta: #b8702a;
      --sev-alta-bg: #fbf0e1;
      --sev-media: #8a6d1c;
      --sev-media-bg: #f7eecf;
      --sev-baja: #3d7d4a;
      --sev-baja-bg: #e2efdf;
      --sev-info: #5a6470;
      --sev-info-bg: #eceef1;

      /* Type - Geist sans (UI + display) + Geist Mono (datos). Sin serif. */
      --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      --font-display: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      --font-mono: 'Geist Mono', 'SF Mono', Menlo, Consolas, monospace;

      /* Spacing (4px base) */
      --s-1: 4px;  --s-2: 8px;  --s-3: 12px;  --s-4: 16px;
      --s-5: 24px; --s-6: 32px; --s-7: 48px;  --s-8: 64px;

      /* Radius */
      --r-1: 4px; --r-2: 6px; --r-3: 10px; --r-pill: 999px;

      /* Motion */
      --d-fast: 120ms;
      --d-base: 200ms;
      --ease: cubic-bezier(.16, 1, .3, 1);

      /* Z */
      --z-nav: 50; --z-bar: 40; --z-modal: 100;
    }

    /* RESET */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
    body {
      font-family: var(--font-sans);
      font-size: 14px;
      font-weight: 400;
      line-height: 1.5;
      letter-spacing: -0.005em;
      color: var(--fg-1);
      background: var(--bg-0);
      background-image:
        radial-gradient(ellipse 1400px 700px at 15% -10%, rgba(154, 102, 53, .07), transparent 60%),
        radial-gradient(ellipse 1000px 600px at 100% 100%, rgba(30, 58, 95, .05), transparent 60%);
      min-height: 100vh;
      display: flex;
      overflow-x: hidden;
    }
    @media (prefers-reduced-motion: reduce) {
      * { animation-duration: .01ms !important; transition-duration: .01ms !important; }
    }

    ::selection { background: var(--accent); color: #fffdf8; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--line-2); border-radius: 999px; border: 2px solid var(--bg-0); }
    ::-webkit-scrollbar-thumb:hover { background: var(--line-3); }
    :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--r-1); }

    /* SIDEBAR */
    nav#nav-tabs {
      width: 244px;
      flex-shrink: 0;
      min-height: 100vh;
      background: linear-gradient(180deg, var(--bg-1) 0%, var(--bg-0) 100%);
      border-right: 1px solid var(--line-1);
      display: flex;
      flex-direction: column;
      padding: var(--s-5) var(--s-3) var(--s-3);
      gap: var(--s-1);
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      overflow-x: hidden;
      z-index: var(--z-nav);
      transition: width var(--d-base) var(--ease), padding var(--d-base) var(--ease), border-color var(--d-base) var(--ease);
    }
    /* Collapsed sidebar (toggle from topbar / shortcut \\) */
    body.sidebar-collapsed nav#nav-tabs {
      width: 0;
      padding-left: 0;
      padding-right: 0;
      border-right-color: transparent;
    }
    body.sidebar-collapsed nav#nav-tabs > * {
      opacity: 0;
      pointer-events: none;
      transition: opacity var(--d-fast) var(--ease);
    }

    /* Toggle buttons in topbar */
    .icon-btn {
      display: inline-flex; align-items: center; justify-content: center;
      width: 32px; height: 32px;
      background: transparent;
      border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      color: var(--fg-3);
      cursor: pointer;
      padding: 0;
      transition: background var(--d-fast) var(--ease), color var(--d-fast) var(--ease), border-color var(--d-fast) var(--ease);
      flex-shrink: 0;
    }
    .icon-btn:hover { background: var(--surface-2); color: var(--fg-1); border-color: var(--line-3); }
    .icon-btn:active { transform: translateY(1px); }
    .icon-btn svg { width: 14px; height: 14px; display: block; }
    .icon-btn .kbd {
      margin-left: 6px;
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--fg-5);
    }

    .brand {
      display: flex; align-items: center; gap: var(--s-2);
      padding: 0 var(--s-3) var(--s-4);
      margin-bottom: var(--s-3);
      border-bottom: 1px solid var(--line-1);
    }
    .brand-mark {
      width: 28px; height: 28px;
      background: var(--accent);
      border-radius: var(--r-1);
      position: relative;
      box-shadow: 0 0 24px -6px var(--accent-glow);
      flex-shrink: 0;
    }
    .brand-mark::before { content: ''; position: absolute; inset: 7px; background: var(--bg-1); border-radius: 1px; }
    .brand-mark::after { content: ''; position: absolute; left: 11px; top: 11px; width: 6px; height: 6px; background: var(--accent); border-radius: 1px; }
    .brand-text { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
    .brand-name { font-size: 13px; font-weight: 600; color: var(--fg-1); letter-spacing: 0.04em; }
    .brand-tag { font-family: var(--font-mono); font-size: 9.5px; color: var(--fg-3); text-transform: uppercase; }

    .status-pill {
      display: flex; align-items: center; gap: var(--s-2);
      padding: var(--s-2) var(--s-3);
      margin: 0 var(--s-2) var(--s-3);
      background: var(--surface-2);
      border: 1px solid var(--line-1);
      border-radius: var(--r-2);
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--fg-3);
    }
    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--fg-4); flex-shrink: 0; }
    .status-dot.ok { background: var(--sev-baja); animation: pulse 2.4s ease-in-out infinite; }
    .status-dot.err { background: var(--sev-critica); }
    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(61, 125, 74, .45); }
      50%      { box-shadow: 0 0 0 6px rgba(61, 125, 74, 0); }
    }

    .nav-section {
      font-family: var(--font-mono);
      font-size: 10px; font-weight: 500;
      color: var(--fg-4);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: var(--s-4) var(--s-3) var(--s-2);
    }
    .nav-section:first-of-type { padding-top: var(--s-2); }

    nav button {
      width: 100%;
      display: flex; align-items: center; gap: var(--s-3);
      padding: 7px var(--s-3);
      background: transparent;
      border: none;
      border-radius: var(--r-1);
      color: var(--fg-3);
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 500;
      letter-spacing: -0.005em;
      cursor: pointer;
      transition: background var(--d-fast) var(--ease), color var(--d-fast) var(--ease);
      text-align: left;
      position: relative;
    }
    nav button .nav-key {
      margin-left: auto;
      font-family: var(--font-mono);
      font-size: 10px; color: var(--fg-5);
      padding: 1px 5px;
      border: 1px solid var(--line-1);
      border-radius: 3px;
    }
    nav button:hover { color: var(--fg-1); background: rgba(154, 102, 53, .06); }
    nav button:hover .nav-key { color: var(--fg-3); border-color: var(--line-2); }
    nav button.active { color: var(--fg-1); background: var(--accent-bg); }
    nav button.active::before {
      content: '';
      position: absolute; left: -4px; top: 4px; bottom: 4px;
      width: 2px; background: var(--accent); border-radius: 0 2px 2px 0;
    }
    nav button.active .nav-key { color: var(--accent); border-color: var(--accent-lo); }

    .nav-footer {
      margin-top: auto;
      padding: var(--s-3);
      border-top: 1px solid var(--line-1);
      display: flex; flex-direction: column; gap: var(--s-1);
    }
    .nav-footer-row {
      display: flex; justify-content: space-between; align-items: center;
      font-family: var(--font-mono);
      font-size: 10px; color: var(--fg-4);
    }
    .nav-footer-row .v { color: var(--fg-2); font-weight: 500; }

    /* MAIN */
    .main { flex: 1; min-width: 0; display: flex; flex-direction: column; }

    .topbar {
      height: 56px;
      padding: 0 var(--s-6);
      display: flex; align-items: center; gap: var(--s-4);
      border-bottom: 1px solid var(--line-1);
      background: rgba(245, 242, 235, .8);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      position: sticky; top: 0;
      z-index: var(--z-bar);
    }
    .breadcrumb {
      display: flex; align-items: center; gap: var(--s-2);
      font-family: var(--font-mono);
      font-size: 11px; color: var(--fg-3);
    }
    .breadcrumb span:not(.sep) { color: var(--fg-2); }
    .breadcrumb .sep { color: var(--fg-5); }
    .topbar .spacer { flex: 1; }
    .topbar-meta {
      display: flex; align-items: center; gap: var(--s-4);
      font-family: var(--font-mono);
      font-size: 11px; color: var(--fg-3);
    }
    .topbar-meta b { color: var(--fg-2); font-weight: 500; }

    .page-intro {
      padding: var(--s-7) var(--s-6) var(--s-5);
      max-width: 1280px;
      width: 100%;
      margin: 0 auto;
    }
    .eyebrow {
      font-family: var(--font-mono);
      font-size: 11px; font-weight: 500;
      color: var(--accent);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: var(--s-2);
    }
    h1 {
      font-family: var(--font-display);
      font-size: clamp(26px, 1.8vw + 15px, 34px);
      font-weight: 600;
      line-height: 1.12;
      letter-spacing: -0.022em;
      color: var(--fg-1);
      margin-bottom: var(--s-3);
    }
    .lead {
      font-size: 15px;
      line-height: 1.55;
      color: var(--fg-3);
      max-width: 64ch;
    }

    .content {
      flex: 1;
      padding: 0 var(--s-6) var(--s-7);
      max-width: 1280px;
      width: 100%;
      margin: 0 auto;
    }

    .tab-panel { display: none; }
    .tab-panel.active { display: block; animation: tabIn 240ms var(--ease); }
    @keyframes tabIn {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    /* LAYOUT */
    .grid-2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: var(--s-5); }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-4); }
    .grid-12 { display: grid; grid-template-columns: repeat(12, 1fr); gap: var(--s-5); }
    @media (max-width: 920px) {
      .grid-2, .grid-3 { grid-template-columns: 1fr; }
      .grid-12 { grid-template-columns: 1fr; }
    }
    .col-span-7 { grid-column: span 7; }
    .col-span-5 { grid-column: span 5; }
    @media (max-width: 920px) {
      [class*="col-span-"] { grid-column: span 1; }
    }

    .card {
      background: var(--surface-1);
      border: 1px solid var(--line-1);
      border-radius: var(--r-3);
      overflow: hidden;
      position: relative;
      box-shadow:
        0 1px 0 rgba(0, 0, 0, .02),
        0 1px 3px rgba(38, 25, 12, .04),
        0 6px 16px -8px rgba(38, 25, 12, .06);
    }
    .card::before {
      content: '';
      position: absolute; top: 0; left: 0; right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, .8), transparent);
      pointer-events: none;
    }
    .card-head {
      padding: var(--s-3) var(--s-4);
      border-bottom: 1px solid var(--line-1);
      display: flex; align-items: center; justify-content: space-between;
      gap: var(--s-3);
    }
    .card-head h2 { font-size: 13px; font-weight: 600; color: var(--fg-1); }
    .card-head .meta {
      font-family: var(--font-mono);
      font-size: 10px; color: var(--fg-4);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .card-body { padding: var(--s-4); }
    .card-body--flush { padding: 0; }

    /* KPI */
    .kpi-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--s-3); }
    .kpi {
      background: var(--surface-1);
      border: 1px solid var(--line-1);
      border-radius: var(--r-2);
      padding: var(--s-3) var(--s-4);
      position: relative;
      overflow: hidden;
    }
    .kpi-label {
      font-family: var(--font-mono);
      font-size: 10px; color: var(--fg-4);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: var(--s-2);
    }
    .kpi-value {
      font-family: var(--font-mono);
      font-size: 26px; font-weight: 500;
      color: var(--fg-1);
      letter-spacing: -0.02em;
      line-height: 1;
    }
    .kpi-delta {
      font-family: var(--font-mono);
      font-size: 11px; color: var(--fg-3);
      margin-top: var(--s-2);
    }
    /* KPI destacados: borde completo tintado + valor en color (sin side-stripe) */
    .kpi--accent { border-color: #d8b98a; background: var(--accent-bg); }
    .kpi--accent .kpi-value { color: var(--accent); }
    .kpi--sky { border-color: #b8c4d6; background: var(--sky-bg); }
    .kpi--sky .kpi-value { color: var(--sky); }

    /* FORMS */
    label {
      display: block;
      font-family: var(--font-mono);
      font-size: 11px; font-weight: 500;
      color: var(--fg-3);
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin-bottom: var(--s-2);
    }
    label small { font-size: 10px; color: var(--fg-4); text-transform: none; letter-spacing: 0; font-weight: 400; }

    textarea, select, input[type="text"], input[type="file"] {
      width: 100%;
      background: var(--surface-1);
      border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      color: var(--fg-1);
      padding: 9px var(--s-3);
      font-family: var(--font-mono);
      font-size: 12.5px;
      line-height: 1.55;
      transition: border-color var(--d-fast) var(--ease), box-shadow var(--d-fast) var(--ease);
      box-shadow: inset 0 1px 0 rgba(38, 25, 12, .02);
    }
    textarea { resize: vertical; min-height: 140px; tab-size: 2; }
    textarea:focus, select:focus, input:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(154, 102, 53, .15), inset 0 1px 0 rgba(38, 25, 12, .02);
    }
    select {
      cursor: pointer;
      appearance: none; -webkit-appearance: none;
      background-image: linear-gradient(45deg, transparent 50%, var(--fg-3) 50%), linear-gradient(135deg, var(--fg-3) 50%, transparent 50%);
      background-position: calc(100% - 14px) 50%, calc(100% - 9px) 50%;
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
      padding-right: var(--s-6);
    }
    select[multiple] { background-image: none; padding-right: var(--s-3); }
    input[type="file"] { font-family: var(--font-sans); padding: var(--s-2) var(--s-3); cursor: pointer; }
    input[type="file"]::file-selector-button {
      background: var(--surface-2);
      border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      color: var(--fg-1);
      padding: 4px 10px;
      margin-right: var(--s-3);
      font-family: var(--font-sans);
      font-size: 12px;
      cursor: pointer;
      transition: background var(--d-fast);
    }
    input[type="file"]::file-selector-button:hover { background: var(--surface-hi); }
    input[type="checkbox"], input[type="radio"] { accent-color: var(--accent); width: auto; }

    /* Form layout helpers */
    .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-3); }
    @media (max-width: 560px) { .field-grid { grid-template-columns: 1fr; } }
    .field-help {
      font-family: var(--font-sans);
      font-size: 11.5px;
      color: var(--fg-3);
      line-height: 1.5;
      margin: -2px 0 var(--s-2);
      text-transform: none;
      letter-spacing: 0;
    }
    .field-help strong { color: var(--fg-2); font-weight: 600; }
    .mode-toggle {
      display: inline-flex; align-items: center; gap: 6px;
      margin-top: var(--s-3);
      padding: 4px 0;
      background: transparent;
      border: none;
      color: var(--accent);
      font-family: var(--font-mono);
      font-size: 11px;
      letter-spacing: 0.02em;
      cursor: pointer;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .mode-toggle:hover { color: var(--accent-hi); }

    /* Empty state guiado */
    .empty-guide {
      padding: var(--s-6) var(--s-4);
      text-align: center;
    }
    .empty-guide-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--fg-1);
      margin-bottom: var(--s-4);
    }
    .empty-guide-steps {
      display: inline-block;
      text-align: left;
      max-width: 460px;
      margin: 0;
      padding: 0;
      list-style: none;
      counter-reset: g;
    }
    .empty-guide-steps li {
      counter-increment: g;
      position: relative;
      padding: var(--s-2) 0 var(--s-2) var(--s-6);
      font-size: 13px;
      color: var(--fg-3);
      line-height: 1.55;
      border-bottom: 1px solid var(--line-1);
    }
    .empty-guide-steps li:last-child { border-bottom: none; }
    .empty-guide-steps li::before {
      content: counter(g);
      position: absolute; left: 0; top: var(--s-2);
      width: 20px; height: 20px;
      display: flex; align-items: center; justify-content: center;
      background: var(--accent-bg);
      border: 1px solid #d8b98a;
      border-radius: var(--r-pill);
      font-family: var(--font-mono);
      font-size: 11px; font-weight: 600;
      color: var(--accent);
    }
    .empty-guide-steps strong { color: var(--fg-1); font-weight: 600; }

    /* Marco checkbox grid */
    .marco-toggle-all {
      display: inline-flex; align-items: center; gap: 8px;
      margin-bottom: var(--s-2);
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--fg-2);
      text-transform: none; letter-spacing: 0; font-weight: 500;
      cursor: pointer;
    }
    .marco-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2px var(--s-3);
      border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      padding: var(--s-2) var(--s-3);
    }
    @media (max-width: 520px) { .marco-grid { grid-template-columns: 1fr; } }
    .marco-item {
      display: flex; align-items: center; gap: 8px;
      padding: 4px 0;
      font-family: var(--font-sans);
      font-size: 12.5px;
      color: var(--fg-2);
      text-transform: none; letter-spacing: 0; font-weight: 400;
      cursor: pointer;
      margin-bottom: 0;
    }
    .marco-item:hover { color: var(--fg-1); }

    /* MODAL */
    .modal-overlay {
      display: none;
      position: fixed; inset: 0;
      z-index: var(--z-modal);
      background: rgba(26, 32, 48, .42);
      backdrop-filter: blur(3px);
      -webkit-backdrop-filter: blur(3px);
      align-items: flex-start; justify-content: center;
      padding: var(--s-7) var(--s-4);
      overflow-y: auto;
    }
    .modal-overlay.open { display: flex; animation: overlayIn 160ms var(--ease); }
    @keyframes overlayIn { from { opacity: 0; } to { opacity: 1; } }
    .modal {
      width: 100%;
      max-width: 600px;
      background: var(--surface-1);
      border: 1px solid var(--line-2);
      border-radius: var(--r-3);
      box-shadow: 0 24px 64px -16px rgba(26, 25, 12, .4);
      display: flex; flex-direction: column;
      max-height: calc(100vh - var(--s-8));
      animation: modalIn 220ms var(--ease);
    }
    @keyframes modalIn {
      from { opacity: 0; transform: translateY(12px) scale(.98); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }
    .modal-head {
      display: flex; align-items: center; justify-content: space-between;
      padding: var(--s-4) var(--s-5);
      border-bottom: 1px solid var(--line-1);
    }
    .modal-head h2 { font-size: 15px; font-weight: 600; color: var(--fg-1); }
    .modal-close {
      width: 28px; height: 28px;
      display: inline-flex; align-items: center; justify-content: center;
      background: transparent; border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      color: var(--fg-3);
      font-size: 18px; line-height: 1;
      cursor: pointer;
      transition: background var(--d-fast), color var(--d-fast);
    }
    .modal-close:hover { background: var(--surface-2); color: var(--fg-1); }
    .modal-body { padding: var(--s-5); overflow-y: auto; }
    .modal-foot {
      display: flex; align-items: center; justify-content: flex-end; gap: var(--s-2);
      padding: var(--s-3) var(--s-5);
      border-top: 1px solid var(--line-1);
      background: var(--surface-2);
      border-radius: 0 0 var(--r-3) var(--r-3);
    }
    .modal-foot #translate-msg { margin: 0 auto 0 0; }

    /* BUTTONS */
    .btn, button.btn {
      display: inline-flex; align-items: center; gap: var(--s-2);
      padding: 8px var(--s-4);
      background: var(--accent);
      color: #fffdf8;
      border: none;
      border-radius: var(--r-1);
      font-family: var(--font-sans);
      font-size: 13px; font-weight: 600;
      letter-spacing: -0.005em;
      cursor: pointer;
      transition: background var(--d-fast) var(--ease), transform var(--d-fast) var(--ease);
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, .18),
        0 1px 2px rgba(122, 79, 40, .25);
    }
    .btn:hover { background: var(--accent-hi); }
    .btn:active { transform: translateY(1px); }
    .btn:disabled { background: var(--surface-3); color: var(--fg-4); cursor: not-allowed; box-shadow: none; }
    .btn--ghost {
      background: var(--surface-1);
      color: var(--fg-2);
      border: 1px solid var(--line-2);
      box-shadow: 0 1px 0 rgba(38, 25, 12, .03);
    }
    .btn--ghost:hover { background: var(--surface-2); color: var(--fg-1); border-color: var(--line-3); }
    .btn-row { display: flex; align-items: center; gap: var(--s-2); flex-wrap: wrap; }

    button:not(.btn):not(nav button) {
      display: inline-flex; align-items: center; gap: var(--s-2);
      padding: 8px var(--s-4);
      background: var(--accent);
      color: #fffdf8;
      border: none;
      border-radius: var(--r-1);
      font-family: var(--font-sans);
      font-size: 13px; font-weight: 600;
      cursor: pointer;
      transition: background var(--d-fast);
    }
    button:not(.btn):not(nav button):hover { background: var(--accent-hi); }
    button:not(.btn):not(nav button):disabled { background: var(--surface-3); color: var(--fg-4); cursor: not-allowed; }
    button.secondary {
      background: transparent !important;
      color: var(--fg-2) !important;
      border: 1px solid var(--line-2) !important;
      box-shadow: none !important;
    }
    button.secondary:hover { background: var(--surface-2) !important; color: var(--fg-1) !important; }

    /* MESSAGES */
    .msg-error, .msg-success, .msg-info {
      display: inline-flex; align-items: center; gap: var(--s-2);
      font-family: var(--font-mono);
      font-size: 11.5px;
      margin-top: var(--s-3);
      padding: 6px 10px;
      border-radius: var(--r-1);
      border: 1px solid;
    }
    .msg-error   { color: var(--sev-critica); border-color: #e8b8b3; background: var(--sev-critica-bg); }
    .msg-success { color: var(--sev-baja);    border-color: #b9d6bc; background: var(--sev-baja-bg); }
    .msg-info    { color: var(--sky);         border-color: #c5d2e3; background: var(--sky-bg); }
    .msg-error::before, .msg-success::before, .msg-info::before {
      content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor;
    }

    /* BADGES */
    .badge {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 2px 8px;
      border-radius: var(--r-pill);
      font-family: var(--font-mono);
      font-size: 10.5px; font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      border: 1px solid;
    }
    .badge::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
    .badge-critica     { color: var(--sev-critica); border-color: #e8b8b3; background: var(--sev-critica-bg); }
    .badge-alta        { color: var(--sev-alta);    border-color: #e8c89a; background: var(--sev-alta-bg); }
    .badge-media       { color: var(--sev-media);   border-color: #e0d088; background: var(--sev-media-bg); }
    .badge-baja        { color: var(--sev-baja);    border-color: #b9d6bc; background: var(--sev-baja-bg); }
    .badge-informativa { color: var(--sev-info);    border-color: #cdd2d8; background: var(--sev-info-bg); }

    /* PROPS */
    .props { width: 100%; }
    .props .row {
      display: grid;
      grid-template-columns: 160px 1fr;
      gap: var(--s-4);
      padding: var(--s-3) 0;
      border-bottom: 1px solid var(--line-1);
      align-items: start;
    }
    .props .row:last-child { border-bottom: none; }
    .props .k {
      font-family: var(--font-mono);
      font-size: 11px; color: var(--fg-4);
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding-top: 2px;
    }
    .props .v { font-size: 13px; color: var(--fg-1); line-height: 1.55; word-break: break-word; }
    .props .v.mono { font-family: var(--font-mono); font-size: 12px; color: var(--fg-2); }

    /* TABLES */
    .table-wrap {
      border: 1px solid var(--line-1);
      border-radius: var(--r-2);
      overflow: auto;
    }
    table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
    th {
      text-align: left;
      padding: 9px var(--s-3);
      background: var(--surface-2);
      border-bottom: 1px solid var(--line-2);
      font-family: var(--font-mono);
      font-size: 10.5px; font-weight: 500;
      color: var(--fg-3);
      letter-spacing: 0.06em;
      text-transform: uppercase;
      position: sticky; top: 0;
      white-space: nowrap;
    }
    td { padding: 9px var(--s-3); border-bottom: 1px solid var(--line-1); vertical-align: top; color: var(--fg-2); }
    td.mono { font-family: var(--font-mono); font-size: 11.5px; color: var(--fg-2); }
    tr:last-child td { border-bottom: none; }
    tbody tr { transition: background var(--d-fast); }
    tbody tr:hover { background: var(--surface-2); }
    tbody tr:hover td { color: var(--fg-1); }

    /* BARS */
    .bar-row {
      display: grid;
      grid-template-columns: 110px 1fr 40px;
      align-items: center;
      gap: var(--s-3);
      padding: 7px 0;
      font-family: var(--font-mono);
      font-size: 12px;
    }
    .bar-row .k { color: var(--fg-2); }
    .bar-row .n { color: var(--fg-3); text-align: right; }
    .bar-track { height: 6px; background: var(--surface-2); border-radius: 2px; overflow: hidden; }
    .bar-fill {
      height: 100%;
      width: 100%;
      background: linear-gradient(90deg, var(--accent-lo), var(--accent));
      border-radius: 2px;
      transform-origin: left center;
      transform: scaleX(0);
      transition: transform 600ms var(--ease);
    }
    .sev-stack {
      display: flex;
      height: 10px;
      border-radius: 2px;
      overflow: hidden;
      background: var(--surface-2);
      margin-top: var(--s-2);
    }
    .sev-stack > div { height: 100%; transition: width 400ms var(--ease); }
    .sev-stack .s-critica     { background: var(--sev-critica); }
    .sev-stack .s-alta        { background: var(--sev-alta); }
    .sev-stack .s-media       { background: var(--sev-media); }
    .sev-stack .s-baja        { background: var(--sev-baja); }
    .sev-stack .s-informativa { background: var(--sev-info); }
    .sev-legend {
      display: flex; flex-wrap: wrap; gap: var(--s-3);
      margin-top: var(--s-3);
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .sev-legend > span { display: inline-flex; align-items: center; gap: 6px; color: var(--fg-3); }
    .sev-legend > span::before { content: ''; width: 8px; height: 8px; border-radius: 2px; }
    .sev-legend .l-critica::before     { background: var(--sev-critica); }
    .sev-legend .l-alta::before        { background: var(--sev-alta); }
    .sev-legend .l-media::before       { background: var(--sev-media); }
    .sev-legend .l-baja::before        { background: var(--sev-baja); }
    .sev-legend .l-informativa::before { background: var(--sev-info); }

    /* AUDIT LOG */
    .audit-log {
      display: none;
      margin-top: var(--s-4);
      background: #1a2030;
      border: 1px solid var(--line-2);
      border-radius: var(--r-2);
      padding: var(--s-3);
      max-height: 280px;
      overflow-y: auto;
      font-family: var(--font-mono);
      font-size: 11.5px;
      line-height: 1.65;
      color: #c4c5c8;
    }
    .audit-log .log-line { color: #c4c5c8; }
    .audit-log .log-line .ts { color: #6b7280; }
    .audit-log .log-line.err { color: #fca5a5; }
    .audit-log .log-line.ok  { color: #86efac; }
    .audit-log .log-line { padding: 1px 0; }
    .audit-log .log-line .ts { margin-right: 8px; }

    /* GRAPH */
    .graph-toolbar {
      display: flex; align-items: center; gap: var(--s-3);
      flex-wrap: wrap;
      padding: var(--s-3) var(--s-4);
      border-bottom: 1px solid var(--line-1);
      background: var(--surface-2);
    }
    .graph-toolbar label { margin-bottom: 0; }
    .graph-toolbar select { width: auto; min-width: 180px; }
    #graph-msg { font-family: var(--font-mono); font-size: 11px; color: var(--fg-3); margin-left: auto; }

    #graph-container {
      width: 100%;
      height: calc(100vh - 240px);
      min-height: 480px;
      background: #faf7f0;
      background-image: radial-gradient(circle, rgba(60, 50, 30, .14) 1px, transparent 1px);
      background-size: 32px 32px;
      border-top: 1px solid var(--line-1);
      overflow: hidden;
    }
    @media (max-width: 768px) { #graph-container { height: 380px; min-height: 320px; } }

    /* Graph tab: drop the 1280px content cap so the graph card spans wider */
    body.tab-grafo .content,
    body.tab-grafo .page-intro { max-width: none; }
    body.tab-grafo .content { padding-left: var(--s-5); padding-right: var(--s-5); }
    body.tab-grafo .page-intro {
      padding-top: var(--s-5);
      padding-bottom: var(--s-3);
      padding-left: var(--s-5);
      padding-right: var(--s-5);
    }
    body.tab-grafo .page-intro h1 { font-size: 22px; margin-bottom: 4px; }
    body.tab-grafo .page-intro .lead { display: none; }
    body.tab-grafo #graph-container { height: calc(100vh - 200px); }

    .graph-legend {
      display: flex; flex-wrap: wrap; gap: var(--s-4);
      padding: var(--s-3) var(--s-4);
      border-top: 1px solid var(--line-1);
      background: var(--surface-2);
      font-family: var(--font-mono);
      font-size: 11px; color: var(--fg-3);
    }
    .graph-legend .swatch { display: inline-flex; align-items: center; gap: 6px; }
    .graph-legend .swatch::before { content: ''; width: 10px; height: 10px; border-radius: 2px; }
    .graph-legend .sw-asset::before   { background: var(--accent); }
    .graph-legend .sw-control::before { background: var(--sky); }

    /* Floating drawer over the graph (right side) */
    #graph-node-info {
      display: none;
      position: absolute;
      top: var(--s-3);
      right: var(--s-3);
      width: 380px;
      max-width: calc(100% - var(--s-6));
      max-height: calc(100% - var(--s-5));
      background: var(--surface-1);
      border: 1px solid var(--line-2);
      border-radius: var(--r-2);
      overflow: hidden;
      box-shadow:
        0 1px 0 rgba(38, 25, 12, .02),
        0 12px 32px -10px rgba(38, 25, 12, .25);
      z-index: 5;
      animation: drawerIn 220ms var(--ease);
    }
    @keyframes drawerIn {
      from { opacity: 0; transform: translateX(8px); }
      to   { opacity: 1; transform: translateX(0); }
    }
    /* Tipo activo/control se distingue por el badge de la cabecera, no por stripe */
    #graph-node-info .gni-head {
      padding: var(--s-4) var(--s-4) var(--s-3);
      border-bottom: 1px solid var(--line-1);
      display: flex; align-items: flex-start; gap: var(--s-3);
    }
    #graph-node-info .gni-head-text { flex: 1; min-width: 0; }
    #graph-node-info .gni-close {
      width: 28px; height: 28px;
      display: inline-flex; align-items: center; justify-content: center;
      background: transparent;
      border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      color: var(--fg-3);
      cursor: pointer; padding: 0;
      flex-shrink: 0;
      font-family: var(--font-sans); font-size: 14px;
      transition: background var(--d-fast), color var(--d-fast), border-color var(--d-fast);
    }
    #graph-node-info .gni-close:hover { background: var(--surface-2); color: var(--fg-1); border-color: var(--line-3); }
    #graph-node-info .node-title {
      font-size: 15px; font-weight: 600;
      color: var(--fg-1);
      letter-spacing: -0.01em;
      margin-bottom: var(--s-2);
      word-break: break-word;
    }
    #graph-node-info .node-type-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: var(--r-pill);
      font-family: var(--font-mono);
      font-size: 10px; font-weight: 500;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      border: 1px solid;
    }
    #graph-node-info .node-type-badge.asset   { color: var(--accent); border-color: var(--accent-lo); background: var(--accent-bg); }
    #graph-node-info .node-type-badge.control { color: var(--sky); border-color: #6b8aae; background: var(--sky-bg); }
    #graph-node-info .gni-body {
      padding: var(--s-4);
      max-height: calc(100vh - 340px);
      overflow-y: auto;
    }
    #graph-node-info .gni-meta {
      color: var(--fg-2);
      font-size: 13px;
      line-height: 1.55;
    }
    /* Section blocks inside detail panel */
    #graph-node-info .gni-section { margin-bottom: var(--s-4); }
    #graph-node-info .gni-section:last-child { margin-bottom: 0; }
    #graph-node-info .gni-section-label {
      display: block;
      font-family: var(--font-mono);
      font-size: 10px; font-weight: 500;
      color: var(--fg-4);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: var(--s-2);
    }
    #graph-node-info .gni-section p {
      color: var(--fg-1);
      font-size: 13px;
      line-height: 1.6;
      word-break: break-word;
    }
    #graph-node-info .gni-section .mono-block {
      background: var(--surface-2);
      border: 1px solid var(--line-1);
      border-radius: var(--r-1);
      padding: var(--s-3);
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--fg-1);
      white-space: pre-wrap;
      word-break: break-word;
    }
    #graph-node-info .gni-chips { display: flex; flex-wrap: wrap; gap: 6px; }
    #graph-node-info .gni-chip {
      display: inline-block;
      padding: 3px 9px;
      background: var(--accent-bg);
      border: 1px solid #e0d4bd;
      border-radius: var(--r-pill);
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--accent-lo);
    }
    #graph-node-info .gni-chip.sky {
      background: var(--sky-bg);
      border-color: #c5d2e3;
      color: var(--sky);
    }
    #graph-node-info .gni-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    #graph-node-info .gni-list li {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: var(--s-3);
      padding: var(--s-2) var(--s-3);
      background: var(--surface-2);
      border: 1px solid var(--line-1);
      border-radius: var(--r-1);
      margin-bottom: 4px;
      font-size: 12.5px;
      align-items: center;
    }
    #graph-node-info .gni-list li:last-child { margin-bottom: 0; }
    #graph-node-info .gni-list .l-id {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--fg-3);
      margin-right: var(--s-2);
    }
    #graph-node-info .gni-list .l-activo {
      color: var(--fg-1);
      word-break: break-word;
    }
    #graph-node-info .gni-meta-row {
      display: flex; flex-wrap: wrap; gap: var(--s-4);
      padding: var(--s-3) 0 var(--s-4);
      border-bottom: 1px solid var(--line-1);
      margin-bottom: var(--s-4);
    }
    #graph-node-info .gni-meta-row .kv {
      display: flex; flex-direction: column; gap: 2px;
    }
    #graph-node-info .gni-meta-row .kv .k {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--fg-4);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    #graph-node-info .gni-meta-row .kv .v {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--fg-1);
    }

    /* DRIFT */
    .drift-result { font-size: 13px; line-height: 1.55; }
    .drift-banner {
      display: flex; align-items: center; gap: var(--s-3);
      padding: var(--s-3) var(--s-4);
      border-radius: var(--r-2);
      margin-bottom: var(--s-4);
    }
    .drift-banner.detected { background: var(--sev-alta-bg); border: 1px solid #e8c89a; color: var(--sev-alta); }
    .drift-banner.ok       { background: var(--sev-baja-bg); border: 1px solid #b9d6bc; color: var(--sev-baja); }
    .drift-banner strong { color: inherit; font-weight: 600; }
    .drift-section { margin-top: var(--s-4); }
    .drift-section strong {
      display: block;
      font-family: var(--font-mono);
      font-size: 10.5px; font-weight: 500;
      color: var(--fg-3);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: var(--s-2);
    }
    .drift-section p {
      color: var(--fg-1);
      background: var(--surface-2);
      border: 1px solid var(--line-2);
      border-radius: var(--r-1);
      padding: var(--s-3);
      font-family: var(--font-mono);
      font-size: 12px;
      white-space: pre-wrap;
    }
    /* Diff: distincion por tinte de fondo + borde completo (sin side-stripe) */
    .drift-section.diff-old p { border-color: #e0b0ac; background: var(--sev-critica-bg); }
    .drift-section.diff-new p { border-color: #b9d6bc; background: var(--sev-baja-bg); }

    /* COPILOT */
    .copilot-meta {
      display: flex; align-items: center; gap: var(--s-4);
      padding: var(--s-2) 0 var(--s-3);
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .conf-meter { display: flex; align-items: center; gap: var(--s-2); color: var(--fg-3); }
    .conf-bar {
      width: 120px; height: 4px;
      background: var(--surface-2);
      border-radius: 2px;
      overflow: hidden;
    }
    .conf-bar > div { height: 100%; width: 100%; transform-origin: left center; transform: scaleX(0); transition: transform 500ms var(--ease); }
    .copilot-sources { display: flex; flex-wrap: wrap; gap: 6px; }
    .copilot-sources .src {
      display: inline-block;
      padding: 2px 8px;
      background: var(--surface-2);
      border: 1px solid var(--line-2);
      border-radius: var(--r-pill);
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--fg-2);
    }
    #copilot-result {
      margin-top: var(--s-3);
      padding: var(--s-4);
      background: var(--surface-2);
      border: 1px solid var(--line-2);
      border-radius: var(--r-2);
      font-size: 14px;
      line-height: 1.7;
      color: var(--fg-1);
      white-space: pre-wrap;
    }

    /* HELPERS */
    .empty {
      color: var(--fg-4);
      font-size: 12.5px;
      text-align: center;
      padding: var(--s-6) 0;
      font-family: var(--font-mono);
    }
    .mt-3 { margin-top: var(--s-3); }
    .mt-4 { margin-top: var(--s-4); }
    .mt-5 { margin-top: var(--s-5); }
    .text-mono { font-family: var(--font-mono); font-size: 12px; color: var(--fg-2); }
    .row-flex { display: flex; align-items: center; gap: var(--s-3); flex-wrap: wrap; }
    .text-muted { color: var(--fg-3); }

    #findings-count {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--fg-3);
      margin-bottom: var(--s-3);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    #findings-count b { color: var(--fg-1); font-weight: 500; }

    .dropzone {
      border: 1.5px dashed var(--line-2);
      border-radius: var(--r-2);
      padding: var(--s-7) var(--s-4);
      text-align: center;
      transition: all var(--d-fast) var(--ease);
      cursor: pointer;
      background: var(--surface-2);
    }
    .dropzone:hover, .dropzone.drag {
      border-color: var(--accent);
      background: var(--accent-bg);
    }
    .dropzone .dz-title { font-size: 14px; font-weight: 500; color: var(--fg-1); margin-bottom: var(--s-1); }
    .dropzone .dz-sub { font-family: var(--font-mono); font-size: 11px; color: var(--fg-3); }
    .dropzone input[type="file"] { display: block; margin: var(--s-3) auto 0; width: auto; }
  </style>
</head>
<body>

  <!-- ═══ SIDEBAR ═══ -->
  <nav id="nav-tabs" aria-label="Navegación principal">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true"></div>
      <div class="brand-text">
        <div class="brand-name">ROSETTA</div>
        <div class="brand-tag">Compliance · v0.1</div>
      </div>
    </div>

    <div class="status-pill" id="api-status">
      <span class="status-dot" id="status-dot"></span>
      <span id="status-label">Comprobando…</span>
    </div>

    <div class="nav-section">Vista general</div>
    <button class="active" onclick="switchTab('inicio',this)" aria-current="page">
      Inicio <span class="nav-key">0</span>
    </button>

    <div class="nav-section">Análisis</div>
    <button onclick="switchTab('traductor',this)">
      Traducir <span class="nav-key">1</span>
    </button>
    <button onclick="switchTab('pdf',this)">
      Ingesta PDF <span class="nav-key">2</span>
    </button>
    <button onclick="switchTab('auditoria',this)">
      Modo Auditoría <span class="nav-key">3</span>
    </button>
    <button onclick="switchTab('drift',this)">
      Procedure Drift <span class="nav-key">4</span>
    </button>

    <div class="nav-section">Inteligencia</div>
    <button onclick="switchTab('cumplimiento',this)">
      Cumplimiento <span class="nav-key">5</span>
    </button>
    <button onclick="switchTab('blue',this)">
      Blue Team <span class="nav-key">6</span>
    </button>
    <button onclick="switchTab('grafo',this)">
      Grafo <span class="nav-key">7</span>
    </button>

    <div class="nav-section">Asistencia</div>
    <button onclick="switchTab('copilot',this)">
      Copilot <span class="nav-key">8</span>
    </button>

    <div class="nav-section">Datos</div>
    <button onclick="switchTab('hallazgos',this)">
      Hallazgos <span class="nav-key">9</span>
    </button>

    <div class="nav-footer">
      <div class="nav-footer-row"><span>marco</span><span class="v">iso_27001_2022</span></div>
      <div class="nav-footer-row"><span>llm</span><span class="v" id="footer-llm">claude</span></div>
      <div class="nav-footer-row"><span>session</span><span class="v">sqlite</span></div>
    </div>
  </nav>

  <!-- ═══ MAIN ═══ -->
  <div class="main">

    <div class="topbar" role="banner">
      <button class="icon-btn" id="sidebar-toggle" onclick="toggleSidebar()" aria-label="Ocultar o mostrar sidebar" title="Ocultar / mostrar sidebar  ·  \\">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="2" y="3" width="12" height="10" rx="1.5"/>
          <line x1="6" y1="3" x2="6" y2="13"/>
        </svg>
      </button>
      <div class="breadcrumb">
        <span>Rosetta</span>
        <span class="sep">/</span>
        <span id="bc-current">Inicio</span>
      </div>
      <div class="spacer"></div>
      <div class="topbar-meta">
        <span><b>7</b> marcos activos</span>
        <span><b id="tb-findings">—</b> hallazgos</span>
      </div>
    </div>

    <!-- INICIO -->
    <div id="tab-inicio" class="tab-panel active">
      <div class="page-intro">
        <div class="eyebrow">Vista general</div>
        <h1>Estado del programa de cumplimiento.</h1>
        <p class="lead">Indicadores clave de la sesión: hallazgos detectados, distribución por severidad, marcos más afectados y controles con mayor incidencia.</p>
      </div>
      <div class="content">
        <div id="inicio-kpis"><div class="empty">Cargando KPIs…</div></div>
      </div>
    </div>

    <!-- TRADUCIR -->
    <div id="tab-traductor" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Traductor Simbiótico</div>
        <h1>De hallazgo técnico a evidencia normativa.</h1>
        <p class="lead">Convierte un hallazgo Red Team en controles incumplidos, citas literales y acciones de mitigación auditables. Tool-use forzado sobre Claude Sonnet 4.6 con RAG por marco.</p>
      </div>
      <div class="content">
        <div class="card">
          <div class="card-head">
            <h2>Última evidencia normativa</h2>
            <button class="btn" onclick="openFindingModal()">+ Traducir hallazgo</button>
          </div>
          <div class="card-body">
            <div id="translate-result">
              <div class="empty-guide">
                <div class="empty-guide-title">Traduce tu primer hallazgo</div>
                <ol class="empty-guide-steps">
                  <li>Pulsa <strong>+ Traducir hallazgo</strong> arriba a la derecha.</li>
                  <li>Rellena los datos del activo afectado y marca los marcos normativos.</li>
                  <li>ROSETTA devuelve los controles incumplidos, la cita literal y la acción de mitigación.</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
        <div class="card" style="margin-top:var(--s-4)">
          <div class="card-head"><h2>Traducciones de la sesión</h2><span class="meta" id="recent-count"></span></div>
          <div class="card-body">
            <div id="recent-translations"><div class="empty">Cargando…</div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL: nuevo hallazgo -->
    <div class="modal-overlay" id="finding-modal" aria-hidden="true" onclick="if(event.target===this)closeFindingModal()">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="finding-modal-title">
        <div class="modal-head">
          <h2 id="finding-modal-title">Nuevo hallazgo</h2>
          <button class="modal-close" onclick="closeFindingModal()" aria-label="Cerrar">&times;</button>
        </div>
        <div class="modal-body">
              <div class="row-flex" style="margin-bottom:var(--s-4)">
                <label for="example-select" style="margin-bottom:0">Cargar ejemplo</label>
                <select id="example-select" onchange="loadExample(this.value)" style="width:auto; min-width:240px">
                  <option value="">Ninguno · empezar en blanco</option>
                  <option value="critica">Crítica · clave AWS root + PII</option>
                  <option value="alta">Alta · SQLi en login producción</option>
                  <option value="media">Media · TLS 1.0 en ERP staging</option>
                  <option value="baja">Baja · cabecera revela el stack</option>
                  <option value="informativa">Informativa · cookie sin SameSite</option>
                </select>
              </div>

              <!-- MODO FORMULARIO -->
              <div id="finding-form">
                <div class="field-grid">
                  <div>
                    <label for="f-origen">Origen</label>
                    <select id="f-origen">
                      <option value="nuclei">nuclei · escáner vulnerabilidades</option>
                      <option value="nmap">nmap · escaneo de red</option>
                      <option value="amass">amass · enumeración dominios</option>
                      <option value="subfinder">subfinder · subdominios</option>
                      <option value="theharvester">theharvester · OSINT</option>
                      <option value="shodan">shodan · activos expuestos</option>
                      <option value="hibp">hibp · credenciales filtradas</option>
                      <option value="github_secrets">github_secrets · secretos en repos</option>
                      <option value="manual">manual · revisión humana</option>
                      <option value="otro">otro</option>
                    </select>
                  </div>
                  <div>
                    <label for="f-dificultad">Dificultad de explotación</label>
                    <select id="f-dificultad">
                      <option value="informativa">informativa</option>
                      <option value="baja">baja</option>
                      <option value="media" selected>media</option>
                      <option value="alta">alta</option>
                      <option value="critica">crítica</option>
                    </select>
                  </div>
                </div>
                <label class="mt-3" for="f-activo">Activo detectado</label>
                <input type="text" id="f-activo" placeholder="URL, IP, subdominio o nombre del activo afectado">
                <label class="mt-3" for="f-evidencia">Evidencia</label>
                <input type="text" id="f-evidencia" placeholder="Enlace, hash o log que prueba el hallazgo">
                <label class="mt-3" for="f-vector">Vector de ataque</label>
                <textarea id="f-vector" style="min-height:80px" placeholder="Descripción breve de cómo se explota o qué expone"></textarea>
                <label class="mt-3" for="f-cve">CVE / CWE relacionado <small>· opcional</small></label>
                <input type="text" id="f-cve" placeholder="CVE-2024-XXXXX o CWE-XXX · déjalo vacío si no aplica">
              </div>

              <!-- MODO JSON AVANZADO -->
              <div id="finding-json-wrap" style="display:none">
                <label for="finding-json">Hallazgo · DatosRedTeam (JSON)</label>
                <textarea id="finding-json" spellcheck="false"></textarea>
              </div>

              <button type="button" class="mode-toggle" onclick="toggleFindingMode()">
                <span id="mode-toggle-label">Cambiar a modo JSON avanzado</span>
              </button>

              <label class="mt-4">Marcos normativos</label>
              <p class="field-help">Marcos regulatorios contra los que traducir <strong>este</strong> hallazgo.</p>
              <label class="marco-toggle-all"><input type="checkbox" id="marco-all" onchange="toggleAllMarcos()"> Seleccionar todos los marcos</label>
              <div class="marco-grid">
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="iso_27001_2022" checked onchange="syncMarcoAll()"> ISO 27001:2022</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="iso_27002_2022" onchange="syncMarcoAll()"> ISO 27002:2022</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="ens_2022" onchange="syncMarcoAll()"> ENS 2022</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="nis2" onchange="syncMarcoAll()"> NIS2</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="dora" onchange="syncMarcoAll()"> DORA</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="rgpd" onchange="syncMarcoAll()"> RGPD</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="nist_csf_2" onchange="syncMarcoAll()"> NIST CSF 2.0</label>
                <label class="marco-item"><input type="checkbox" class="marco-cb" value="pci_dss_4" onchange="syncMarcoAll()"> PCI-DSS 4.0</label>
              </div>
        </div>
        <div class="modal-foot">
          <div id="translate-msg"></div>
          <button class="btn btn--ghost" onclick="clearFinding()">Limpiar</button>
          <button class="btn" id="btn-translate" onclick="doTranslate()">Traducir hallazgo</button>
        </div>
      </div>
    </div>

    <!-- CUMPLIMIENTO -->
    <div id="tab-cumplimiento" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Estado de cumplimiento</div>
        <h1>Visibilidad agregada por marco.</h1>
        <p class="lead">Top controles incumplidos, distribución de severidad y total de hallazgos por marco regulatorio. Consulta Neo4j si está disponible; degradación grácil a memoria.</p>
      </div>
      <div class="content">
        <div class="card">
          <div class="card-head"><h2>Consulta</h2><span class="meta">GET /compliance/state/{marco}</span></div>
          <div class="card-body">
            <div class="row-flex">
              <div style="flex:1; min-width:220px">
                <label for="state-marco">Marco a consultar</label>
                <p class="field-help">Estado de cumplimiento global de <strong>todos</strong> los hallazgos contra el marco elegido.</p>
                <select id="state-marco">
                  <option value="iso_27001_2022">ISO 27001:2022</option>
                  <option value="ens_2022">ENS 2022</option>
                  <option value="nis2">NIS2</option>
                  <option value="dora">DORA</option>
                  <option value="rgpd">RGPD</option>
                  <option value="nist_csf_2">NIST CSF 2.0</option>
                  <option value="pci_dss_4">PCI-DSS 4.0</option>
                </select>
              </div>
              <button class="btn" onclick="doComplianceState()" style="align-self:flex-end">Consultar</button>
            </div>
            <div id="state-result" class="mt-5"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODO A -->
    <div id="tab-auditoria" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Auditoría automática Red Team</div>
        <h1>Escaneo en tiempo real con streaming.</h1>
        <p class="lead">Orquesta Nuclei y Nmap sobre los objetivos autorizados. Progreso vía WebSocket con replay para reconexiones tardías. Cada hallazgo se registra en sesión.</p>
      </div>
      <div class="content">
        <div class="card">
          <div class="card-head"><h2>Parámetros</h2><span class="meta">POST /audit/start</span></div>
          <div class="card-body">
            <label for="audit-objetivos">Objetivos autorizados <small>· uno por línea</small></label>
            <textarea id="audit-objetivos" style="min-height:80px" spellcheck="false">https://ejemplo.com</textarea>
            <label class="mt-4">Adaptadores</label>
            <div class="row-flex">
              <label style="display:inline-flex; align-items:center; gap:8px; margin-bottom:0; text-transform:none; letter-spacing:0; font-family:var(--font-sans); font-size:13px; color:var(--fg-2)">
                <input type="checkbox" id="chk-nuclei" checked> nuclei
              </label>
              <label style="display:inline-flex; align-items:center; gap:8px; margin-bottom:0; text-transform:none; letter-spacing:0; font-family:var(--font-sans); font-size:13px; color:var(--fg-2)">
                <input type="checkbox" id="chk-nmap"> nmap
              </label>
            </div>
            <label class="mt-4" for="audit-alcance">Declaración de alcance <small>· mínimo 10 caracteres</small></label>
            <textarea id="audit-alcance" style="min-height:60px" placeholder="Autorizado por el CISO para escanear staging el 2026-05-24."></textarea>
            <div class="mt-4">
              <button class="btn" id="btn-audit" onclick="startAudit()">Iniciar auditoría</button>
              <div id="audit-msg"></div>
            </div>
            <div id="audit-log" class="audit-log" role="log" aria-live="polite"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- PDF -->
    <div id="tab-pdf" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Ingesta de informes</div>
        <h1>Convierte un PDF de auditoría en hallazgos estructurados.</h1>
        <p class="lead">pdfplumber para texto digital; fallback a visión LLM (pypdfium2 + Claude) en páginas escaneadas. Cada hallazgo extraído se registra como HallazgoMaestro.</p>
      </div>
      <div class="content">
        <div class="card">
          <div class="card-head"><h2>Documento</h2><span class="meta">multipart · max 200 MB</span></div>
          <div class="card-body">
            <label class="dropzone" id="pdf-drop">
              <div class="dz-title">Arrastra el PDF aquí o haz clic para seleccionar</div>
              <div class="dz-sub">.pdf · informes de auditoría, pentest, gap analysis</div>
              <input type="file" id="pdf-file" accept=".pdf">
            </label>
            <div class="mt-4">
              <button class="btn" id="btn-ingest" onclick="doIngestPdf()">Extraer hallazgos</button>
              <div id="ingest-msg"></div>
            </div>
            <div id="ingest-result" class="mt-5"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- BLUE -->
    <div id="tab-blue" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Correlación Red ↔ Blue</div>
        <h1>Alertas Wazuh cruzadas con hallazgos.</h1>
        <p class="lead">Ingesta offline JSON o CSV. Mide cobertura defensiva real: ¿qué activos detectados por Red Team tienen además alertas Blue Team correlacionadas?</p>
      </div>
      <div class="content">
        <div class="card">
          <div class="card-head"><h2>Payload</h2><span class="meta">POST /blue/ingest</span></div>
          <div class="card-body">
            <label>Formato</label>
            <div class="row-flex">
              <label style="display:inline-flex; align-items:center; gap:8px; margin-bottom:0; text-transform:none; letter-spacing:0; font-family:var(--font-sans); font-size:13px; color:var(--fg-2)">
                <input type="radio" name="blue-fmt" value="json" checked> JSON
              </label>
              <label style="display:inline-flex; align-items:center; gap:8px; margin-bottom:0; text-transform:none; letter-spacing:0; font-family:var(--font-sans); font-size:13px; color:var(--fg-2)">
                <input type="radio" name="blue-fmt" value="csv"> CSV
              </label>
            </div>
            <label class="mt-4" for="blue-data">Alertas</label>
            <textarea id="blue-data" style="min-height:120px" placeholder='[{"id":"1","timestamp":"2026-04-24T10:00:00","rule":{"id":"5710","level":7,"description":"SSH brute force"},"agent":{"id":"001","name":"srv-web","ip":"1.2.3.4"}}]'></textarea>
            <div class="mt-4">
              <button class="btn" id="btn-blue" onclick="doBlueIngest()">Ingestar alertas</button>
              <div id="blue-msg"></div>
            </div>
            <div id="blue-result" class="mt-5"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- GRAFO -->
    <div id="tab-grafo" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Grafo de correlación</div>
        <h1>Activo → control, en un solo plano.</h1>
        <p class="lead">Vista interactiva estilo Maltego: cada nodo es un activo afectado o un control incumplido. Arrastra para reorganizar, click para detalles, scroll para zoom.</p>
      </div>
      <div class="content">
        <div class="card card-body--flush" style="position:relative">
          <div class="graph-toolbar">
            <div style="display:flex; align-items:center; gap:8px">
              <label for="graph-marco" style="margin-bottom:0">Filtrar por marco</label>
              <select id="graph-marco" title="Muestra solo los nodos activo y control del marco elegido. 'Todos' no filtra.">
                <option value="">Todos los marcos</option>
                <option value="iso_27001_2022">ISO 27001:2022</option>
                <option value="ens_2022">ENS 2022</option>
                <option value="nis2">NIS2</option>
                <option value="dora">DORA</option>
                <option value="rgpd">RGPD</option>
                <option value="nist_csf_2">NIST CSF 2.0</option>
                <option value="pci_dss_4">PCI-DSS 4.0</option>
              </select>
            </div>
            <button class="btn" onclick="loadGraph()">Cargar</button>
            <button class="btn btn--ghost" onclick="togglePhysics()" id="btn-physics">Fijar nodos</button>
            <button class="btn btn--ghost" onclick="fitGraph()">Centrar</button>
            <label style="display:inline-flex; align-items:center; gap:6px; margin:0; font-family:var(--font-sans); font-size:12px; color:var(--fg-3); text-transform:none; letter-spacing:0">
              <input type="checkbox" id="graph-incluir-archivados" onchange="loadGraph()"> incluir archivados
            </label>
            <span id="graph-msg"></span>
          </div>
          <div id="graph-container"></div>
          <div class="graph-legend">
            <span class="swatch sw-asset">Activo con hallazgo</span>
            <span class="swatch sw-control">Control normativo</span>
            <span style="margin-left:auto; color:var(--fg-4)">arrastra · click · scroll</span>
          </div>
          <div id="graph-node-info" role="dialog" aria-labelledby="gni-title">
            <div class="gni-head">
              <div class="gni-head-text">
                <div class="node-title" id="gni-title"></div>
                <span class="node-type-badge" id="gni-badge"></span>
              </div>
              <button class="gni-close" onclick="document.getElementById('graph-node-info').style.display='none'" aria-label="Cerrar panel">×</button>
            </div>
            <div class="gni-body">
              <div class="gni-meta" id="gni-meta"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- DRIFT -->
    <div id="tab-drift" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Procedure drift</div>
        <h1>Detecta si lo escrito y lo real divergen.</h1>
        <p class="lead">El procedimiento dice una cosa; las alertas Wazuh y los logs cuentan otra. ROSETTA identifica la desviación, propone redacción nueva y mapea los controles afectados.</p>
      </div>
      <div class="content">
        <div class="grid-2">
          <div class="card">
            <div class="card-head"><h2>Input</h2><span class="meta">procedimiento + observaciones</span></div>
            <div class="card-body">
              <label for="drift-proc">Procedimiento escrito</label>
              <textarea id="drift-proc" style="min-height:180px" placeholder="Pega aquí el procedimiento interno de seguridad (IAM, accesos, respuesta a incidentes…)"></textarea>
              <label class="mt-4" for="drift-obs">Observaciones reales <small>· una por línea</small></label>
              <textarea id="drift-obs" style="min-height:120px" placeholder="Log Wazuh: usuario admin activo 90 días sin rotación&#10;Alerta: acceso desde IP no corporativa sin MFA&#10;Nuclei: endpoint /api/admin sin autenticación"></textarea>
              <div class="mt-4">
                <button class="btn" id="btn-drift" onclick="doDrift()">Detectar drift</button>
                <div id="drift-msg"></div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-head"><h2>Análisis</h2><span class="meta">ResultadoDrift</span></div>
            <div class="card-body">
              <div id="drift-result"><div class="empty">Ejecuta el análisis para ver el resultado.</div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- COPILOT -->
    <div id="tab-copilot" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Copilot normativo</div>
        <h1>Pregunta libre sobre el corpus regulatorio.</h1>
        <p class="lead">RAG sobre 7 marcos. Respuestas fundamentadas con citas a los controles fuente y nivel de confianza calculado proporcional a la cobertura RAG.</p>
      </div>
      <div class="content">
        <div class="card">
          <div class="card-head"><h2>Consulta</h2><span class="meta">POST /copilot/ask</span></div>
          <div class="card-body">
            <label for="copilot-pregunta">Pregunta</label>
            <textarea id="copilot-pregunta" style="min-height:80px" placeholder="¿Qué control ISO 27001 aplica cuando se expone una clave de cifrado en un repositorio público?"></textarea>
            <label class="mt-4" for="copilot-contexto">Contexto operativo <small>· opcional</small></label>
            <textarea id="copilot-contexto" style="min-height:60px" placeholder="Sistema de pagos PCI-DSS en producción, sector financiero."></textarea>
            <div class="mt-4">
              <button class="btn" id="btn-copilot" onclick="doCopilot()">Preguntar al Copilot</button>
              <div id="copilot-msg"></div>
            </div>
            <div id="copilot-result"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- HALLAZGOS -->
    <div id="tab-hallazgos" class="tab-panel">
      <div class="page-intro">
        <div class="eyebrow">Hallazgos de sesión</div>
        <h1>Registro persistente.</h1>
        <p class="lead">Cada hallazgo traducido, ingerido por PDF, generado por Modo A o detectado por el Gate de CI/CD se almacena en SQLite. Filtra por estado o fecha y archiva hallazgos resueltos.</p>
      </div>
      <div class="content">
        <div class="card" style="margin-bottom:var(--s-4)">
          <div class="card-head"><h2>Filtros</h2><span class="meta">Excluye solucionados por defecto</span></div>
          <div class="card-body">
            <div class="row-flex" style="align-items:flex-end">
              <div style="min-width:160px">
                <label for="findings-estado">Estado</label>
                <select id="findings-estado" onchange="loadFindings()">
                  <option value="">Activos + en progreso</option>
                  <option value="activo">Solo activos</option>
                  <option value="en_progreso">Solo en progreso</option>
                  <option value="solucionado">Solo solucionados</option>
                  <option value="all">Todos (incl. archivados)</option>
                </select>
              </div>
              <div style="min-width:160px">
                <label for="findings-desde">Desde</label>
                <input type="date" id="findings-desde" onchange="loadFindings()">
              </div>
              <div style="min-width:160px">
                <label for="findings-hasta">Hasta</label>
                <input type="date" id="findings-hasta" onchange="loadFindings()">
              </div>
              <button class="btn btn--ghost" onclick="clearFindingFilters()" style="margin-top:0">Limpiar</button>
              <button class="btn btn--ghost" onclick="loadFindings()" style="margin-top:0">↻ Refrescar</button>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><h2>Listado</h2><span class="meta" id="findings-count"></span></div>
          <div class="card-body">
            <div id="findings-table"><div class="empty">Cargando hallazgos…</div></div>
          </div>
        </div>
      </div>
    </div>

  </div><!-- /.main -->

  <script>
    const API = '';
    const TAB_LABELS = {
      'inicio':'Inicio','traductor':'Traducir','cumplimiento':'Cumplimiento','auditoria':'Modo Auditoría',
      'pdf':'Ingesta PDF','blue':'Blue Team','grafo':'Grafo','drift':'Procedure Drift',
      'copilot':'Copilot','hallazgos':'Hallazgos',
    };
    let _graphNetwork = null;
    let _graphNodes   = null;
    let _physicsOn    = true;

    const MARCO_SHORT = {
      'iso_27001_2022': 'ISO 27001',
      'iso_27002_2022': 'ISO 27002',
      'ens_2022':       'ENS',
      'nis2':           'NIS2',
      'dora':           'DORA',
      'rgpd':           'RGPD',
      'nist_csf_2':     'NIST CSF',
      'pci_dss_4':      'PCI-DSS',
    };
    function marcoShort(m) { return MARCO_SHORT[m] || m; }

    function setMsg(id, html) { const el = document.getElementById(id); if (el) el.innerHTML = html; }
    function msgErr(id, t)  { setMsg(id, '<div class="msg-error">'   + t + '</div>'); }
    function msgOk(id, t)   { setMsg(id, '<div class="msg-success">' + t + '</div>'); }
    function msgInfo(id, t) { setMsg(id, '<div class="msg-info">'    + t + '</div>'); }
    function esc(s) { return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
    function badgeHtml(sev) { const s = sev || 'media'; return '<span class="badge badge-' + s + '">' + s + '</span>'; }

    function switchTab(name, btn) {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('nav button').forEach(b => { b.classList.remove('active'); b.removeAttribute('aria-current'); });
      document.getElementById('tab-' + name).classList.add('active');
      if (btn) { btn.classList.add('active'); btn.setAttribute('aria-current', 'page'); }
      document.getElementById('bc-current').textContent = TAB_LABELS[name] || name;
      /* Tag <body> with active tab so per-tab layout overrides can apply */
      document.body.classList.forEach(c => { if (c.startsWith('tab-')) document.body.classList.remove(c); });
      document.body.classList.add('tab-' + name);
      try { sessionStorage.setItem('rosetta:tab', name); } catch (_) {}
      if (name === 'hallazgos') loadFindings();
      if (name === 'grafo') {
        loadGraph();
        /* Re-fit graph after layout settles (container size changed) */
        setTimeout(function() { if (_graphNetwork) { try { _graphNetwork.redraw(); _graphNetwork.fit({ animation: false }); } catch (_) {} } }, 260);
      }
    }

    /* ── Sidebar collapse toggle ───────────────────────────────────── */
    function toggleSidebar(force) {
      const collapsed = typeof force === 'boolean' ? force : !document.body.classList.contains('sidebar-collapsed');
      document.body.classList.toggle('sidebar-collapsed', collapsed);
      try { localStorage.setItem('rosetta:sidebar', collapsed ? '1' : '0'); } catch (_) {}
      const btn = document.getElementById('sidebar-toggle');
      if (btn) btn.setAttribute('aria-pressed', String(collapsed));
      /* Re-fit graph if visible (sidebar collapse changes available width) */
      setTimeout(function() { if (_graphNetwork) { try { _graphNetwork.redraw(); _graphNetwork.fit({ animation: false }); } catch (_) {} } }, 220);
    }
    try {
      if (localStorage.getItem('rosetta:sidebar') === '1') document.body.classList.add('sidebar-collapsed');
    } catch (_) {}

    document.addEventListener('keydown', function(ev) {
      if (ev.key === 'Escape') {
        const m = document.getElementById('finding-modal');
        if (m && m.classList.contains('open')) { closeFindingModal(); return; }
      }
      if (ev.target.matches('textarea, input, select')) return;
      if (ev.key === '\\\\') { ev.preventDefault(); toggleSidebar(); return; }
      const map = { '0':'inicio','1':'traductor','2':'pdf','3':'auditoria','4':'drift','5':'cumplimiento','6':'blue','7':'grafo','8':'copilot','9':'hallazgos' };
      if (map[ev.key]) {
        ev.preventDefault();
        const idx = Object.keys(map).indexOf(ev.key);
        const btns = document.querySelectorAll('nav button');
        if (btns[idx]) btns[idx].click();
      }
    });

    async function checkHealth() {
      const dot = document.getElementById('status-dot');
      const lbl = document.getElementById('status-label');
      try {
        const r = await fetch(API + '/health');
        const d = await r.json();
        dot.className = 'status-dot ok';
        lbl.textContent = 'API ' + (d.version || 'ok');
      } catch (_) {
        dot.className = 'status-dot err';
        lbl.textContent = 'API no disponible';
      }
    }

    /* ── Modo formulario vs JSON avanzado ──────────────────────────── */
    let _findingJsonMode = false;

    function buildFindingFromForm() {
      const cve = document.getElementById('f-cve').value.trim();
      const h = {
        origen: document.getElementById('f-origen').value,
        activo_detectado: document.getElementById('f-activo').value.trim(),
        evidencia: document.getElementById('f-evidencia').value.trim(),
        vector_ataque: document.getElementById('f-vector').value.trim(),
        dificultad_explotacion: document.getElementById('f-dificultad').value,
      };
      if (cve) h.cve_relacionado = cve;
      return h;
    }

    function fillFindingForm(h) {
      h = h || {};
      if (h.origen) document.getElementById('f-origen').value = h.origen;
      if (h.dificultad_explotacion) document.getElementById('f-dificultad').value = h.dificultad_explotacion;
      document.getElementById('f-activo').value = h.activo_detectado || '';
      document.getElementById('f-evidencia').value = h.evidencia || '';
      document.getElementById('f-vector').value = h.vector_ataque || '';
      document.getElementById('f-cve').value = h.cve_relacionado || '';
    }

    function toggleFindingMode() {
      const form = document.getElementById('finding-form');
      const jsonWrap = document.getElementById('finding-json-wrap');
      const label = document.getElementById('mode-toggle-label');
      _findingJsonMode = !_findingJsonMode;
      if (_findingJsonMode) {
        /* form → json: vuelca el formulario al textarea */
        document.getElementById('finding-json').value = JSON.stringify(buildFindingFromForm(), null, 2);
        form.style.display = 'none';
        jsonWrap.style.display = 'block';
        label.textContent = 'Volver al modo formulario';
      } else {
        /* json → form: intenta parsear el textarea al formulario */
        try {
          const parsed = JSON.parse(document.getElementById('finding-json').value || '{}');
          fillFindingForm(parsed);
        } catch (_) {}
        jsonWrap.style.display = 'none';
        form.style.display = 'block';
        label.textContent = 'Cambiar a modo JSON avanzado';
      }
    }

    function clearFinding() {
      fillFindingForm({ dificultad_explotacion: 'media', origen: 'nuclei' });
      document.getElementById('finding-json').value = '';
      document.getElementById('example-select').value = '';
      setMsg('translate-msg', '');
    }

    /* ── Modal de hallazgo ─────────────────────────────────────────── */
    function openFindingModal() {
      const m = document.getElementById('finding-modal');
      m.classList.add('open');
      m.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }
    function closeFindingModal() {
      const m = document.getElementById('finding-modal');
      m.classList.remove('open');
      m.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    /* ── Marcos: seleccionar todos / sincronizar ───────────────────── */
    function toggleAllMarcos() {
      const all = document.getElementById('marco-all').checked;
      document.querySelectorAll('.marco-cb').forEach(cb => { cb.checked = all; });
    }
    function syncMarcoAll() {
      const cbs = Array.from(document.querySelectorAll('.marco-cb'));
      const checked = cbs.filter(cb => cb.checked).length;
      const all = document.getElementById('marco-all');
      all.checked = checked === cbs.length;
      all.indeterminate = checked > 0 && checked < cbs.length;
    }

    /* ── Traducciones recientes (tab Traducir) ─────────────────────── */
    async function loadRecentTranslations() {
      const wrap = document.getElementById('recent-translations');
      const cnt = document.getElementById('recent-count');
      if (!wrap) return;
      try {
        const r = await fetch(API + '/findings?limit=6&estado=all');
        const d = await r.json();
        const items = d.items || [];
        if (cnt) cnt.textContent = (d.total || 0) + ' en total';
        if (!items.length) {
          wrap.innerHTML = '<div class="empty">Sin traducciones todavía.</div>';
          return;
        }
        const rows = items.map(f =>
          '<tr>' +
            '<td class="mono">' + esc(f.id_hallazgo) + '</td>' +
            '<td>' + esc(f.activo_detectado) + '</td>' +
            '<td class="mono">' + (f.controles_incumplidos || []).map(esc).join(', ') + '</td>' +
            '<td>' + badgeHtml(f.impacto_legal) + '</td>' +
            '<td class="mono">' + esc((f.timestamp || '').replace('T', ' ').slice(0, 16)) + '</td>' +
          '</tr>'
        ).join('');
        wrap.innerHTML =
          '<div class="table-wrap"><table>' +
            '<thead><tr><th>ID</th><th>Activo</th><th>Controles</th><th>Impacto</th><th>Fecha</th></tr></thead>' +
            '<tbody>' + rows + '</tbody>' +
          '</table></div>';
      } catch (e) {
        wrap.innerHTML = '<div class="msg-error">Error: ' + esc(e.message) + '</div>';
      }
    }

    async function doTranslate() {
      const btn = document.getElementById('btn-translate');
      let hallazgo;
      if (_findingJsonMode) {
        try { hallazgo = JSON.parse(document.getElementById('finding-json').value); }
        catch (e) { msgErr('translate-msg', 'JSON inválido: ' + esc(e.message)); return; }
      } else {
        hallazgo = buildFindingFromForm();
        const faltan = [];
        if (!hallazgo.activo_detectado) faltan.push('Activo detectado');
        if (!hallazgo.evidencia) faltan.push('Evidencia');
        if (!hallazgo.vector_ataque) faltan.push('Vector de ataque');
        if (faltan.length) { msgErr('translate-msg', 'Faltan campos: ' + faltan.join(', ')); return; }
      }
      const opts = Array.from(document.querySelectorAll('.marco-cb:checked')).map(c => c.value);
      if (!opts.length) { msgErr('translate-msg', 'Selecciona al menos un marco normativo.'); return; }
      btn.disabled = true;
      msgInfo('translate-msg', 'Traduciendo hallazgo a marcos seleccionados…');
      setMsg('translate-result', '<div class="empty">Procesando traducción…</div>');
      const body = { hallazgo, marcos: opts };
      try {
        const r = await fetch(API + '/translate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
        const data = await r.json();
        if (!r.ok) {
          msgErr('translate-msg', 'Error ' + r.status + ': ' + esc(data.detail || JSON.stringify(data)));
          setMsg('translate-result', '<div class="empty">Sin resultado.</div>');
        } else {
          renderTranslate(data);
          updateFindingsCount();
          loadRecentTranslations();
          setMsg('translate-msg', '');
          closeFindingModal();
        }
      } catch (e) { msgErr('translate-msg', 'Error de red: ' + esc(e.message)); }
      btn.disabled = false;
    }

    function renderTranslate(data) {
      const marcos = (data.marcos_aplicables || []).map(m =>
        '<span class="badge badge-informativa" style="text-transform:none">' + esc(m) + '</span>'
      ).join(' ');
      const controles = (data.controles_incumplidos || []).map(c =>
        '<span style="display:inline-block; padding:2px 8px; background:var(--surface-2); border:1px solid var(--line-2); border-radius:var(--r-pill); font-family:var(--font-mono); font-size:11px; color:var(--accent-hi); margin:0 4px 4px 0">' + esc(c) + '</span>'
      ).join('');
      const html = '<div class="props">' +
        '<div class="row"><div class="k">Impacto legal</div><div class="v">' + badgeHtml(data.impacto_legal) + '</div></div>' +
        '<div class="row"><div class="k">Marcos aplicables</div><div class="v">' + (marcos || '—') + '</div></div>' +
        '<div class="row"><div class="k">Controles incumplidos</div><div class="v">' + (controles || '<span class="text-muted">—</span>') + '</div></div>' +
        '<div class="row"><div class="k">Cita normativa</div><div class="v mono">' + esc(data.cita_normativa || '—') + '</div></div>' +
        '<div class="row"><div class="k">Justificación</div><div class="v">' + esc(data.justificacion || '—') + '</div></div>' +
        '<div class="row"><div class="k">Acción de mitigación</div><div class="v">' + esc(data.accion_mitigacion || '—') + '</div></div>' +
        '<div class="row"><div class="k">Evidencia auditoría</div><div class="v mono">' + esc(data.evidencia_auditoria || '—') + '</div></div>' +
        '</div>';
      setMsg('translate-result', html);
    }

    async function doComplianceState() {
      const marco = document.getElementById('state-marco').value;
      setMsg('state-result', '<div class="empty">Consultando…</div>');
      try {
        const r = await fetch(API + '/compliance/state/' + marco);
        const d = await r.json();
        if (!r.ok) { setMsg('state-result', '<div class="msg-error">Error ' + r.status + ': ' + esc(d.detail || JSON.stringify(d)) + '</div>'); return; }
        renderComplianceState(d);
      } catch (e) { setMsg('state-result', '<div class="msg-error">Error de red: ' + esc(e.message) + '</div>'); }
    }

    function renderComplianceState(d) {
      const total = d.total_hallazgos || 0;
      const sevDist = d.severidad_distribution || {};
      const sevTotal = Object.values(sevDist).reduce((a, b) => a + b, 0) || 1;
      const sevOrder = ['critica', 'alta', 'media', 'baja', 'informativa'];
      const criticos = (sevDist.critica || 0) + (sevDist.alta || 0);

      let html = '<div class="kpi-strip mt-3">' +
        '<div class="kpi kpi--accent"><div class="kpi-label">Hallazgos totales</div><div class="kpi-value">' + total + '</div></div>' +
        '<div class="kpi kpi--accent"><div class="kpi-label">Crítica + alta</div><div class="kpi-value">' + criticos + '</div></div>' +
        '<div class="kpi kpi--sky"><div class="kpi-label">Controles afectados</div><div class="kpi-value">' + (d.controles_incumplidos || []).length + '</div></div>' +
      '</div>';

      if (d.controles_incumplidos && d.controles_incumplidos.length) {
        const max = Math.max.apply(null, d.controles_incumplidos.map(c => c.total_hallazgos).concat([1]));
        html += '<div class="mt-5"><label>Top controles incumplidos</label>';
        d.controles_incumplidos.forEach(c => {
          const pct = Math.round((c.total_hallazgos / max) * 100);
          html += '<div class="bar-row"><span class="k">' + esc(c.control_id) + '</span><div class="bar-track"><div class="bar-fill" style="transform:scaleX(' + (pct/100) + ')"></div></div><span class="n">' + c.total_hallazgos + '</span></div>';
        });
        html += '</div>';
      }

      if (Object.keys(sevDist).length) {
        html += '<div class="mt-5"><label>Distribución por severidad</label><div class="sev-stack">';
        sevOrder.forEach(s => {
          if (sevDist[s]) {
            const w = (sevDist[s] / sevTotal) * 100;
            html += '<div class="s-' + s + '" style="width:' + w + '%"></div>';
          }
        });
        html += '</div><div class="sev-legend">';
        sevOrder.forEach(s => { if (sevDist[s]) html += '<span class="l-' + s + '">' + s + ' · ' + sevDist[s] + '</span>'; });
        html += '</div></div>';
      }

      if (!total) html = '<div class="empty mt-3">Sin hallazgos para este marco todavía. Traduce alguno para empezar.</div>';
      setMsg('state-result', html);
    }

    async function startAudit() {
      const btn = document.getElementById('btn-audit');
      const logEl = document.getElementById('audit-log');
      const objetivos = document.getElementById('audit-objetivos').value.split('\\n').map(s => s.trim()).filter(Boolean);
      const alcance = document.getElementById('audit-alcance').value.trim();
      const adaptadores = [];
      if (document.getElementById('chk-nuclei').checked) adaptadores.push('nuclei');
      if (document.getElementById('chk-nmap').checked) adaptadores.push('nmap');
      if (!objetivos.length) { msgErr('audit-msg', 'Introduce al menos un objetivo.'); return; }
      if (alcance.length < 10) { msgErr('audit-msg', 'Declaración mínimo 10 caracteres.'); return; }
      btn.disabled = true; logEl.style.display = 'block'; logEl.innerHTML = '';
      msgInfo('audit-msg', 'Iniciando auditoría…');
      let auditId;
      try {
        const r = await fetch(API + '/audit/start', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ objetivos, adaptadores, declaracion_alcance: alcance }) });
        const d = await r.json();
        if (!r.ok) { msgErr('audit-msg', 'Error ' + r.status + ': ' + esc(d.detail || JSON.stringify(d))); btn.disabled = false; return; }
        auditId = d.audit_id;
        msgOk('audit-msg', 'Auditoría ' + esc(auditId) + ' en curso');
      } catch (e) { msgErr('audit-msg', 'Error de red: ' + esc(e.message)); btn.disabled = false; return; }

      const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(wsProto + '://' + location.host + '/audit/ws/' + auditId);
      ws.onmessage = function(ev) {
        const d = JSON.parse(ev.data);
        const cls = d.tipo === 'error' ? 'err' : d.tipo === 'fin' ? 'ok' : '';
        const ts = (d.timestamp || '').slice(11, 19);
        logEl.innerHTML += '<div class="log-line ' + cls + '"><span class="ts">' + esc(ts) + '</span>' + esc(d.mensaje || '') + '</div>';
        logEl.scrollTop = logEl.scrollHeight;
        if (d.tipo === 'fin') {
          msgOk('audit-msg', 'Completada · ' + (d.hallazgos_acumulados || 0) + ' hallazgo(s)');
          btn.disabled = false; updateFindingsCount();
        }
      };
      ws.onerror = function() { msgErr('audit-msg', 'Error en WebSocket'); btn.disabled = false; };
      ws.onclose = function() { if (btn.disabled) btn.disabled = false; };
    }

    (function setupDropzone() {
      const dz = document.getElementById('pdf-drop');
      const input = document.getElementById('pdf-file');
      if (!dz || !input) return;
      ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); dz.classList.add('drag'); }));
      ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); dz.classList.remove('drag'); }));
      dz.addEventListener('drop', e => { const files = e.dataTransfer && e.dataTransfer.files; if (files && files[0]) input.files = files; });
    })();

    async function doIngestPdf() {
      const btn  = document.getElementById('btn-ingest');
      const file = document.getElementById('pdf-file').files && document.getElementById('pdf-file').files[0];
      if (!file) { msgErr('ingest-msg', 'Selecciona un PDF primero.'); return; }
      btn.disabled = true;
      msgInfo('ingest-msg', 'Procesando ' + esc(file.name) + '…');
      setMsg('ingest-result', '<div class="empty">Procesando…</div>');
      const form = new FormData(); form.append('file', file);
      try {
        const r = await fetch(API + '/ingest/pdf', { method:'POST', body: form });
        const d = await r.json();
        if (!r.ok) { msgErr('ingest-msg', 'Error ' + r.status + ': ' + esc(d.detail || JSON.stringify(d))); setMsg('ingest-result', '<div class="empty">—</div>'); }
        else {
          msgOk('ingest-msg', d.total_hallazgos + ' hallazgo(s) extraído(s)');
          const ids = (d.hallazgo_ids || []).slice(0, 5).join(', ');
          const more = (d.hallazgo_ids || []).length > 5 ? ' …' : '';
          const html = '<div class="kpi-strip">' +
            '<div class="kpi kpi--accent"><div class="kpi-label">Hallazgos</div><div class="kpi-value">' + d.total_hallazgos + '</div></div>' +
            '<div class="kpi kpi--sky"><div class="kpi-label">Páginas</div><div class="kpi-value">' + d.paginas_procesadas + '</div></div>' +
            '<div class="kpi"><div class="kpi-label">Páginas útiles</div><div class="kpi-value">' + d.paginas_con_hallazgos + '</div></div>' +
          '</div>' +
          '<div class="mt-4 props">' +
            '<div class="row"><div class="k">Modo de extracción</div><div class="v mono">' + esc(d.modo_extraccion) + '</div></div>' +
            '<div class="row"><div class="k">IDs registrados</div><div class="v mono">' + esc(ids + more) + '</div></div>' +
          '</div>';
          setMsg('ingest-result', html);
          updateFindingsCount();
        }
      } catch (e) { msgErr('ingest-msg', 'Error de red: ' + esc(e.message)); }
      btn.disabled = false;
    }

    async function doBlueIngest() {
      const btn     = document.getElementById('btn-blue');
      const fmt     = document.querySelector('input[name="blue-fmt"]:checked').value;
      const rawData = document.getElementById('blue-data').value.trim();
      if (!rawData) { msgErr('blue-msg', 'Introduce datos JSON o CSV.'); return; }
      btn.disabled = true; msgInfo('blue-msg', 'Procesando…'); setMsg('blue-result', '<div class="empty">Procesando…</div>');
      let body;
      if (fmt === 'json') {
        try { body = { formato:'json', datos_json: JSON.parse(rawData) }; }
        catch (e) { msgErr('blue-msg', 'JSON inválido: ' + esc(e.message)); btn.disabled = false; return; }
      } else { body = { formato:'csv', datos_csv: rawData }; }
      try {
        const r = await fetch(API + '/blue/ingest', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
        const d = await r.json();
        if (!r.ok) { msgErr('blue-msg', 'Error ' + r.status + ': ' + esc(d.detail || JSON.stringify(d))); }
        else {
          const cob = d.resumen_cobertura || {};
          msgOk('blue-msg', d.total_alertas + ' alerta(s) normalizada(s)');
          const pct = cob.porcentaje_cobertura || 0;
          const html = '<div class="kpi-strip">' +
            '<div class="kpi kpi--sky"><div class="kpi-label">Alertas Wazuh</div><div class="kpi-value">' + d.total_alertas + '</div></div>' +
            '<div class="kpi kpi--accent"><div class="kpi-label">Cobertura Red↔Blue</div><div class="kpi-value">' + pct + '%</div><div class="kpi-delta">' + (cob.con_cobertura||0) + ' de ' + (cob.total_hallazgos||0) + '</div></div>' +
            '<div class="kpi"><div class="kpi-label">Sin cobertura</div><div class="kpi-value">' + (cob.sin_cobertura || 0) + '</div></div>' +
          '</div>';
          setMsg('blue-result', html);
        }
      } catch (e) { msgErr('blue-msg', 'Error de red: ' + esc(e.message)); }
      btn.disabled = false;
    }

    /* ── GRAFO ─────────────────────────────────────────────────────── */
    async function loadGraph() {
      const marco = document.getElementById('graph-marco').value;
      const msgEl = document.getElementById('graph-msg');
      const infoEl = document.getElementById('graph-node-info');
      infoEl.style.display = 'none';
      msgEl.textContent = 'Cargando grafo…';
      const url = API + '/graph/data' + (marco ? '?marco=' + marco : '');
      try {
        const r = await fetch(url);
        const d = await r.json();
        if (!r.ok) { msgEl.textContent = 'Error: ' + (d.detail || ''); return; }

        _graphNodes = new vis.DataSet(d.nodes || []);
        const edges = new vis.DataSet(d.edges || []);
        const nodeCount = (d.nodes || []).length;
        const edgeCount = (d.edges || []).length;
        msgEl.textContent = nodeCount + ' nodos · ' + edgeCount + ' aristas';

        const container = document.getElementById('graph-container');

        /* ── Railway/Vercel-style card renderer ─────────────────────── */
        function rrect(ctx, x, y, w, h, r) {
          ctx.beginPath();
          ctx.moveTo(x + r, y);
          ctx.lineTo(x + w - r, y);
          ctx.quadraticCurveTo(x + w, y, x + w, y + r);
          ctx.lineTo(x + w, y + h - r);
          ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
          ctx.lineTo(x + r, y + h);
          ctx.quadraticCurveTo(x, y + h, x, y + h - r);
          ctx.lineTo(x, y + r);
          ctx.quadraticCurveTo(x, y, x + r, y);
          ctx.closePath();
        }

        /* Icon drawers (16px stroke icons drawn at given top-left x,y) */
        function drawIconAsset(ctx, x, y, color) {
          /* triangular warning */
          ctx.save();
          ctx.strokeStyle = color; ctx.fillStyle = 'transparent';
          ctx.lineWidth = 1.6; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
          ctx.beginPath();
          ctx.moveTo(x + 9, y + 1.5);
          ctx.lineTo(x + 16.5, y + 14.5);
          ctx.lineTo(x + 1.5, y + 14.5);
          ctx.closePath();
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(x + 9, y + 6); ctx.lineTo(x + 9, y + 10);
          ctx.stroke();
          ctx.beginPath();
          ctx.arc(x + 9, y + 12.4, 0.6, 0, Math.PI * 2);
          ctx.fillStyle = color; ctx.fill();
          ctx.restore();
        }
        function drawIconControl(ctx, x, y, color) {
          /* document with lines */
          ctx.save();
          ctx.strokeStyle = color; ctx.fillStyle = 'transparent';
          ctx.lineWidth = 1.6; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
          ctx.beginPath();
          ctx.moveTo(x + 3, y + 1.5);
          ctx.lineTo(x + 12, y + 1.5);
          ctx.lineTo(x + 15, y + 4.5);
          ctx.lineTo(x + 15, y + 14.5);
          ctx.lineTo(x + 3, y + 14.5);
          ctx.closePath();
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(x + 12, y + 1.5); ctx.lineTo(x + 12, y + 4.5); ctx.lineTo(x + 15, y + 4.5);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(x + 5.5, y + 8); ctx.lineTo(x + 12.5, y + 8);
          ctx.moveTo(x + 5.5, y + 11); ctx.lineTo(x + 12.5, y + 11);
          ctx.stroke();
          ctx.restore();
        }
        function drawIconCheck(ctx, x, y, color) {
          ctx.save();
          ctx.strokeStyle = color; ctx.lineWidth = 1.7; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
          ctx.beginPath();
          ctx.moveTo(x + 1.5, y + 6.5);
          ctx.lineTo(x + 4.5, y + 9.5);
          ctx.lineTo(x + 10.5, y + 3.5);
          ctx.stroke();
          ctx.restore();
        }
        function drawIconLayer(ctx, x, y, color) {
          /* tag/marco glyph */
          ctx.save();
          ctx.strokeStyle = color; ctx.lineWidth = 1.4; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
          ctx.beginPath();
          ctx.moveTo(x + 1.5, y + 4); ctx.lineTo(x + 7, y + 1); ctx.lineTo(x + 12.5, y + 4);
          ctx.lineTo(x + 12.5, y + 5); ctx.lineTo(x + 7, y + 8); ctx.lineTo(x + 1.5, y + 5); ctx.closePath();
          ctx.stroke();
          ctx.globalAlpha = 0.55;
          ctx.beginPath();
          ctx.moveTo(x + 1.5, y + 7.5); ctx.lineTo(x + 7, y + 10.5); ctx.lineTo(x + 12.5, y + 7.5);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(x + 1.5, y + 10.5); ctx.lineTo(x + 7, y + 13.5); ctx.lineTo(x + 12.5, y + 10.5);
          ctx.stroke();
          ctx.restore();
        }

        const NODE_TYPE = {
          asset:   { iconColor:'#9a6635' /* copper — warning/red-team */ },
          control: { iconColor:'#1e3a5f' /* deep navy — normative */ },
        };

        const W = 300, H = 138, R = 12, PAD = 18;

        function ellipsize(ctx, text, maxW) {
          let t = text || '';
          if (ctx.measureText(t).width <= maxW) return t;
          while (t.length > 1 && ctx.measureText(t + '…').width > maxW) t = t.slice(0, -1);
          return t + '…';
        }

        function makeRenderer(group, nodeData) {
          const type = NODE_TYPE[group] || NODE_TYPE.control;
          /* Build metadata: subtitle, status line, footer */
          const isAsset = group === 'asset';
          const title = (nodeData && nodeData.label) || '';
          /* node.title typically: "SEC-XXXX · activo_completo" (asset) or "A.8.28" (control) */
          const rawTip = (nodeData && nodeData.title) ? String(nodeData.title) : '';
          let subtitle = '';
          if (isAsset) {
            const idMatch = rawTip.match(/^(SEC-[A-Z0-9]+|AUD-[A-Z0-9]+|PDF-[A-Z0-9]+)/);
            subtitle = idMatch ? idMatch[1] : '';
          } else {
            subtitle = 'control normativo';
          }
          const origen = (nodeData && nodeData.origen) ? String(nodeData.origen).replace(/_/g, ' ') : '';
          const statusText = isAsset
            ? (origen ? 'detected via ' + origen : 'detected via red team')
            : 'mapped via translator';
          const marcosArr = (nodeData && Array.isArray(nodeData.marcos)) ? nodeData.marcos : [];

          return {
            drawNode({ ctx, x, y, state: { selected, hover } }) {
              const left = x - W/2;
              const top  = y - H/2;

              /* Card body — premium paper aesthetic */
              ctx.save();
              if (selected || hover) {
                ctx.shadowColor = 'rgba(38, 25, 12, 0.18)';
                ctx.shadowBlur = selected ? 22 : 14;
                ctx.shadowOffsetY = 6;
              } else {
                ctx.shadowColor = 'rgba(38, 25, 12, 0.08)';
                ctx.shadowBlur = 6;
                ctx.shadowOffsetY = 2;
              }
              rrect(ctx, left, top, W, H, R);
              ctx.fillStyle = '#fffdf8';
              ctx.fill();
              ctx.strokeStyle = selected ? '#9a6635' : (hover ? '#a8a18d' : '#d8d2c0');
              ctx.lineWidth = selected ? 1.5 : 1;
              ctx.stroke();
              ctx.restore();

              /* Header row: icon + title */
              const iconX = left + PAD;
              const iconY = top + PAD;
              if (isAsset) drawIconAsset(ctx, iconX, iconY, type.iconColor);
              else         drawIconControl(ctx, iconX, iconY, type.iconColor);

              /* Title */
              ctx.save();
              ctx.fillStyle = '#1a2030';
              ctx.font = '600 14.5px Geist, system-ui, sans-serif';
              ctx.textBaseline = 'top';
              ctx.textAlign = 'left';
              const titleX = iconX + 24;
              const titleMaxW = W - PAD * 2 - 24;
              ctx.fillText(ellipsize(ctx, title, titleMaxW), titleX, iconY + 1);
              ctx.restore();

              /* Subtitle */
              if (subtitle) {
                ctx.save();
                ctx.fillStyle = '#6b7280';
                ctx.font = '500 11.5px "Geist Mono", monospace';
                ctx.textBaseline = 'top';
                ctx.textAlign = 'left';
                ctx.fillText(ellipsize(ctx, subtitle, titleMaxW), titleX, iconY + 19);
                ctx.restore();
              }

              /* Separator */
              const sepY = top + 60;
              ctx.save();
              ctx.strokeStyle = '#ebe6d8';
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(left + PAD, sepY);
              ctx.lineTo(left + W - PAD, sepY);
              ctx.stroke();
              ctx.restore();

              /* Status line: sage check + text */
              const statusY = sepY + 12;
              drawIconCheck(ctx, left + PAD, statusY, '#3d7d4a');
              ctx.save();
              ctx.fillStyle = '#3a4254';
              ctx.font = '500 11.5px Geist, system-ui, sans-serif';
              ctx.textBaseline = 'top';
              ctx.textAlign = 'left';
              ctx.fillText(ellipsize(ctx, statusText, W - PAD * 2 - 18), left + PAD + 18, statusY + 1);
              ctx.restore();

              /* Footer row: layer icon + marco chips */
              const footY = statusY + 22;
              drawIconLayer(ctx, left + PAD, footY, '#9a6635');

              /* Render marco chips inline (overflow → "+N") */
              ctx.save();
              ctx.font = '500 10.5px "Geist Mono", monospace';
              ctx.textBaseline = 'top';
              ctx.textAlign = 'left';
              const chipsStartX = left + PAD + 18;
              const chipsMaxX   = left + W - PAD;
              const chipPadX = 6, chipPadY = 2, chipGap = 4;
              let cursorX = chipsStartX;
              let rendered = 0;
              const labels = (marcosArr.length ? marcosArr : ['—']).map(marcoShort);
              for (let i = 0; i < labels.length; i++) {
                const txt = labels[i];
                const txtW = ctx.measureText(txt).width;
                const chipW = txtW + chipPadX * 2;
                /* Reserve ~28px for possible "+N" suffix */
                const reserve = (i < labels.length - 1) ? 28 : 0;
                if (cursorX + chipW + reserve > chipsMaxX && rendered > 0) {
                  /* Out of space → render "+N" with remaining count */
                  const remaining = labels.length - rendered;
                  const moreTxt = '+' + remaining;
                  const moreW = ctx.measureText(moreTxt).width;
                  ctx.fillStyle = '#f5e9d6';
                  rrect(ctx, cursorX, footY, moreW + chipPadX * 2, 16, 4);
                  ctx.fill();
                  ctx.strokeStyle = '#e0d4bd';
                  ctx.lineWidth = 1;
                  ctx.stroke();
                  ctx.fillStyle = '#7a4f28';
                  ctx.fillText(moreTxt, cursorX + chipPadX, footY + chipPadY);
                  break;
                }
                /* Draw chip background + text */
                ctx.fillStyle = '#f5e9d6';
                rrect(ctx, cursorX, footY, chipW, 16, 4);
                ctx.fill();
                ctx.strokeStyle = '#e0d4bd';
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.fillStyle = '#7a4f28';
                ctx.fillText(txt, cursorX + chipPadX, footY + chipPadY);
                cursorX += chipW + chipGap;
                rendered++;
              }
              ctx.restore();
            },
            nodeDimensions: { width: W, height: H },
          };
        }

        const options = {
          nodes: {
            shape: 'custom',
            ctxRenderer: function({ ctx, id, x, y, state, style, label }) {
              const node = _graphNodes ? _graphNodes.get(id) : null;
              const grp  = (node && node.group) || 'control';
              const r    = makeRenderer(grp, node);
              return { drawNode() { r.drawNode({ ctx, x, y, state }); }, nodeDimensions: r.nodeDimensions };
            },
          },
          edges: {
            width: 1.2,
            color: { color:'#a8a18d', highlight:'#9a6635', hover:'#7a7560', opacity: 1 },
            dashes: [4, 4],
            font: {
              size: 11,
              color: '#6b7280',
              face: 'Geist Mono, monospace',
              strokeWidth: 4,
              strokeColor: '#faf7f0',
              align: 'middle',
            },
            smooth: { type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 },
            arrows: { to: { enabled: true, scaleFactor: 0.5, type: 'arrow' } },
            selectionWidth: 1.6,
            hoverWidth: 1.4,
          },
          physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
              gravitationalConstant: -120,
              centralGravity: 0.002,
              springLength: 260,
              springConstant: 0.04,
              damping: 0.7,
              avoidOverlap: 1.0,
            },
            stabilization: { iterations: 250, fit: true },
            minVelocity: 0.4,
          },
          interaction: { hover:true, tooltipDelay:200, dragNodes:true, dragView:true, zoomView:true, multiselect:false, zoomSpeed:0.5 },
          layout: { improvedLayout: true },
        };

        if (_graphNetwork) { _graphNetwork.destroy(); }
        _graphNetwork = new vis.Network(container, { nodes: _graphNodes, edges }, options);
        _physicsOn = true;
        document.getElementById('btn-physics').textContent = 'Fijar nodos';

        _graphNetwork.on('stabilizationIterationsDone', function () {
          _graphNetwork.setOptions({ physics: { enabled: false } });
          _physicsOn = false;
          document.getElementById('btn-physics').textContent = 'Soltar nodos';
        });

        _graphNetwork.on('click', function (params) {
          if (!params.nodes.length) { infoEl.style.display = 'none'; return; }
          const nodeId = params.nodes[0];
          const node   = _graphNodes.get(nodeId);
          if (!node) return;
          const isAsset = node.group === 'asset';
          const badge   = document.getElementById('gni-badge');
          document.getElementById('gni-title').textContent = node.label || String(nodeId);
          badge.textContent  = isAsset ? 'Activo · Red Team' : 'Control normativo';
          badge.className    = 'node-type-badge ' + (isAsset ? 'asset' : 'control');
          const html = isAsset ? renderAssetDetail(node) : renderControlDetail(node);
          document.getElementById('gni-meta').innerHTML = html;
          infoEl.classList.toggle('is-asset', isAsset);
          infoEl.style.display = 'block';
        });

        if (nodeCount === 0) msgEl.textContent = 'Sin hallazgos con compliance: traduce uno primero.';
      } catch (e) { msgEl.textContent = 'Error de red: ' + e.message; }
    }

    /* ── Node detail renderers ─────────────────────────────────────── */
    function renderAssetDetail(node) {
      const d = node.detail || {};
      const marcos = (node.marcos || []).map(m => '<span class="gni-chip">' + esc(marcoShort(m)) + '</span>').join('');
      const controles = (d.controles_incumplidos || []).map(c => '<span class="gni-chip sky">' + esc(c) + '</span>').join('');
      const sev = d.severidad || 'media';

      let html = '<div class="gni-meta-row">' +
        '<div class="kv"><span class="k">Hallazgo</span><span class="v">' + esc(d.hallazgo_id || '—') + '</span></div>' +
        '<div class="kv"><span class="k">Origen</span><span class="v">' + esc(d.origen || '—') + '</span></div>' +
        '<div class="kv"><span class="k">Severidad</span><span class="v">' + badgeHtml(sev) + '</span></div>' +
        (d.cve_relacionado ? '<div class="kv"><span class="k">CVE</span><span class="v">' + esc(d.cve_relacionado) + '</span></div>' : '') +
        '<div class="kv"><span class="k">Registrado</span><span class="v">' + esc((d.timestamp || '').replace('T', ' ').slice(0, 19)) + '</span></div>' +
      '</div>';

      if (d.activo) html += section('Activo detectado', '<p>' + esc(d.activo) + '</p>');
      if (d.vector_ataque) html += section('Vector de ataque', '<p>' + esc(d.vector_ataque) + '</p>');
      if (d.evidencia) html += section('Evidencia técnica', '<div class="mono-block">' + esc(d.evidencia) + '</div>');
      if (marcos) html += section('Marcos aplicables', '<div class="gni-chips">' + marcos + '</div>');
      if (controles) html += section('Controles incumplidos', '<div class="gni-chips">' + controles + '</div>');
      if (d.cita_normativa) html += section('Cita normativa', '<div class="mono-block">' + esc(d.cita_normativa) + '</div>');
      if (d.justificacion) html += section('Justificación', '<p>' + esc(d.justificacion) + '</p>');
      if (d.accion_mitigacion) html += section('Acción de mitigación', '<p>' + esc(d.accion_mitigacion) + '</p>');
      if (d.evidencia_auditoria) html += section('Evidencia para auditoría', '<div class="mono-block">' + esc(d.evidencia_auditoria) + '</div>');
      return html;
    }

    function renderControlDetail(node) {
      const d = node.detail || {};
      const marcos = (d.marcos || node.marcos || []).map(m => '<span class="gni-chip">' + esc(marcoShort(m)) + '</span>').join('');
      const activos = (d.activos_afectados || []).map(a =>
        '<li><span class="l-activo">' + esc(a.activo || '') + '</span>' +
        '<span><span class="l-id">' + esc(a.hallazgo_id || '') + '</span>' + badgeHtml(a.severidad || 'media') + '</span></li>'
      ).join('');

      let html = '<div class="gni-meta-row">' +
        '<div class="kv"><span class="k">Control</span><span class="v">' + esc(d.control_id || node.label || '—') + '</span></div>' +
        '<div class="kv"><span class="k">Hallazgos</span><span class="v">' + (d.total_hallazgos || 0) + '</span></div>' +
        '<div class="kv"><span class="k">Severidad máx</span><span class="v">' + badgeHtml(d.severidad_max || 'media') + '</span></div>' +
      '</div>';

      if (marcos) html += section('Marcos a los que pertenece', '<div class="gni-chips">' + marcos + '</div>');
      if (activos) html += section('Activos afectados', '<ul class="gni-list">' + activos + '</ul>');

      const citas = d.citas_normativas || [];
      if (citas.length) {
        const items = citas.map(c => '<div class="mono-block" style="margin-bottom:6px">' + esc(c) + '</div>').join('');
        html += section('Citas normativas (' + citas.length + ')', items);
      }

      const justs = d.justificaciones || [];
      if (justs.length) {
        const items = justs.map(j => '<p style="margin-bottom:8px">' + esc(j) + '</p>').join('');
        html += section('Justificaciones (' + justs.length + ')', items);
      }

      const mitigs = d.acciones_mitigacion || [];
      if (mitigs.length) {
        const items = mitigs.map(m => '<p style="margin-bottom:8px">' + esc(m) + '</p>').join('');
        html += section('Acciones de mitigación (' + mitigs.length + ')', items);
      }

      return html;
    }

    function section(label, body) {
      return '<div class="gni-section"><span class="gni-section-label">' + esc(label) + '</span>' + body + '</div>';
    }

    function togglePhysics() {
      if (!_graphNetwork) return;
      _physicsOn = !_physicsOn;
      _graphNetwork.setOptions({ physics: { enabled: _physicsOn } });
      document.getElementById('btn-physics').textContent = _physicsOn ? 'Fijar nodos' : 'Soltar nodos';
    }
    function fitGraph() {
      if (_graphNetwork) _graphNetwork.fit({ animation: { duration:400, easingFunction:'easeInOutQuad' } });
    }

    async function doDrift() {
      const btn    = document.getElementById('btn-drift');
      const proc   = document.getElementById('drift-proc').value.trim();
      const obsRaw = document.getElementById('drift-obs').value.trim();
      if (!proc)   { msgErr('drift-msg', 'Introduce el texto del procedimiento.'); return; }
      if (!obsRaw) { msgErr('drift-msg', 'Introduce al menos una observación.'); return; }
      const observaciones = obsRaw.split('\\n').map(s => s.trim()).filter(Boolean);
      btn.disabled = true; msgInfo('drift-msg', 'Analizando drift…');
      setMsg('drift-result', '<div class="empty">Analizando…</div>');
      try {
        const r = await fetch(API + '/drift/analyze', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ procedimiento: proc, observaciones }) });
        const d = await r.json();
        if (!r.ok) { msgErr('drift-msg', 'Error ' + r.status + ': ' + esc(d.detail || JSON.stringify(d))); setMsg('drift-result', '<div class="empty">Error.</div>'); }
        else { msgOk('drift-msg', 'Análisis completado'); setMsg('drift-result', renderDrift(d)); }
      } catch (e) { msgErr('drift-msg', 'Error de red: ' + esc(e.message)); setMsg('drift-result', '<div class="empty">Error de red.</div>'); }
      btn.disabled = false;
    }

    function renderDrift(d) {
      const detected = !!d.drift_detectado;
      let html = '<div class="drift-result">';
      html += '<div class="drift-banner ' + (detected ? 'detected' : 'ok') + '"><strong>' + (detected ? 'Drift detectado' : 'Sin drift significativo') + '</strong>' + (d.severidad ? ' · ' + badgeHtml(d.severidad) : '') + '</div>';
      if (d.descripcion_drift) html += '<div class="drift-section"><strong>Descripción</strong><p>' + esc(d.descripcion_drift) + '</p></div>';
      if (detected && d.fragmento_afectado)   html += '<div class="drift-section diff-old"><strong>Fragmento afectado</strong><p>' + esc(d.fragmento_afectado) + '</p></div>';
      if (detected && d.redaccion_propuesta)  html += '<div class="drift-section diff-new"><strong>Redacción propuesta</strong><p>' + esc(d.redaccion_propuesta) + '</p></div>';
      if (d.controles_afectados && d.controles_afectados.length) {
        const ctrls = d.controles_afectados.map(c => '<span class="badge badge-informativa" style="text-transform:none">' + esc(c) + '</span>').join(' ');
        html += '<div class="drift-section"><strong>Controles afectados</strong><p style="font-family:var(--font-sans); padding:var(--s-3)">' + ctrls + '</p></div>';
      }
      html += '</div>';
      return html;
    }

    async function doCopilot() {
      const btn      = document.getElementById('btn-copilot');
      const pregunta = document.getElementById('copilot-pregunta').value.trim();
      const contexto = document.getElementById('copilot-contexto').value.trim();
      if (!pregunta) { msgErr('copilot-msg', 'Escribe una pregunta primero.'); return; }
      btn.disabled = true; msgInfo('copilot-msg', 'Consultando Copilot…'); setMsg('copilot-result', '');
      try {
        const r = await fetch(API + '/copilot/ask', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ pregunta, contexto }) });
        const d = await r.json();
        if (!r.ok) { msgErr('copilot-msg', 'Error ' + r.status + ': ' + esc(d.detail || JSON.stringify(d))); }
        else {
          const pct = Math.round((d.confianza || 0) * 100);
          const color = pct >= 70 ? 'var(--sev-baja)' : pct >= 40 ? 'var(--sev-alta)' : 'var(--sev-critica)';
          const sources = (d.fuentes || []).map(s => '<span class="src">' + esc(s) + '</span>').join('');
          const meta = '<div class="copilot-meta">' +
            '<div class="conf-meter">Confianza ' + pct + '% <div class="conf-bar"><div style="transform:scaleX(' + (pct/100) + '); background:' + color + '"></div></div></div>' +
            (sources ? '<div class="copilot-sources">' + sources + '</div>' : '') +
          '</div>';
          setMsg('copilot-msg', meta);
          setMsg('copilot-result', esc(d.respuesta || '—'));
        }
      } catch (e) { msgErr('copilot-msg', 'Error de red: ' + esc(e.message)); }
      btn.disabled = false;
    }

    /* ── HALLAZGOS — con filtros + estado actions ──────────────────── */
    function estadoBadgeHtml(e) {
      const map = {
        'activo':       { c: 'sev-info-bg',     fg: 'fg-2',         label: 'Activo' },
        'en_progreso':  { c: 'sev-alta-bg',     fg: 'sev-alta',     label: 'En progreso' },
        'solucionado':  { c: 'sev-baja-bg',     fg: 'sev-baja',     label: 'Solucionado' },
      };
      const m = map[e] || map.activo;
      return '<span style="display:inline-flex; align-items:center; gap:5px; padding:2px 8px; border-radius:var(--r-pill); background:var(--' + m.c + '); color:var(--' + m.fg + '); font-family:var(--font-mono); font-size:10.5px; font-weight:500; letter-spacing:0.04em; text-transform:uppercase; border:1px solid currentColor"><span style="width:5px; height:5px; border-radius:50%; background:currentColor"></span>' + m.label + '</span>';
    }

    function clearFindingFilters() {
      document.getElementById('findings-estado').value = '';
      document.getElementById('findings-desde').value = '';
      document.getElementById('findings-hasta').value = '';
      loadFindings();
    }

    async function loadFindings() {
      const estado = document.getElementById('findings-estado').value;
      const desde  = document.getElementById('findings-desde').value;
      const hasta  = document.getElementById('findings-hasta').value;
      const params = new URLSearchParams({ limit: '100' });
      if (estado) params.set('estado', estado);
      if (desde)  params.set('desde', desde);
      if (hasta)  params.set('hasta', hasta + 'T23:59:59');
      try {
        const r = await fetch(API + '/findings?' + params.toString());
        const d = await r.json();
        const total = d.total || 0;
        document.getElementById('findings-count').textContent = total + ' hallazgo(s)';
        if (!d.items || d.items.length === 0) {
          setMsg('findings-table', '<div class="empty">Sin hallazgos con los filtros actuales.</div>');
          return;
        }
        const rows = d.items.map(f => {
          const estadoNow = f.estado || 'activo';
          const btnProg = estadoNow === 'en_progreso'
            ? '<button class="btn btn--ghost" disabled style="padding:3px 8px; font-size:11px; margin:0">en progreso</button>'
            : '<button class="btn btn--ghost" onclick="setFindingEstado(\\''+ esc(f.id_hallazgo) +'\\', \\'en_progreso\\')" style="padding:3px 8px; font-size:11px; margin:0">en progreso</button>';
          const btnSol = estadoNow === 'solucionado'
            ? '<button class="btn btn--ghost" disabled style="padding:3px 8px; font-size:11px; margin:0">solucionado</button>'
            : '<button class="btn btn--ghost" onclick="setFindingEstado(\\''+ esc(f.id_hallazgo) +'\\', \\'solucionado\\')" style="padding:3px 8px; font-size:11px; margin:0">solucionar</button>';
          const btnReact = estadoNow !== 'activo'
            ? '<button class="btn btn--ghost" onclick="setFindingEstado(\\''+ esc(f.id_hallazgo) +'\\', \\'activo\\')" style="padding:3px 8px; font-size:11px; margin:0">reactivar</button>'
            : '';
          return '<tr>' +
            '<td class="mono">' + esc(f.id_hallazgo) + '</td>' +
            '<td>' + esc(f.activo_detectado) + '</td>' +
            '<td class="mono">' + esc(f.origen) + '</td>' +
            '<td class="mono">' + (f.controles_incumplidos || []).map(esc).join(', ') + '</td>' +
            '<td>' + badgeHtml(f.impacto_legal) + '</td>' +
            '<td>' + estadoBadgeHtml(estadoNow) + '</td>' +
            '<td class="mono">' + esc((f.timestamp || '').replace('T', ' ').slice(0, 19)) + '</td>' +
            '<td><div style="display:flex; gap:4px; flex-wrap:wrap">' + btnProg + btnSol + btnReact + '</div></td>' +
          '</tr>';
        }).join('');
        setMsg('findings-table',
          '<div class="table-wrap"><table>' +
            '<thead><tr><th>ID</th><th>Activo</th><th>Origen</th><th>Controles</th><th>Impacto</th><th>Estado</th><th>Timestamp</th><th>Acciones</th></tr></thead>' +
            '<tbody>' + rows + '</tbody>' +
          '</table></div>');
      } catch (e) { setMsg('findings-table', '<div class="msg-error">Error: ' + esc(e.message) + '</div>'); }
    }

    async function setFindingEstado(id, estado) {
      try {
        const r = await fetch(API + '/findings/' + encodeURIComponent(id) + '/estado', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ estado }),
        });
        if (!r.ok) {
          const d = await r.json().catch(() => ({}));
          alert('Error: ' + (d.detail || r.status));
          return;
        }
        await loadFindings();
        await updateFindingsCount();
      } catch (e) {
        alert('Error de red: ' + e.message);
      }
    }

    async function updateFindingsCount() {
      try {
        const r = await fetch(API + '/findings?limit=1&estado=all');
        const d = await r.json();
        document.getElementById('tb-findings').textContent = d.total || 0;
      } catch (_) {}
    }

    /* ── INICIO — KPIs ─────────────────────────────────────────────── */
    async function loadInicio() {
      const wrap = document.getElementById('inicio-kpis');
      try {
        const r = await fetch(API + '/stats');
        if (!r.ok) { wrap.innerHTML = '<div class="msg-error">No se pudieron cargar estadísticas.</div>'; return; }
        const d = await r.json();
        wrap.innerHTML = renderInicio(d);
      } catch (e) {
        wrap.innerHTML = '<div class="msg-error">Error de red: ' + esc(e.message) + '</div>';
      }
    }

    function renderInicio(d) {
      const total = d.total_hallazgos || 0;
      const estado = d.estado_distribution || {};
      const sev = d.severidad_distribution || {};
      const criticos = (sev.critica || 0) + (sev.alta || 0);
      const pctResuelto = total ? Math.round((estado.solucionado || 0) / total * 100) : 0;

      let html = '<div class="kpi-strip" style="margin-bottom:var(--s-5)">' +
        '<div class="kpi kpi--accent"><div class="kpi-label">Hallazgos totales</div><div class="kpi-value">' + total + '</div><div class="kpi-delta">' + (estado.activo || 0) + ' activos · ' + (estado.en_progreso || 0) + ' en progreso</div></div>' +
        '<div class="kpi kpi--accent"><div class="kpi-label">Crítica + alta</div><div class="kpi-value">' + criticos + '</div><div class="kpi-delta">' + (sev.critica || 0) + ' crítica · ' + (sev.alta || 0) + ' alta</div></div>' +
        '<div class="kpi kpi--sky"><div class="kpi-label">Resueltos</div><div class="kpi-value">' + (estado.solucionado || 0) + '</div><div class="kpi-delta">' + pctResuelto + '% del total</div></div>' +
        '<div class="kpi"><div class="kpi-label">Marcos cubiertos</div><div class="kpi-value">' + Object.keys(d.marcos_top || {}).length + '</div><div class="kpi-delta">de 7 disponibles</div></div>' +
      '</div>';

      /* Two-col layout: distrib severidad + top controles */
      html += '<div class="grid-12">';

      /* Severidad stack */
      html += '<div class="card col-span-7"><div class="card-head"><h2>Distribución por severidad</h2><span class="meta">por hallazgo</span></div><div class="card-body">';
      const sevOrder = ['critica', 'alta', 'media', 'baja', 'informativa'];
      const sevTotal = sevOrder.reduce((acc, k) => acc + (sev[k] || 0), 0) || 1;
      html += '<div class="sev-stack">';
      sevOrder.forEach(s => { if (sev[s]) { const w = (sev[s] / sevTotal) * 100; html += '<div class="s-' + s + '" style="width:' + w + '%"></div>'; } });
      html += '</div><div class="sev-legend">';
      sevOrder.forEach(s => { if (sev[s]) html += '<span class="l-' + s + '">' + s + ' · ' + sev[s] + '</span>'; });
      html += '</div></div></div>';

      /* Estado distribution */
      html += '<div class="card col-span-5"><div class="card-head"><h2>Pipeline de remediación</h2><span class="meta">estado actual</span></div><div class="card-body">';
      const estadoRows = [
        { k: 'activo',      label: 'Activos',       color: 'var(--fg-3)' },
        { k: 'en_progreso', label: 'En progreso',   color: 'var(--sev-alta)' },
        { k: 'solucionado', label: 'Solucionados',  color: 'var(--sev-baja)' },
      ];
      const eMax = Math.max(1, ...estadoRows.map(r => estado[r.k] || 0));
      estadoRows.forEach(r => {
        const cnt = estado[r.k] || 0;
        const pct = Math.round((cnt / eMax) * 100);
        html += '<div class="bar-row"><span class="k">' + r.label + '</span><div class="bar-track"><div class="bar-fill" style="transform:scaleX(' + (pct/100) + '); background:' + r.color + '"></div></div><span class="n">' + cnt + '</span></div>';
      });
      html += '</div></div>';

      /* Top marcos */
      html += '<div class="card col-span-7"><div class="card-head"><h2>Marcos más afectados</h2><span class="meta">top 7</span></div><div class="card-body">';
      const marcosTop = d.marcos_top || {};
      const marcoMax = Math.max(1, ...Object.values(marcosTop));
      if (Object.keys(marcosTop).length === 0) {
        html += '<div class="empty">Sin datos todavía.</div>';
      } else {
        Object.entries(marcosTop).forEach(([m, cnt]) => {
          const pct = Math.round((cnt / marcoMax) * 100);
          html += '<div class="bar-row"><span class="k">' + esc(marcoShort(m)) + '</span><div class="bar-track"><div class="bar-fill" style="transform:scaleX(' + (pct/100) + ')"></div></div><span class="n">' + cnt + '</span></div>';
        });
      }
      html += '</div></div>';

      /* Top controles */
      html += '<div class="card col-span-5"><div class="card-head"><h2>Controles incumplidos</h2><span class="meta">top 5</span></div><div class="card-body">';
      const ctrlsTop = d.controles_top || [];
      if (ctrlsTop.length === 0) {
        html += '<div class="empty">Sin datos todavía.</div>';
      } else {
        const ctrlMax = Math.max(1, ...ctrlsTop.map(c => c.total_hallazgos));
        ctrlsTop.forEach(c => {
          const pct = Math.round((c.total_hallazgos / ctrlMax) * 100);
          html += '<div class="bar-row"><span class="k">' + esc(c.control_id) + '</span><div class="bar-track"><div class="bar-fill" style="transform:scaleX(' + (pct/100) + ')"></div></div><span class="n">' + c.total_hallazgos + '</span></div>';
        });
      }
      html += '</div></div>';

      /* Últimos hallazgos */
      html += '<div class="card" style="grid-column: span 12"><div class="card-head"><h2>Últimos 5 hallazgos</h2><span class="meta">orden cronológico inverso</span></div><div class="card-body">';
      const ultimos = d.ultimos_hallazgos || [];
      if (ultimos.length === 0) {
        html += '<div class="empty">Sin hallazgos aún.</div>';
      } else {
        const rows = ultimos.map(f =>
          '<tr>' +
            '<td class="mono">' + esc(f.id_hallazgo) + '</td>' +
            '<td>' + esc(f.activo_detectado) + '</td>' +
            '<td>' + badgeHtml(f.impacto_legal) + '</td>' +
            '<td>' + estadoBadgeHtml(f.estado || 'activo') + '</td>' +
            '<td class="mono">' + esc((f.timestamp || '').replace('T', ' ').slice(0, 19)) + '</td>' +
          '</tr>'
        ).join('');
        html += '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Activo</th><th>Impacto</th><th>Estado</th><th>Timestamp</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
      }
      html += '</div></div>';

      html += '</div>';  /* /grid-12 */
      return html;
    }

    /* ── Ejemplos JSON para tab Traducir ──────────────────────────── */
    const EXAMPLES = {
      critica: {
        "origen": "github_secrets",
        "activo_detectado": "github.com/acme-corp/billing-api (commit a3f9c21) — AWS root access keys + RDS prod credentials",
        "evidencia": "https://github.com/acme-corp/billing-api/blob/a3f9c21/src/config/aws.py#L14 — AKIAIOSFODNN7EXAMPLE + RDS prod con 2.3M PII europeos",
        "vector_ataque": "Acceso administrativo total a AWS prod via credenciales root committeadas en repo público. Exfiltración masiva PII, ransomware sobre RDS, pivote a redes corporativas.",
        "dificultad_explotacion": "baja",
        "cve_relacionado": "CWE-798"
      },
      alta: {
        "origen": "nuclei",
        "activo_detectado": "https://portal.acme-corp.com/api/v1/auth/login — endpoint público sin WAF",
        "evidencia": "Nuclei sqli-auth-bypass.yaml — payload ' OR '1'='1'-- devuelve 200 + cookie sesión válida. 3500 cuentas B2B afectadas.",
        "vector_ataque": "Bypass de autenticación e inyección SQL ciega en login producción sin WAF. Permite extracción tabla users, elevación privilegios, dumping PII.",
        "dificultad_explotacion": "baja",
        "cve_relacionado": "CWE-89"
      },
      media: {
        "origen": "nmap",
        "activo_detectado": "staging-erp.acme-internal.local:443 (10.42.13.7) — ERP staging vía VPN",
        "evidencia": "Nmap ssl-enum-ciphers: TLSv1.0/1.1 habilitados, RC4-SHA aceptado, certificado expirado 2024-08. SSL Labs grade F.",
        "vector_ataque": "Servidor interno permite TLS obsoleto (BEAST, POODLE). Datos RRHH de 1200 empleados en claro frente a atacante con foothold VPN.",
        "dificultad_explotacion": "media",
        "cve_relacionado": "CVE-2014-3566"
      },
      baja: {
        "origen": "nuclei",
        "activo_detectado": "https://www.acme-corp.com — sitio corporativo público",
        "evidencia": "Nuclei tech-detect/php-detect.yaml — X-Powered-By: PHP/7.4.33, Server: Apache/2.4.41, X-AspNet-Version exponiendo stack.",
        "vector_ataque": "Fuga de versión expone stack tecnológico exacto. PHP 7.4 EOL. Reduce esfuerzo reconnaissance del atacante hacia CVEs conocidos.",
        "dificultad_explotacion": "informativa",
        "cve_relacionado": "CWE-200"
      },
      informativa: {
        "origen": "manual",
        "activo_detectado": "https://www.acme-corp.com/preferences — endpoint público con cookie de preferencia idioma",
        "evidencia": "Manual: cookie lang_pref sin SameSite, sin Secure, sin HttpOnly. Solo contiene valor es|en|fr|de, sin sesión ni PII.",
        "vector_ataque": "Cookie no sensible carece de hardening. Sin vector real, pero comportamiento inconsistente entre clientes futuros. Hallazgo preventivo OWASP ASVS V3.4.3.",
        "dificultad_explotacion": "informativa",
        "cve_relacionado": null
      }
    };

    function loadExample(key) {
      if (!key) { clearFinding(); return; }
      const ex = EXAMPLES[key];
      if (!ex) return;
      /* Rellena el formulario y mantiene el textarea JSON sincronizado */
      fillFindingForm(ex);
      document.getElementById('finding-json').value = JSON.stringify(ex, null, 2);
    }
    /* Cargar ejemplo crítica por defecto al inicializar */
    setTimeout(function() {
      try {
        loadExample('critica');
        document.getElementById('example-select').value = 'critica';
      } catch (_) {}
    }, 0);

    /* ── Hook switchTab para refrescar Inicio + Hallazgos ─────────── */
    const _origSwitchTab = switchTab;
    switchTab = function(name, btn) {
      _origSwitchTab(name, btn);
      if (name === 'inicio') loadInicio();
      if (name === 'traductor') loadRecentTranslations();
    };

    /* ── Hook loadGraph param archivados ──────────────────────────── */
    const _origLoadGraph = loadGraph;
    loadGraph = async function() {
      /* monkey-patch fetch param incluir_archivados */
      const includeArch = document.getElementById('graph-incluir-archivados');
      const orig = window.fetch;
      window.fetch = function(url, opts) {
        if (typeof url === 'string' && url.indexOf('/graph/data') === 0) {
          const sep = url.indexOf('?') >= 0 ? '&' : '?';
          url = url + sep + 'incluir_archivados=' + (includeArch && includeArch.checked ? 'true' : 'false');
        }
        return orig.apply(this, arguments);
      };
      try { await _origLoadGraph(); } finally { window.fetch = orig; }
    };

    /* ── Boot ──────────────────────────────────────────────────────── */
    checkHealth();
    updateFindingsCount();
    loadInicio();
    syncMarcoAll();
    try {
      const saved = sessionStorage.getItem('rosetta:tab');
      if (saved && saved !== 'inicio') {
        const map = { 'inicio':0,'traductor':1,'pdf':2,'auditoria':3,'drift':4,'cumplimiento':5,'blue':6,'grafo':7,'copilot':8,'hallazgos':9 };
        const idx = map[saved];
        if (idx != null) {
          const btns = document.querySelectorAll('nav button');
          if (btns[idx]) btns[idx].click();
        }
      }
    } catch (_) {}
  </script>

</body>
</html>"""
