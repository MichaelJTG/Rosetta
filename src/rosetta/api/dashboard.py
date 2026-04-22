"""Dashboard HTML embebido — interfaz visual para auditor.

Panel único servido por FastAPI en GET /dashboard. Sin dependencias externas:
vanilla JS con fetch(), CSS grid básico, sin CDN ni npm.
"""

from __future__ import annotations

HTML_DASHBOARD: str = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ROSETTA — Dashboard</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
      padding: 1.5rem;
    }
    header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 2rem;
      border-bottom: 1px solid #2d3748;
      padding-bottom: 1rem;
    }
    header h1 { font-size: 1.5rem; letter-spacing: .05em; color: #63b3ed; }
    header span { font-size: .85rem; color: #718096; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: auto auto;
      gap: 1.5rem;
    }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .card {
      background: #1a202c;
      border: 1px solid #2d3748;
      border-radius: 8px;
      padding: 1.25rem;
    }
    .card h2 { font-size: 1rem; color: #90cdf4; margin-bottom: 1rem; }
    label { font-size: .8rem; color: #a0aec0; display: block; margin-bottom: .25rem; }
    textarea, select, input {
      width: 100%;
      background: #2d3748;
      border: 1px solid #4a5568;
      border-radius: 4px;
      color: #e2e8f0;
      padding: .5rem;
      font-size: .85rem;
      font-family: 'Consolas', monospace;
    }
    textarea { resize: vertical; min-height: 160px; }
    select { cursor: pointer; }
    button {
      margin-top: .75rem;
      padding: .5rem 1.25rem;
      background: #3182ce;
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: .875rem;
    }
    button:hover { background: #2b6cb0; }
    button:disabled { background: #4a5568; cursor: not-allowed; }
    .error { color: #fc8181; font-size: .8rem; margin-top: .5rem; }
    .success { color: #68d391; font-size: .8rem; margin-top: .5rem; }
    table { width: 100%; border-collapse: collapse; font-size: .8rem; margin-top: .75rem; }
    th { text-align: left; color: #718096; border-bottom: 1px solid #2d3748; padding: .4rem .5rem; }
    td { padding: .4rem .5rem; border-bottom: 1px solid #1a202c; vertical-align: top; word-break: break-word; }
    tr:hover td { background: #2d3748; }
    .badge {
      display: inline-block;
      padding: .1rem .4rem;
      border-radius: 3px;
      font-size: .7rem;
      font-weight: 600;
    }
    .badge-critica { background:#742a2a; color:#fc8181; }
    .badge-alta    { background:#744210; color:#f6ad55; }
    .badge-media   { background:#744210; color:#fbd38d; }
    .badge-baja    { background:#276749; color:#9ae6b4; }
    .badge-informativa { background:#2c5282; color:#90cdf4; }
    .empty { color: #4a5568; font-size: .8rem; text-align: center; padding: 1rem 0; }
    .compliance-bar { margin-top: .5rem; }
    .bar-row { display: flex; align-items: center; gap: .5rem; margin-bottom: .3rem; font-size: .8rem; }
    .bar-fill { height: 12px; background: #3182ce; border-radius: 3px; min-width: 4px; transition: width .3s; }
    #findings-count { color: #718096; font-size: .8rem; margin-bottom: .5rem; }
    .span-full { grid-column: 1 / -1; }
  </style>
</head>
<body>
  <header>
    <h1>&#9670; ROSETTA</h1>
    <span>Plataforma de cumplimiento continuo · MVP-6</span>
    <span id="api-status" style="margin-left:auto; font-size:.8rem;"></span>
  </header>

  <div class="grid">

    <!-- Panel 1: Traducir hallazgo -->
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
      <label for="marcos-select" style="margin-top:.75rem">Marco(s) normativo(s)</label>
      <select id="marcos-select" multiple size="3">
        <option value="iso_27001_2022" selected>ISO 27001:2022</option>
        <option value="ens_2022">ENS 2022</option>
        <option value="nis2">NIS2</option>
        <option value="dora">DORA</option>
        <option value="nist_csf_2">NIST CSF 2.0</option>
      </select>
      <button id="btn-translate" onclick="doTranslate()">Traducir</button>
      <div id="translate-msg"></div>
      <div id="translate-result" style="margin-top:.75rem"></div>
    </div>

    <!-- Panel 2: Estado de cumplimiento -->
    <div class="card">
      <h2>&#128200; Estado de cumplimiento</h2>
      <label for="state-marco">Marco normativo</label>
      <select id="state-marco">
        <option value="iso_27001_2022">ISO 27001:2022</option>
        <option value="ens_2022">ENS 2022</option>
        <option value="nis2">NIS2</option>
        <option value="dora">DORA</option>
        <option value="nist_csf_2">NIST CSF 2.0</option>
      </select>
      <button onclick="doComplianceState()">Consultar estado</button>
      <div id="state-result" style="margin-top:.75rem"></div>
    </div>

    <!-- Panel 3: Auditoría automática (Modo A) -->
    <div class="card">
      <h2>&#9881; Auditoría automática (Modo A)</h2>
      <label for="audit-objetivos">Objetivos (uno por línea)</label>
      <textarea id="audit-objetivos" style="min-height:80px">https://ejemplo.com</textarea>
      <label style="margin-top:.5rem">Adaptadores</label>
      <div style="display:flex; gap:1rem; margin-bottom:.5rem; font-size:.85rem">
        <label><input type="checkbox" id="chk-nuclei" checked> nuclei</label>
        <label><input type="checkbox" id="chk-nmap"> nmap</label>
      </div>
      <label for="audit-alcance">Declaración de alcance autorizado</label>
      <textarea id="audit-alcance" style="min-height:60px" placeholder="Ej: Autorizado por el CISO para escanear el entorno de staging el 2026-04-22."></textarea>
      <button id="btn-audit" onclick="startAudit()">Iniciar auditoría</button>
      <div id="audit-msg"></div>
      <div id="audit-log" style="margin-top:.75rem; font-size:.75rem; font-family:Consolas,monospace; max-height:180px; overflow-y:auto; background:#0f1117; padding:.5rem; border-radius:4px; display:none;"></div>
    </div>

    <!-- Panel 5: Ingesta de PDF de auditoría -->
    <div class="card">
      <h2>&#128196; Ingestar informe PDF</h2>
      <label for="pdf-file">Informe de auditoría (PDF)</label>
      <input type="file" id="pdf-file" accept=".pdf" style="font-family:system-ui; padding:.4rem 0;">
      <button id="btn-ingest" onclick="doIngestPdf()">Extraer hallazgos</button>
      <div id="ingest-msg"></div>
      <div id="ingest-result" style="margin-top:.75rem"></div>
    </div>

    <!-- Panel 4: Hallazgos de sesión (ancho completo) -->
    <div class="card span-full">
      <h2>&#9776; Hallazgos de sesión</h2>
      <div id="findings-count"></div>
      <div id="findings-table"><div class="empty">Sin hallazgos aún — traduce un hallazgo para empezar.</div></div>
      <button onclick="loadFindings()" style="margin-top:.5rem; background:#2d3748;">&#8635; Refrescar</button>
    </div>

  </div>

  <script>
    const API = '';

    async function checkHealth() {
      try {
        const r = await fetch(API + '/health');
        const d = await r.json();
        document.getElementById('api-status').innerHTML =
          '<span style="color:#68d391">&#9679; API ' + d.version + '</span>';
      } catch {
        document.getElementById('api-status').innerHTML =
          '<span style="color:#fc8181">&#9679; API no disponible</span>';
      }
    }

    function badgeHtml(sev) {
      return '<span class="badge badge-' + sev + '">' + sev + '</span>';
    }

    async function doTranslate() {
      const btn = document.getElementById('btn-translate');
      const msgEl = document.getElementById('translate-msg');
      const resEl = document.getElementById('translate-result');
      btn.disabled = true;
      msgEl.innerHTML = '<span style="color:#90cdf4">Traduciendo...</span>';
      resEl.innerHTML = '';

      let hallazgo;
      try { hallazgo = JSON.parse(document.getElementById('finding-json').value); }
      catch (e) { msgEl.innerHTML = '<span class="error">JSON inválido: ' + e.message + '</span>'; btn.disabled=false; return; }

      const opts = Array.from(document.getElementById('marcos-select').selectedOptions).map(o => o.value);
      const body = { hallazgo, marcos: opts.length ? opts : ['iso_27001_2022'] };

      try {
        const r = await fetch(API + '/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await r.json();
        if (!r.ok) {
          msgEl.innerHTML = '<span class="error">Error ' + r.status + ': ' + (data.detail || JSON.stringify(data)) + '</span>';
        } else {
          msgEl.innerHTML = '<span class="success">&#10003; Traducción registrada</span>';
          resEl.innerHTML = renderCompliance(data);
          loadFindings();
        }
      } catch (e) {
        msgEl.innerHTML = '<span class="error">Error de red: ' + e.message + '</span>';
      }
      btn.disabled = false;
    }

    function renderCompliance(d) {
      return '<table><tr><th>Campo</th><th>Valor</th></tr>' +
        '<tr><td>Marcos</td><td>' + (d.marcos_aplicables||[]).join(', ') + '</td></tr>' +
        '<tr><td>Controles incumplidos</td><td>' + (d.controles_incumplidos||[]).join(', ') + '</td></tr>' +
        '<tr><td>Impacto legal</td><td>' + badgeHtml(d.impacto_legal||'media') + '</td></tr>' +
        '<tr><td>Acción de mitigación</td><td>' + (d.accion_mitigacion||'—') + '</td></tr>' +
        '<tr><td>Cita normativa</td><td>' + (d.cita_normativa||'—') + '</td></tr>' +
        '</table>';
    }

    async function loadFindings() {
      try {
        const r = await fetch(API + '/findings?limit=50');
        const d = await r.json();
        const countEl = document.getElementById('findings-count');
        const tableEl = document.getElementById('findings-table');
        countEl.textContent = d.total + ' hallazgo(s) en sesión';
        if (!d.items || d.items.length === 0) {
          tableEl.innerHTML = '<div class="empty">Sin hallazgos aún.</div>';
          return;
        }
        let rows = d.items.map(f =>
          '<tr>' +
          '<td>' + f.id_hallazgo + '</td>' +
          '<td>' + f.activo_detectado + '</td>' +
          '<td>' + f.origen + '</td>' +
          '<td>' + (f.controles_incumplidos||[]).join(', ') + '</td>' +
          '<td>' + badgeHtml(f.impacto_legal||'media') + '</td>' +
          '<td>' + (f.timestamp||'').replace('T',' ').slice(0,19) + '</td>' +
          '</tr>'
        ).join('');
        tableEl.innerHTML = '<table><tr><th>ID</th><th>Activo</th><th>Origen</th><th>Controles</th><th>Impacto</th><th>Timestamp</th></tr>' + rows + '</table>';
      } catch (e) {
        document.getElementById('findings-table').innerHTML = '<div class="error">Error cargando hallazgos: ' + e.message + '</div>';
      }
    }

    async function doComplianceState() {
      const marco = document.getElementById('state-marco').value;
      const resEl = document.getElementById('state-result');
      resEl.innerHTML = '<span style="color:#90cdf4">Consultando...</span>';
      try {
        const r = await fetch(API + '/compliance/state/' + marco);
        const d = await r.json();
        if (!r.ok) {
          resEl.innerHTML = '<span class="error">Error ' + r.status + ': ' + (d.detail||JSON.stringify(d)) + '</span>';
          return;
        }
        let html = '<p style="font-size:.85rem; margin-bottom:.5rem">Total hallazgos: <strong>' + d.total_hallazgos + '</strong></p>';
        if (d.controles_incumplidos && d.controles_incumplidos.length) {
          html += '<p style="font-size:.8rem; color:#a0aec0; margin-bottom:.25rem">Controles más incumplidos:</p>';
          const max = Math.max(...d.controles_incumplidos.map(c => c.total_hallazgos), 1);
          html += '<div class="compliance-bar">';
          d.controles_incumplidos.forEach(c => {
            const pct = Math.round((c.total_hallazgos / max) * 100);
            html += '<div class="bar-row">' +
              '<span style="min-width:80px">' + c.control_id + '</span>' +
              '<div class="bar-fill" style="width:' + pct + '%"></div>' +
              '<span>' + c.total_hallazgos + '</span>' +
              '</div>';
          });
          html += '</div>';
        }
        if (d.severidad_distribution && Object.keys(d.severidad_distribution).length) {
          html += '<p style="font-size:.8rem; color:#a0aec0; margin-top:.75rem; margin-bottom:.25rem">Distribución por severidad:</p>';
          html += '<div style="display:flex; gap:.5rem; flex-wrap:wrap">';
          Object.entries(d.severidad_distribution).forEach(([sev, cnt]) => {
            html += '<span class="badge badge-' + sev + '">' + sev + ': ' + cnt + '</span>';
          });
          html += '</div>';
        }
        resEl.innerHTML = html;
      } catch (e) {
        resEl.innerHTML = '<span class="error">Error de red: ' + e.message + '</span>';
      }
    }

    async function startAudit() {
      const btn = document.getElementById('btn-audit');
      const msgEl = document.getElementById('audit-msg');
      const logEl = document.getElementById('audit-log');
      const objetivos = document.getElementById('audit-objetivos').value
        .split('\\n').map(s => s.trim()).filter(Boolean);
      const alcance = document.getElementById('audit-alcance').value.trim();
      const adaptadores = [];
      if (document.getElementById('chk-nuclei').checked) adaptadores.push('nuclei');
      if (document.getElementById('chk-nmap').checked) adaptadores.push('nmap');

      if (!objetivos.length) { msgEl.innerHTML = '<span class="error">Introduce al menos un objetivo.</span>'; return; }
      if (alcance.length < 10) { msgEl.innerHTML = '<span class="error">La declaración de alcance debe tener al menos 10 caracteres.</span>'; return; }

      btn.disabled = true;
      logEl.style.display = 'block';
      logEl.innerHTML = '';
      msgEl.innerHTML = '<span style="color:#90cdf4">Iniciando auditoría...</span>';

      const body = { objetivos, adaptadores, declaracion_alcance: alcance };
      let auditId;
      try {
        const r = await fetch(API + '/audit/start', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
        const d = await r.json();
        if (!r.ok) { msgEl.innerHTML = '<span class="error">Error ' + r.status + ': ' + (d.detail||JSON.stringify(d)) + '</span>'; btn.disabled=false; return; }
        auditId = d.audit_id;
        msgEl.innerHTML = '<span class="success">&#9679; Auditoría ' + auditId + ' en curso...</span>';
      } catch(e) { msgEl.innerHTML = '<span class="error">Error de red: ' + e.message + '</span>'; btn.disabled=false; return; }

      const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(wsProto + '://' + location.host + '/audit/ws/' + auditId);
      ws.onmessage = function(ev) {
        const d = JSON.parse(ev.data);
        const color = d.tipo === 'error' ? '#fc8181' : d.tipo === 'fin' ? '#68d391' : '#e2e8f0';
        logEl.innerHTML += '<div style="color:' + color + '">[' + (d.timestamp||'').slice(11,19) + '] ' + (d.mensaje||'') + '</div>';
        logEl.scrollTop = logEl.scrollHeight;
        if (d.tipo === 'fin') {
          msgEl.innerHTML = '<span class="success">&#10003; Auditoría completada — ' + (d.hallazgos_acumulados||0) + ' hallazgo(s)</span>';
          loadFindings();
          btn.disabled = false;
        }
      };
      ws.onerror = function() { msgEl.innerHTML = '<span class="error">Error en WebSocket</span>'; btn.disabled=false; };
      ws.onclose = function() { if (btn.disabled) btn.disabled = false; };
    }

    async function doIngestPdf() {
      const btn = document.getElementById('btn-ingest');
      const msgEl = document.getElementById('ingest-msg');
      const resEl = document.getElementById('ingest-result');
      const fileInput = document.getElementById('pdf-file');
      const file = fileInput.files && fileInput.files[0];
      if (!file) {
        msgEl.innerHTML = '<span class="error">Selecciona un archivo PDF primero.</span>';
        return;
      }
      btn.disabled = true;
      msgEl.innerHTML = '<span style="color:#90cdf4">Procesando PDF... (puede tardar unos segundos)</span>';
      resEl.innerHTML = '';
      const form = new FormData();
      form.append('file', file);
      try {
        const r = await fetch(API + '/ingest/pdf', { method: 'POST', body: form });
        const d = await r.json();
        if (!r.ok) {
          msgEl.innerHTML = '<span class="error">Error ' + r.status + ': ' + (d.detail || JSON.stringify(d)) + '</span>';
        } else {
          msgEl.innerHTML = '<span class="success">&#10003; ' + d.total_hallazgos + ' hallazgo(s) extraídos de ' + d.paginas_procesadas + ' página(s)</span>';
          resEl.innerHTML = '<table><tr><th>Campo</th><th>Valor</th></tr>' +
            '<tr><td>Páginas procesadas</td><td>' + d.paginas_procesadas + '</td></tr>' +
            '<tr><td>Páginas con hallazgos</td><td>' + d.paginas_con_hallazgos + '</td></tr>' +
            '<tr><td>Modo extracción</td><td>' + d.modo_extraccion + '</td></tr>' +
            '<tr><td>IDs registrados</td><td style="font-size:.75rem">' + (d.hallazgo_ids||[]).slice(0,5).join(', ') + (d.hallazgo_ids.length > 5 ? ' …' : '') + '</td></tr>' +
            '</table>';
          loadFindings();
        }
      } catch (e) {
        msgEl.innerHTML = '<span class="error">Error de red: ' + e.message + '</span>';
      }
      btn.disabled = false;
    }

    checkHealth();
    loadFindings();
  </script>
</body>
</html>"""
