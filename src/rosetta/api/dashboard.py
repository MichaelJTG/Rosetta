"""Dashboard HTML embebido — interfaz visual para auditor.

Panel único servido por FastAPI en GET /dashboard. Usa vis.js (CDN) para
el grafo y vanilla JS para el resto. Sin dependencias de npm.
"""

from __future__ import annotations

HTML_DASHBOARD: str = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ROSETTA — Dashboard</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0f1117;
      --surface: #1a202c;
      --border: #2d3748;
      --text: #e2e8f0;
      --muted: #718096;
      --accent: #63b3ed;
      --btn: #3182ce;
      --btn-hover: #2b6cb0;
      --input-bg: #2d3748;
      --input-border: #4a5568;
      --error: #fc8181;
      --success: #68d391;
    }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 1rem;
    }
    header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: .75rem;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1rem;
    }
    header h1 { font-size: 1.4rem; letter-spacing: .05em; color: var(--accent); }
    header span { font-size: .82rem; color: var(--muted); }
    #api-status { margin-left: auto; font-size: .8rem; }

    nav { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: 1.25rem; }
    nav button {
      padding: .35rem .85rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 4px;
      color: var(--muted);
      font-size: .82rem;
      cursor: pointer;
      transition: all .15s;
      margin-top: 0;
    }
    nav button:hover { color: var(--text); border-color: var(--accent); }
    nav button.active { background: var(--btn); color: #fff; border-color: var(--btn); }

    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem; }
    @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.1rem;
    }
    .card h2 { font-size: .95rem; color: var(--accent); margin-bottom: .9rem; }
    .span-full { grid-column: 1 / -1; }

    label { font-size: .78rem; color: var(--muted); display: block; margin-bottom: .2rem; }
    textarea, select, input[type="text"], input[type="file"] {
      width: 100%;
      background: var(--input-bg);
      border: 1px solid var(--input-border);
      border-radius: 4px;
      color: var(--text);
      padding: .45rem .5rem;
      font-size: .82rem;
      font-family: 'Consolas', monospace;
    }
    textarea { resize: vertical; min-height: 140px; }
    select { cursor: pointer; }
    input[type="file"] { font-family: system-ui; padding: .35rem 0; }
    input[type="checkbox"], input[type="radio"] { accent-color: var(--btn); }

    button {
      margin-top: .65rem;
      padding: .45rem 1.1rem;
      background: var(--btn);
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: .84rem;
      transition: background .15s;
    }
    button:hover { background: var(--btn-hover); }
    button:disabled { background: var(--input-border); cursor: not-allowed; }
    button.secondary {
      background: var(--input-bg); border: 1px solid var(--border); color: var(--muted);
    }
    button.secondary:hover { color: var(--text); }

    .msg-error   { color: var(--error);   font-size: .78rem; margin-top: .4rem; }
    .msg-success { color: var(--success); font-size: .78rem; margin-top: .4rem; }
    .msg-info    { color: var(--accent);  font-size: .78rem; margin-top: .4rem; }

    table { width: 100%; border-collapse: collapse; font-size: .78rem; margin-top: .65rem; }
    th { text-align: left; color: var(--muted); border-bottom: 1px solid var(--border); padding: .35rem .45rem; white-space: nowrap; }
    td { padding: .35rem .45rem; border-bottom: 1px solid var(--bg); vertical-align: top; word-break: break-word; }
    tr:hover td { background: var(--border); }

    .badge { display: inline-block; padding: .1rem .4rem; border-radius: 3px; font-size: .68rem; font-weight: 600; }
    .badge-critica     { background:#742a2a; color:#fc8181; }
    .badge-alta        { background:#744210; color:#f6ad55; }
    .badge-media       { background:#5a4010; color:#fbd38d; }
    .badge-baja        { background:#276749; color:#9ae6b4; }
    .badge-informativa { background:#2c5282; color:#90cdf4; }

    .empty { color: var(--input-border); font-size: .8rem; text-align: center; padding: 1rem 0; }

    .bar-row  { display: flex; align-items: center; gap: .5rem; margin-bottom: .3rem; font-size: .78rem; }
    .bar-fill { height: 11px; background: var(--btn); border-radius: 3px; min-width: 4px; transition: width .3s; }

    #findings-count { color: var(--muted); font-size: .78rem; margin-bottom: .4rem; }

    .audit-log {
      margin-top: .65rem; font-size: .72rem; font-family: Consolas, monospace;
      max-height: 160px; overflow-y: auto; background: var(--bg);
      padding: .45rem; border-radius: 4px; display: none;
    }

    #graph-container {
      width: 100%; height: 420px;
      background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
      margin-top: .65rem;
    }
    @media (max-width: 768px) { #graph-container { height: 280px; } }

    .drift-result { margin-top: .75rem; font-size: .82rem; line-height: 1.55; }
    .drift-badge  { display: inline-block; padding: .15rem .55rem; border-radius: 12px; font-size: .75rem; font-weight: 700; margin-bottom: .5rem; }
    .drift-detected { background: #744210; color: #f6ad55; }
    .drift-ok       { background: #276749; color: #9ae6b4; }
    .drift-section  { margin-top: .6rem; }
    .drift-section strong { color: var(--accent); display: block; font-size: .78rem; margin-bottom: .15rem; }
    .drift-section p { color: var(--text); background: var(--bg); border-radius: 4px; padding: .4rem .6rem; font-size: .8rem; white-space: pre-wrap; }

    #copilot-result { margin-top: .75rem; font-size: .83rem; line-height: 1.6; white-space: pre-wrap; }

    .flex-row { display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; margin-bottom: .4rem; font-size: .82rem; }
    .mt-sm { margin-top: .5rem; }
    .mt-md { margin-top: .75rem; }
  </style>
</head>
<body>
  <header>
    <h1>&#9670; ROSETTA</h1>
    <span>Plataforma de cumplimiento continuo</span>
    <span id="api-status"></span>
  </header>

  <nav id="nav-tabs">
    <button class="active" onclick="switchTab('traductor',this)">&#9654; Traducir</button>
    <button onclick="switchTab('cumplimiento',this)">&#128200; Cumplimiento</button>
    <button onclick="switchTab('auditoria',this)">&#9881; Modo A</button>
    <button onclick="switchTab('pdf',this)">&#128196; PDF</button>
    <button onclick="switchTab('blue',this)">&#128737; Blue</button>
    <button onclick="switchTab('grafo',this)">&#128202; Grafo</button>
    <button onclick="switchTab('drift',this)">&#128203; Drift</button>
    <button onclick="switchTab('copilot',this)">&#129302; Copilot</button>
    <button onclick="switchTab('hallazgos',this)">&#9776; Hallazgos</button>
  </nav>

  <!-- ===== TAB: Traducir ===== -->
  <div id="tab-traductor" class="tab-panel active">
    <div class="grid">
      <div class="card">
        <h2>&#9654; Traducir hallazgo</h2>
        <label for="finding-json">Hallazgo (DatosRedTeam JSON)</label>
        <textarea id="finding-json">{
  "origen": "github_secrets",
  "activo_detectado": "AWS_ACCESS_KEY_ID en repo público",
  "evidencia": "https://github.com/org/repo/commit/abc123",
  "vector_ataque": "Exposición de credencial cloud en código fuente",
  "dificultad_explotacion": "baja"
}</textarea>
        <label class="mt-sm" for="marcos-select">Marco(s) <small style="color:var(--muted)">(Ctrl+clic para varios)</small></label>
        <select id="marcos-select" multiple size="4">
          <option value="iso_27001_2022" selected>ISO 27001:2022</option>
          <option value="ens_2022">ENS 2022</option>
          <option value="nis2">NIS2</option>
          <option value="dora">DORA</option>
          <option value="rgpd">RGPD</option>
          <option value="nist_csf_2">NIST CSF 2.0</option>
          <option value="pci_dss_4">PCI-DSS 4.0</option>
        </select>
        <button id="btn-translate" onclick="doTranslate()">Traducir</button>
        <div id="translate-msg"></div>
        <div id="translate-result" class="mt-md"></div>
      </div>

      <div class="card">
        <h2>&#9432; Guía rápida</h2>
        <p style="font-size:.82rem; color:var(--muted); line-height:1.7">
          <strong style="color:var(--text)">Traducir:</strong> Convierte un hallazgo técnico a evidencia normativa.<br>
          <strong style="color:var(--text)">Modo A:</strong> Auditoría automática Red Team (Nuclei/Nmap).<br>
          <strong style="color:var(--text)">PDF:</strong> Extrae hallazgos de un informe de auditoría.<br>
          <strong style="color:var(--text)">Blue:</strong> Correlaciona alertas Wazuh con hallazgos Red Team.<br>
          <strong style="color:var(--text)">Grafo:</strong> Visualiza activos &#8594; controles (vis.js).<br>
          <strong style="color:var(--text)">Drift:</strong> Detecta si un procedimiento escrito diverge de la realidad.<br>
          <strong style="color:var(--text)">Copilot:</strong> Pregunta normativa en lenguaje natural.
        </p>
      </div>
    </div>
  </div>

  <!-- ===== TAB: Cumplimiento ===== -->
  <div id="tab-cumplimiento" class="tab-panel">
    <div class="card" style="max-width:640px">
      <h2>&#128200; Estado de cumplimiento</h2>
      <label for="state-marco">Marco normativo</label>
      <select id="state-marco">
        <option value="iso_27001_2022">ISO 27001:2022</option>
        <option value="ens_2022">ENS 2022</option>
        <option value="nis2">NIS2</option>
        <option value="dora">DORA</option>
        <option value="rgpd">RGPD</option>
        <option value="nist_csf_2">NIST CSF 2.0</option>
        <option value="pci_dss_4">PCI-DSS 4.0</option>
      </select>
      <button onclick="doComplianceState()">Consultar estado</button>
      <div id="state-result" class="mt-md"></div>
    </div>
  </div>

  <!-- ===== TAB: Modo A ===== -->
  <div id="tab-auditoria" class="tab-panel">
    <div class="card" style="max-width:680px">
      <h2>&#9881; Auditoría automática (Modo A)</h2>
      <label for="audit-objetivos">Objetivos (uno por línea)</label>
      <textarea id="audit-objetivos" style="min-height:80px">https://ejemplo.com</textarea>
      <label class="mt-sm">Adaptadores</label>
      <div class="flex-row">
        <label><input type="checkbox" id="chk-nuclei" checked> nuclei</label>
        <label><input type="checkbox" id="chk-nmap"> nmap</label>
      </div>
      <label for="audit-alcance">Declaración de alcance autorizado</label>
      <textarea id="audit-alcance" style="min-height:55px" placeholder="Ej: Autorizado por el CISO para escanear staging el 2026-04-24."></textarea>
      <button id="btn-audit" onclick="startAudit()">Iniciar auditoría</button>
      <div id="audit-msg"></div>
      <div id="audit-log" class="audit-log"></div>
    </div>
  </div>

  <!-- ===== TAB: PDF ===== -->
  <div id="tab-pdf" class="tab-panel">
    <div class="card" style="max-width:580px">
      <h2>&#128196; Ingestar informe PDF</h2>
      <label for="pdf-file">Informe de auditoría (PDF)</label>
      <input type="file" id="pdf-file" accept=".pdf">
      <button id="btn-ingest" onclick="doIngestPdf()">Extraer hallazgos</button>
      <div id="ingest-msg"></div>
      <div id="ingest-result" class="mt-md"></div>
    </div>
  </div>

  <!-- ===== TAB: Blue Team ===== -->
  <div id="tab-blue" class="tab-panel">
    <div class="card">
      <h2>&#128737; Blue Team &#8212; Alertas Wazuh</h2>
      <div class="flex-row">
        <span>Formato:</span>
        <label><input type="radio" name="blue-fmt" value="json" checked> JSON</label>
        <label><input type="radio" name="blue-fmt" value="csv"> CSV</label>
      </div>
      <label for="blue-data">Datos de alertas</label>
      <textarea id="blue-data" style="min-height:100px; font-size:.78rem" placeholder='[{"id":"1","timestamp":"2026-04-24T10:00:00","rule":{"id":"5710","level":7,"description":"SSH brute force"},"agent":{"id":"001","name":"srv-web","ip":"1.2.3.4"}}]'></textarea>
      <button id="btn-blue" onclick="doBlueIngest()">Ingestar alertas</button>
      <div id="blue-msg"></div>
      <div id="blue-result" class="mt-md"></div>
    </div>
  </div>

  <!-- ===== TAB: Grafo vis.js ===== -->
  <div id="tab-grafo" class="tab-panel">
    <div class="card">
      <h2>&#128202; Grafo de correlación activo &#8594; control</h2>
      <div class="flex-row">
        <label for="graph-marco" style="margin:0; white-space:nowrap">Marco:</label>
        <select id="graph-marco" style="width:auto; min-width:160px">
          <option value="">Todos</option>
          <option value="iso_27001_2022">ISO 27001:2022</option>
          <option value="ens_2022">ENS 2022</option>
          <option value="nis2">NIS2</option>
          <option value="dora">DORA</option>
          <option value="rgpd">RGPD</option>
          <option value="nist_csf_2">NIST CSF 2.0</option>
          <option value="pci_dss_4">PCI-DSS 4.0</option>
        </select>
        <button onclick="loadGraph()" style="margin-top:0">&#8635; Cargar</button>
        <span id="graph-msg" style="font-size:.78rem; color:var(--muted)"></span>
      </div>
      <div id="graph-container"></div>
      <p style="font-size:.72rem; color:var(--muted); margin-top:.4rem">
        &#9670; Rojo/naranja = activo con hallazgo &nbsp;|&nbsp; &#9679; Azul = control normativo &nbsp;|&nbsp;
        Arrastra para reorganizar &nbsp;|&nbsp; Scroll para zoom
      </p>
    </div>
  </div>

  <!-- ===== TAB: Procedure Drift ===== -->
  <div id="tab-drift" class="tab-panel">
    <div class="grid">
      <div class="card">
        <h2>&#128203; Analizar Procedure Drift</h2>
        <label for="drift-proc">Texto del procedimiento interno</label>
        <textarea id="drift-proc" style="min-height:160px" placeholder="Pega aquí el procedimiento escrito de seguridad (IAM, accesos, respuesta a incidentes…)"></textarea>
        <label class="mt-sm" for="drift-obs">Observaciones reales (una por línea)</label>
        <textarea id="drift-obs" style="min-height:100px" placeholder="Ej:&#10;Log Wazuh: usuario admin activo 90 días sin rotación&#10;Alerta: acceso desde IP no corporativa sin MFA&#10;Nuclei: endpoint /api/admin sin autenticación"></textarea>
        <button id="btn-drift" onclick="doDrift()">Detectar drift</button>
        <div id="drift-msg"></div>
      </div>
      <div class="card">
        <h2>&#128203; Resultado del análisis</h2>
        <div id="drift-result"><div class="empty">Ejecuta el análisis para ver el resultado.</div></div>
      </div>
    </div>
  </div>

  <!-- ===== TAB: Copilot ===== -->
  <div id="tab-copilot" class="tab-panel">
    <div class="card" style="max-width:780px">
      <h2>&#129302; Copilot normativo</h2>
      <label for="copilot-pregunta">Pregunta en lenguaje natural</label>
      <textarea id="copilot-pregunta" style="min-height:80px" placeholder="¿Qué control ISO aplica cuando se expone una clave de cifrado en un repositorio público?"></textarea>
      <label class="mt-sm" for="copilot-contexto">Contexto operativo (opcional)</label>
      <textarea id="copilot-contexto" style="min-height:50px" placeholder="Ej: Sistema de pagos PCI-DSS en producción, sector financiero."></textarea>
      <button id="btn-copilot" onclick="doCopilot()">Preguntar al Copilot</button>
      <div id="copilot-msg"></div>
      <div id="copilot-result"></div>
    </div>
  </div>

  <!-- ===== TAB: Hallazgos ===== -->
  <div id="tab-hallazgos" class="tab-panel">
    <div class="card">
      <h2>&#9776; Hallazgos de sesión</h2>
      <div id="findings-count"></div>
      <div id="findings-table"><div class="empty">Sin hallazgos aún.</div></div>
      <button class="secondary" onclick="loadFindings()" style="margin-top:.5rem">&#8635; Refrescar</button>
    </div>
  </div>

  <script>
    const API = '';
    let _graphNetwork = null;

    function switchTab(name, btn) {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + name).classList.add('active');
      btn.classList.add('active');
      if (name === 'hallazgos') loadFindings();
      if (name === 'grafo') loadGraph();
    }

    function badgeHtml(sev) {
      return '<span class="badge badge-' + (sev||'media') + '">' + (sev||'media') + '</span>';
    }
    function setMsg(id, html) { document.getElementById(id).innerHTML = html; }
    function msgErr(id, t)  { setMsg(id, '<span class="msg-error">'   + t + '</span>'); }
    function msgOk(id, t)   { setMsg(id, '<span class="msg-success">' + t + '</span>'); }
    function msgInfo(id, t) { setMsg(id, '<span class="msg-info">'    + t + '</span>'); }
    function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

    async function checkHealth() {
      try {
        const r = await fetch(API + '/health');
        const d = await r.json();
        document.getElementById('api-status').innerHTML =
          '<span style="color:var(--success)">&#9679; API ' + d.version + '</span>';
      } catch {
        document.getElementById('api-status').innerHTML =
          '<span style="color:var(--error)">&#9679; API no disponible</span>';
      }
    }

    async function doTranslate() {
      const btn = document.getElementById('btn-translate');
      btn.disabled = true;
      msgInfo('translate-msg', 'Traduciendo…');
      setMsg('translate-result', '');
      let hallazgo;
      try { hallazgo = JSON.parse(document.getElementById('finding-json').value); }
      catch (e) { msgErr('translate-msg', 'JSON inválido: ' + e.message); btn.disabled=false; return; }
      const opts = Array.from(document.getElementById('marcos-select').selectedOptions).map(o => o.value);
      const body = { hallazgo, marcos: opts.length ? opts : ['iso_27001_2022'] };
      try {
        const r = await fetch(API + '/translate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
        const data = await r.json();
        if (!r.ok) { msgErr('translate-msg', 'Error ' + r.status + ': ' + (data.detail||JSON.stringify(data))); }
        else {
          msgOk('translate-msg', '&#10003; Traducción registrada');
          setMsg('translate-result',
            '<table><tr><th>Campo</th><th>Valor</th></tr>' +
            '<tr><td>Marcos</td><td>' + (data.marcos_aplicables||[]).join(', ') + '</td></tr>' +
            '<tr><td>Controles incumplidos</td><td>' + (data.controles_incumplidos||[]).join(', ') + '</td></tr>' +
            '<tr><td>Impacto legal</td><td>' + badgeHtml(data.impacto_legal) + '</td></tr>' +
            '<tr><td>Acción de mitigación</td><td>' + esc(data.accion_mitigacion||'—') + '</td></tr>' +
            '<tr><td>Cita normativa</td><td>' + esc(data.cita_normativa||'—') + '</td></tr>' +
            '</table>');
        }
      } catch (e) { msgErr('translate-msg', 'Error de red: ' + e.message); }
      btn.disabled = false;
    }

    async function doComplianceState() {
      const marco = document.getElementById('state-marco').value;
      setMsg('state-result', '<span class="msg-info">Consultando…</span>');
      try {
        const r = await fetch(API + '/compliance/state/' + marco);
        const d = await r.json();
        if (!r.ok) { setMsg('state-result', '<span class="msg-error">Error ' + r.status + ': ' + (d.detail||JSON.stringify(d)) + '</span>'); return; }
        let html = '<p style="font-size:.82rem; margin-bottom:.5rem">Total hallazgos: <strong>' + d.total_hallazgos + '</strong></p>';
        if (d.controles_incumplidos && d.controles_incumplidos.length) {
          const max = Math.max(...d.controles_incumplidos.map(c => c.total_hallazgos), 1);
          html += '<p style="font-size:.78rem; color:var(--muted); margin-bottom:.25rem">Controles más incumplidos:</p>';
          d.controles_incumplidos.forEach(c => {
            const pct = Math.round((c.total_hallazgos / max) * 100);
            html += '<div class="bar-row"><span style="min-width:80px">' + c.control_id + '</span><div class="bar-fill" style="width:' + pct + '%"></div><span>' + c.total_hallazgos + '</span></div>';
          });
        }
        if (d.severidad_distribution && Object.keys(d.severidad_distribution).length) {
          html += '<p style="font-size:.78rem; color:var(--muted); margin-top:.65rem; margin-bottom:.25rem">Distribución por severidad:</p>';
          html += '<div style="display:flex; gap:.4rem; flex-wrap:wrap">';
          Object.entries(d.severidad_distribution).forEach(([sev, cnt]) => { html += '<span class="badge badge-' + sev + '">' + sev + ': ' + cnt + '</span>'; });
          html += '</div>';
        }
        setMsg('state-result', html);
      } catch (e) { msgErr('state-result', 'Error de red: ' + e.message); }
    }

    async function startAudit() {
      const btn = document.getElementById('btn-audit');
      const logEl = document.getElementById('audit-log');
      const objetivos = document.getElementById('audit-objetivos').value.split('\\n').map(s=>s.trim()).filter(Boolean);
      const alcance = document.getElementById('audit-alcance').value.trim();
      const adaptadores = [];
      if (document.getElementById('chk-nuclei').checked) adaptadores.push('nuclei');
      if (document.getElementById('chk-nmap').checked) adaptadores.push('nmap');
      if (!objetivos.length) { msgErr('audit-msg','Introduce al menos un objetivo.'); return; }
      if (alcance.length < 10) { msgErr('audit-msg','Declaración mínimo 10 caracteres.'); return; }
      btn.disabled = true; logEl.style.display = 'block'; logEl.innerHTML = '';
      msgInfo('audit-msg', 'Iniciando auditoría…');
      let auditId;
      try {
        const r = await fetch(API + '/audit/start', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ objetivos, adaptadores, declaracion_alcance: alcance }) });
        const d = await r.json();
        if (!r.ok) { msgErr('audit-msg','Error ' + r.status + ': ' + (d.detail||JSON.stringify(d))); btn.disabled=false; return; }
        auditId = d.audit_id;
        msgOk('audit-msg', '&#9679; Auditoría ' + auditId + ' en curso…');
      } catch(e) { msgErr('audit-msg','Error de red: ' + e.message); btn.disabled=false; return; }
      const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(wsProto + '://' + location.host + '/audit/ws/' + auditId);
      ws.onmessage = function(ev) {
        const d = JSON.parse(ev.data);
        const color = d.tipo==='error' ? 'var(--error)' : d.tipo==='fin' ? 'var(--success)' : 'var(--text)';
        logEl.innerHTML += '<div style="color:' + color + '">[' + (d.timestamp||'').slice(11,19) + '] ' + esc(d.mensaje||'') + '</div>';
        logEl.scrollTop = logEl.scrollHeight;
        if (d.tipo === 'fin') { msgOk('audit-msg','&#10003; Completada — ' + (d.hallazgos_acumulados||0) + ' hallazgo(s)'); btn.disabled=false; }
      };
      ws.onerror = function() { msgErr('audit-msg','Error en WebSocket'); btn.disabled=false; };
      ws.onclose = function() { if (btn.disabled) btn.disabled=false; };
    }

    async function doIngestPdf() {
      const btn  = document.getElementById('btn-ingest');
      const file = document.getElementById('pdf-file').files && document.getElementById('pdf-file').files[0];
      if (!file) { msgErr('ingest-msg','Selecciona un PDF.'); return; }
      btn.disabled = true; msgInfo('ingest-msg','Procesando PDF…'); setMsg('ingest-result','');
      const form = new FormData(); form.append('file', file);
      try {
        const r = await fetch(API + '/ingest/pdf', { method:'POST', body: form });
        const d = await r.json();
        if (!r.ok) { msgErr('ingest-msg','Error ' + r.status + ': ' + (d.detail||JSON.stringify(d))); }
        else {
          msgOk('ingest-msg','&#10003; ' + d.total_hallazgos + ' hallazgo(s) de ' + d.paginas_procesadas + ' página(s)');
          setMsg('ingest-result','<table><tr><th>Campo</th><th>Valor</th></tr>' +
            '<tr><td>Páginas procesadas</td><td>' + d.paginas_procesadas + '</td></tr>' +
            '<tr><td>Páginas con hallazgos</td><td>' + d.paginas_con_hallazgos + '</td></tr>' +
            '<tr><td>Modo extracción</td><td>' + d.modo_extraccion + '</td></tr>' +
            '<tr><td>IDs</td><td style="font-size:.72rem">' + (d.hallazgo_ids||[]).slice(0,5).join(', ') + (d.hallazgo_ids.length>5?' …':'') + '</td></tr></table>');
        }
      } catch (e) { msgErr('ingest-msg','Error de red: ' + e.message); }
      btn.disabled = false;
    }

    async function doBlueIngest() {
      const btn     = document.getElementById('btn-blue');
      const fmt     = document.querySelector('input[name="blue-fmt"]:checked').value;
      const rawData = document.getElementById('blue-data').value.trim();
      if (!rawData) { msgErr('blue-msg','Introduce datos JSON o CSV.'); return; }
      btn.disabled = true; msgInfo('blue-msg','Procesando…'); setMsg('blue-result','');
      let body;
      if (fmt === 'json') {
        try { body = { formato:'json', datos_json: JSON.parse(rawData) }; }
        catch (e) { msgErr('blue-msg','JSON inválido: ' + e.message); btn.disabled=false; return; }
      } else { body = { formato:'csv', datos_csv: rawData }; }
      try {
        const r = await fetch(API + '/blue/ingest', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
        const d = await r.json();
        if (!r.ok) { msgErr('blue-msg','Error ' + r.status + ': ' + (d.detail||JSON.stringify(d))); }
        else {
          const cob = d.resumen_cobertura || {};
          msgOk('blue-msg','&#10003; ' + d.total_alertas + ' alerta(s) ingestada(s)');
          setMsg('blue-result','<table><tr><th>Campo</th><th>Valor</th></tr>' +
            '<tr><td>Total alertas</td><td>' + d.total_alertas + '</td></tr>' +
            '<tr><td>Con cobertura Blue</td><td>' + (cob.con_cobertura||0) + ' / ' + (cob.total_hallazgos||0) + ' (' + (cob.porcentaje_cobertura||0) + '%)</td></tr>' +
            '<tr><td>Sin cobertura</td><td>' + (cob.sin_cobertura||0) + '</td></tr>' +
            '<tr><td>Alertas correlacionadas</td><td>' + (cob.total_alertas_correlacionadas||0) + '</td></tr></table>');
        }
      } catch (e) { msgErr('blue-msg','Error de red: ' + e.message); }
      btn.disabled = false;
    }

    async function loadGraph() {
      const marco = document.getElementById('graph-marco').value;
      const msgEl = document.getElementById('graph-msg');
      msgEl.textContent = 'Cargando grafo…';
      const url = API + '/graph/data' + (marco ? '?marco=' + marco : '');
      try {
        const r = await fetch(url);
        const d = await r.json();
        if (!r.ok) { msgEl.textContent = 'Error: ' + (d.detail||''); return; }
        const nodes = new vis.DataSet(d.nodes || []);
        const edges = new vis.DataSet(d.edges || []);
        const nodeCount = (d.nodes||[]).length;
        const edgeCount = (d.edges||[]).length;
        msgEl.textContent = nodeCount + ' nodos · ' + edgeCount + ' aristas';
        const container = document.getElementById('graph-container');
        const options = {
          nodes: { shape:'dot', size:14, font:{ size:11, color:'#e2e8f0' }, borderWidth:2 },
          edges: {
            width:1, color:{ color:'#4a5568', highlight:'#90cdf4' },
            font:{ size:9, color:'#718096', align:'middle' },
            smooth:{ type:'curvedCW', roundness:0.2 },
            arrows:{ to:{ enabled:true, scaleFactor:0.6 } },
          },
          groups: {
            asset:   { color:{ background:'#742a2a', border:'#fc8181' }, shape:'diamond' },
            control: { color:{ background:'#2b6cb0', border:'#90cdf4' }, shape:'dot' },
          },
          physics: {
            enabled: true, solver:'forceAtlas2Based',
            forceAtlas2Based:{ gravitationalConstant:-35, centralGravity:0.01, springLength:120, damping:0.55 },
            stabilization:{ iterations:150 },
          },
          interaction:{ hover:true, tooltipDelay:150 },
        };
        if (_graphNetwork) { _graphNetwork.destroy(); }
        _graphNetwork = new vis.Network(container, { nodes, edges }, options);
        if (nodeCount === 0) msgEl.textContent = 'Sin hallazgos con compliance — traduce uno primero.';
      } catch (e) { msgEl.textContent = 'Error de red: ' + e.message; }
    }

    async function doDrift() {
      const btn  = document.getElementById('btn-drift');
      const proc = document.getElementById('drift-proc').value.trim();
      const obsRaw = document.getElementById('drift-obs').value.trim();
      if (!proc)   { msgErr('drift-msg','Introduce el texto del procedimiento.'); return; }
      if (!obsRaw) { msgErr('drift-msg','Introduce al menos una observación.'); return; }
      const observaciones = obsRaw.split('\\n').map(s=>s.trim()).filter(Boolean);
      btn.disabled = true; msgInfo('drift-msg','Analizando drift…');
      setMsg('drift-result','<div class="empty">Analizando…</div>');
      try {
        const r = await fetch(API + '/drift/analyze', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ procedimiento:proc, observaciones }) });
        const d = await r.json();
        if (!r.ok) { msgErr('drift-msg','Error ' + r.status + ': ' + (d.detail||JSON.stringify(d))); setMsg('drift-result','<div class="empty">Error.</div>'); }
        else { msgOk('drift-msg','&#10003; Análisis completado'); setMsg('drift-result', renderDrift(d)); }
      } catch (e) { msgErr('drift-msg','Error de red: ' + e.message); setMsg('drift-result','<div class="empty">Error de red.</div>'); }
      btn.disabled = false;
    }

    function renderDrift(d) {
      const detected = d.drift_detectado;
      let html = '<div class="drift-result">';
      html += '<span class="drift-badge ' + (detected?'drift-detected':'drift-ok') + '">' + (detected?'&#9888; DRIFT DETECTADO':'&#10003; Sin drift significativo') + '</span>';
      if (d.severidad) html += ' ' + badgeHtml(d.severidad);
      if (d.descripcion_drift) html += '<div class="drift-section"><strong>Descripción del drift</strong><p>' + esc(d.descripcion_drift) + '</p></div>';
      if (detected && d.fragmento_afectado) html += '<div class="drift-section"><strong>Fragmento afectado</strong><p>' + esc(d.fragmento_afectado) + '</p></div>';
      if (detected && d.redaccion_propuesta) html += '<div class="drift-section"><strong>Redacción propuesta</strong><p>' + esc(d.redaccion_propuesta) + '</p></div>';
      if (d.controles_afectados && d.controles_afectados.length) html += '<div class="drift-section"><strong>Controles afectados</strong><p>' + d.controles_afectados.join(', ') + '</p></div>';
      html += '</div>';
      return html;
    }

    async function doCopilot() {
      const btn      = document.getElementById('btn-copilot');
      const pregunta = document.getElementById('copilot-pregunta').value.trim();
      const contexto = document.getElementById('copilot-contexto').value.trim();
      if (!pregunta) { msgErr('copilot-msg','Escribe una pregunta primero.'); return; }
      btn.disabled = true; msgInfo('copilot-msg','Consultando Copilot…'); setMsg('copilot-result','');
      try {
        const r = await fetch(API + '/copilot/ask', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ pregunta, contexto }) });
        const d = await r.json();
        if (!r.ok) { msgErr('copilot-msg','Error ' + r.status + ': ' + (d.detail||JSON.stringify(d))); }
        else {
          const pct = Math.round((d.confianza||0) * 100);
          const col = pct>=70 ? 'var(--success)' : pct>=40 ? '#f6ad55' : 'var(--error)';
          const fuentesTxt = d.fuentes && d.fuentes.length ? ' · <span style="color:var(--accent)">' + d.fuentes.join(', ') + '</span>' : '';
          setMsg('copilot-msg','<span style="color:' + col + '">&#10003; Confianza: ' + pct + '%</span>' + fuentesTxt);
          setMsg('copilot-result', esc(d.respuesta||'—'));
        }
      } catch (e) { msgErr('copilot-msg','Error de red: ' + e.message); }
      btn.disabled = false;
    }

    async function loadFindings() {
      try {
        const r = await fetch(API + '/findings?limit=50');
        const d = await r.json();
        document.getElementById('findings-count').textContent = (d.total||0) + ' hallazgo(s) en sesión';
        if (!d.items || d.items.length === 0) { setMsg('findings-table','<div class="empty">Sin hallazgos aún.</div>'); return; }
        const rows = d.items.map(f =>
          '<tr><td>' + f.id_hallazgo + '</td><td>' + esc(f.activo_detectado) + '</td><td>' + f.origen + '</td>' +
          '<td style="font-size:.72rem">' + (f.controles_incumplidos||[]).join(', ') + '</td>' +
          '<td>' + badgeHtml(f.impacto_legal) + '</td>' +
          '<td>' + (f.timestamp||'').replace('T',' ').slice(0,19) + '</td></tr>'
        ).join('');
        setMsg('findings-table','<table><tr><th>ID</th><th>Activo</th><th>Origen</th><th>Controles</th><th>Impacto</th><th>Timestamp</th></tr>' + rows + '</table>');
      } catch (e) { setMsg('findings-table','<span class="msg-error">Error: ' + e.message + '</span>'); }
    }

    checkHealth();
  </script>
</body>
</html>"""
