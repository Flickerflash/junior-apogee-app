/* ═══════════════════════════════════════════════════════════════
   Junior Apogee Dashboard – JavaScript
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ─── Constants ────────────────────────────────────────────────────────────────

const AGENT_COLORS = {
  Apogee:      '#58a6ff',
  Prodigy:     '#3fb950',
  Reciprocity: '#d2a8ff',
  COLLEEN:     '#ffa657',
  DemiJoule:   '#ff7b72',
};

const LAYER_LABELS = {
  A_Reasoning: 'Layer A – Reasoning',
  B_Action:    'Layer B – Action',
  C_Outcomes:  'Layer C – Outcomes',
};

// ─── State ────────────────────────────────────────────────────────────────────

let radarChart   = null;
let barChart     = null;
let donutChart   = null;
let historyChart = null;
let owaspChart   = null;
let flagPieChart = null;

// ─── Utils ────────────────────────────────────────────────────────────────────

const fmt = v => v != null ? (v * 100).toFixed(1) + '%' : 'N/A';
const fmtMs = ms => ms >= 1000 ? (ms / 1000).toFixed(2) + 's' : ms.toFixed(0) + 'ms';
const fmtCost = usd => '$' + usd.toFixed(5);

function scoreClass(v) {
  if (v == null) return '';
  if (v >= 0.90) return 'score-high';
  if (v >= 0.75) return 'score-medium';
  return 'score-low';
}

function agentClass(agent) {
  return 'agent-' + agent.toLowerCase().replace(/\s/g, '-');
}

function pillClass(status) {
  switch (status) {
    case 'passed':   return 'pill pill-passed';
    case 'failed':   return 'pill pill-failed';
    case 'warning':  return 'pill pill-warning';
    case 'critical': return 'pill pill-critical';
    default:         return 'pill pill-info';
  }
}

function avg(arr) {
  const valid = arr.filter(v => v != null);
  if (!valid.length) return 0;
  return valid.reduce((a, b) => a + b, 0) / valid.length;
}

function barFillColor(val) {
  if (val >= 0.90) return '#3fb950';
  if (val >= 0.75) return '#e3b341';
  return '#f85149';
}

// ─── Chart Defaults ───────────────────────────────────────────────────────────

Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#2a3347';
Chart.defaults.font.family = "'Inter', sans-serif";

// ─── Tab Routing ──────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');

    // Lazy-load tabs
    if (btn.dataset.tab === 'agents')     loadAgents();
    if (btn.dataset.tab === 'tasks')      loadTasks();
    if (btn.dataset.tab === 'governance') loadGovernance();
  });
});

// ─── Overview ─────────────────────────────────────────────────────────────────

async function loadSnapshot() {
  try {
    const res  = await fetch('/api/v1/snapshot');
    const data = await res.json();
    renderKPIs(data);
    renderMetricsTable(data.agent_summaries);
    renderRadarChart(data.agent_summaries);
    renderBarChart(data.agent_summaries);
    renderDonutChart();
    renderDriftAlerts(data.drift_alerts);
    document.getElementById('snapshotTime').textContent = 'Updated ' + new Date(data.taken_at).toLocaleTimeString();
  } catch (e) {
    console.error('Snapshot fetch failed', e);
  }
}

function renderKPIs(data) {
  const s = data.agent_summaries;
  document.getElementById('kpiTotal').textContent   = data.total_evals;
  document.getElementById('kpiSuccess').textContent = fmt(avg(s.map(x => x.task_success_rate)));
  document.getElementById('kpiFaith').textContent   = fmt(avg(s.map(x => x.faithfulness)));
  document.getElementById('kpiEthics').textContent  = fmt(avg(s.map(x => x.ethics_rights_pass)));
  const alerts = data.drift_alerts.length;
  const alertEl = document.getElementById('kpiAlerts');
  alertEl.textContent = alerts;
  alertEl.className = 'kpi-value ' + (alerts === 0 ? 'good' : alerts <= 2 ? 'alert' : 'danger');
}

function renderMetricsTable(summaries) {
  const tbody = document.getElementById('metricsBody');
  tbody.innerHTML = summaries.map(s => `
    <tr>
      <td class="${agentClass(s.agent)}">${s.agent}</td>
      <td class="${scoreClass(s.task_success_rate)}">${fmt(s.task_success_rate)}</td>
      <td class="${scoreClass(s.faithfulness)}">${fmt(s.faithfulness)}</td>
      <td class="${scoreClass(s.tool_accuracy)}">${fmt(s.tool_accuracy)}</td>
      <td class="${scoreClass(s.ethics_rights_pass)}">${fmt(s.ethics_rights_pass)}</td>
      <td class="${scoreClass(s.archival_quality)}">${fmt(s.archival_quality)}</td>
      <td class="${scoreClass(s.overall_score)}">${fmt(s.overall_score)}</td>
      <td>${fmtMs(s.avg_latency_ms)}</td>
      <td>${fmtCost(s.avg_cost_usd)}</td>
    </tr>
  `).join('');
}

function renderRadarChart(summaries) {
  const labels = ['Task Success', 'Faithfulness', 'Tool Accuracy', 'Ethics/Rights', 'Archival'];
  const datasets = summaries.map(s => ({
    label: s.agent,
    data: [
      s.task_success_rate * 100,
      s.faithfulness * 100,
      s.tool_accuracy * 100,
      s.ethics_rights_pass * 100,
      (s.archival_quality != null ? s.archival_quality : 0) * 100,
    ],
    borderColor: AGENT_COLORS[s.agent] || '#888',
    backgroundColor: (AGENT_COLORS[s.agent] || '#888') + '22',
    pointBackgroundColor: AGENT_COLORS[s.agent] || '#888',
    borderWidth: 2,
    pointRadius: 3,
  }));

  if (radarChart) radarChart.destroy();
  radarChart = new Chart(document.getElementById('radarChart'), {
    type: 'radar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          min: 60, max: 100,
          ticks: { stepSize: 10, font: { size: 10 } },
          grid: { color: '#2a3347' },
          pointLabels: { font: { size: 11 }, color: '#c9d1d9' },
        }
      },
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } },
    }
  });
}

function renderBarChart(summaries) {
  if (barChart) barChart.destroy();
  barChart = new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: {
      labels: summaries.map(s => s.agent),
      datasets: [
        {
          label: 'Task Success',
          data: summaries.map(s => +(s.task_success_rate * 100).toFixed(1)),
          backgroundColor: summaries.map(s => AGENT_COLORS[s.agent] + 'cc'),
          borderColor:     summaries.map(s => AGENT_COLORS[s.agent]),
          borderWidth: 1, borderRadius: 4,
        },
        {
          label: 'Faithfulness',
          data: summaries.map(s => +(s.faithfulness * 100).toFixed(1)),
          backgroundColor: summaries.map(s => AGENT_COLORS[s.agent] + '55'),
          borderColor:     summaries.map(s => AGENT_COLORS[s.agent]),
          borderWidth: 1, borderRadius: 4, borderDash: [4, 4],
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 70, max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#2a3347' } },
        x: { grid: { display: false } },
      },
      plugins: { legend: { position: 'top', labels: { boxWidth: 12 } } },
    }
  });
}

function renderDonutChart() {
  if (donutChart) donutChart.destroy();
  donutChart = new Chart(document.getElementById('donutChart'), {
    type: 'doughnut',
    data: {
      labels: ['Layer A – Reasoning', 'Layer B – Action', 'Layer C – Outcomes', 'Governance'],
      datasets: [{
        data: [28, 42, 68, 20],
        backgroundColor: ['#58a6ff', '#3fb950', '#d2a8ff', '#ffa657'],
        borderColor: '#0d1117',
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12 } },
        tooltip: { callbacks: { label: ctx => ctx.label + ': ' + ctx.raw + ' tasks' } },
      },
    }
  });
}

function renderDriftAlerts(alerts) {
  const section = document.getElementById('driftSection');
  const container = document.getElementById('driftAlerts');
  if (!alerts || alerts.length === 0) { section.style.display = 'none'; return; }
  section.style.display = '';
  container.innerHTML = alerts.map(a => `
    <div class="alert-item ${a.severity === 'critical' ? 'critical' : ''}">
      <div class="alert-icon">${a.severity === 'critical' ? '🔴' : '⚠️'}</div>
      <div class="alert-body">
        <div class="alert-msg">${a.message}</div>
        <div class="alert-meta">
          <span class="${agentClass(a.agent)}">${a.agent}</span> ·
          ${a.metric_name.replace(/_/g, ' ')} ·
          Baseline: ${fmt(a.baseline_value)} → Current: ${fmt(a.current_value)} (${(a.delta*100).toFixed(1)}pp) ·
          ${new Date(a.detected_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  `).join('');
}

// ─── History Chart ────────────────────────────────────────────────────────────

async function loadHistory() {
  try {
    const data = await (await fetch('/api/v1/history')).json();
    if (historyChart) historyChart.destroy();
    const labels = Array.from({length: 20}, (_, i) => `T-${20 - i}`);
    const datasets = Object.entries(data).map(([agent, values]) => ({
      label: agent,
      data: values.map(v => +(v * 100).toFixed(1)),
      borderColor: AGENT_COLORS[agent] || '#888',
      backgroundColor: 'transparent',
      borderWidth: 2,
      tension: 0.35,
      pointRadius: 0,
    }));
    historyChart = new Chart(document.getElementById('historyChart'), {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 70, max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#2a3347' } },
          x: { grid: { display: false } },
        },
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } },
      }
    });
  } catch(e) { console.error('History fetch failed', e); }
}

// ─── Agents Tab ───────────────────────────────────────────────────────────────

async function loadAgents() {
  const grid = document.getElementById('agentsGrid');
  try {
    const agents = await (await fetch('/api/v1/agents')).json();
    const snapRes = await fetch('/api/v1/snapshot');
    const snap    = await snapRes.json();
    const summaryMap = {};
    snap.agent_summaries.forEach(s => summaryMap[s.agent] = s);

    grid.innerHTML = agents.map(a => {
      const s = summaryMap[a.name] || {};
      const metrics = [
        { label: 'Task Success',  val: s.task_success_rate },
        { label: 'Faithfulness',  val: s.faithfulness },
        { label: 'Tool Accuracy', val: s.tool_accuracy },
        { label: 'Ethics/Rights', val: s.ethics_rights_pass },
        { label: 'Overall',       val: s.overall_score },
      ];
      return `
        <div class="agent-card">
          <div class="agent-card-header">
            <div class="agent-avatar ${agentClass(a.name)}" style="color:${AGENT_COLORS[a.name]};border-color:${AGENT_COLORS[a.name]}">
              ${a.name[0]}
            </div>
            <div class="agent-info">
              <h3 class="${agentClass(a.name)}">${a.name}</h3>
              <div class="agent-model">🤖 ${a.model_backend} · 🌡 ${a.temperature}</div>
            </div>
          </div>
          <div class="agent-desc">${a.description.replace(/\s+/g,' ').trim()}</div>
          <div class="agent-tags">
            ${a.tags.map(t => `<span class="agent-tag">${t}</span>`).join('')}
          </div>
          <div class="agent-metrics">
            ${metrics.map(m => `
              <div class="metric-bar">
                <div class="metric-bar-label">${m.label}</div>
                <div class="metric-bar-track">
                  <div class="metric-bar-fill"
                    style="width:${m.val != null ? (m.val*100).toFixed(1) : 0}%;background:${barFillColor(m.val || 0)}">
                  </div>
                </div>
                <div class="metric-bar-val">${m.val != null ? fmt(m.val) : 'N/A'}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');
  } catch(e) {
    grid.innerHTML = `<div class="loading">Failed to load agents: ${e.message}</div>`;
  }
}

// ─── Tasks Tab ────────────────────────────────────────────────────────────────

async function loadTasks() {
  const tbody = document.getElementById('tasksBody');
  try {
    const tasks = await (await fetch('/api/v1/task-results')).json();
    tbody.innerHTML = tasks.map(t => `
      <tr>
        <td style="font-family:var(--mono);font-size:11px;color:var(--muted)">${t.family_id}</td>
        <td>${t.name}</td>
        <td class="${agentClass(t.agent)}">${t.agent}</td>
        <td><span class="pill pill-info">${t.layer.replace('_', ' ')}</span></td>
        <td class="${scoreClass(t.score)}">${(t.score * 100).toFixed(1)}%</td>
        <td><span class="${pillClass(t.status)}">${t.status}</span></td>
        <td>${fmtMs(t.latency_ms)}</td>
      </tr>
    `).join('');
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading">Error: ${e.message}</td></tr>`;
  }
}

// ─── Governance Tab ───────────────────────────────────────────────────────────

async function loadGovernance() {
  try {
    const data = await (await fetch('/api/v1/compliance')).json();

    document.getElementById('govScore').textContent    = fmt(data.compliance_score);
    document.getElementById('govScore').className      = 'kpi-value ' + scoreClass(data.compliance_score);
    document.getElementById('govTotal').textContent    = data.total_checks;
    document.getElementById('govPassed').textContent   = data.passed_checks;
    document.getElementById('govCritical').textContent = data.critical_count;
    document.getElementById('govCritical').className   = 'kpi-value ' + (data.critical_count > 0 ? 'danger' : 'good');

    renderOwaspChart(data);
    renderFlagPieChart(data.flags);
    renderGovTable(data.flags);
  } catch(e) { console.error('Governance fetch failed', e); }
}

function renderOwaspChart(data) {
  const owaspIds = ['A01','A02','A03','A04','A05','A06','A07','A08','A09','A10'];
  const flagMap  = {};
  data.flags.filter(f => f.owasp_id && f.owasp_id.startsWith('OWASP')).forEach(f => {
    flagMap[f.owasp_id.replace('OWASP-','')] = (flagMap[f.owasp_id.replace('OWASP-','')] || 0) + 1;
  });
  const vals = owaspIds.map(id => flagMap[id] || 0);
  const max  = data.total_checks / owaspIds.length || 1;
  const scores = vals.map(v => Math.max(0, 100 - (v / max * 100)));

  if (owaspChart) owaspChart.destroy();
  owaspChart = new Chart(document.getElementById('owaspChart'), {
    type: 'bar',
    data: {
      labels: owaspIds.map(id => 'OWASP-' + id),
      datasets: [{
        label: 'Compliance %',
        data: scores,
        backgroundColor: scores.map(s => s >= 90 ? '#3fb95088' : s >= 70 ? '#e3b34188' : '#f8514988'),
        borderColor:     scores.map(s => s >= 90 ? '#3fb950' : s >= 70 ? '#e3b341' : '#f85149'),
        borderWidth: 1, borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 0, max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#2a3347' } },
        x: { grid: { display: false } },
      },
      plugins: { legend: { display: false } },
    }
  });
}

function renderFlagPieChart(flags) {
  const cats = {};
  flags.forEach(f => cats[f.category] = (cats[f.category] || 0) + 1);
  if (flagPieChart) flagPieChart.destroy();
  if (!Object.keys(cats).length) return;
  flagPieChart = new Chart(document.getElementById('flagPieChart'), {
    type: 'pie',
    data: {
      labels: Object.keys(cats),
      datasets: [{
        data: Object.values(cats),
        backgroundColor: ['#58a6ff','#f85149','#e3b341','#3fb950','#d2a8ff'],
        borderColor: '#0d1117',
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } },
    }
  });
}

function renderGovTable(flags) {
  const tbody = document.getElementById('govBody');
  if (!flags.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--accent2);padding:20px">✅ No governance flags raised</td></tr>';
    return;
  }
  tbody.innerHTML = flags.map(f => `
    <tr>
      <td style="font-family:var(--mono);font-size:11px">${f.owasp_id || '—'}</td>
      <td>${f.category}</td>
      <td><span class="${pillClass(f.severity)}">${f.severity}</span></td>
      <td class="${f.agent ? agentClass(f.agent) : ''}">${f.agent || '—'}</td>
      <td style="font-size:12px">${f.description}</td>
      <td>${f.mitigated ? '<span class="pill pill-passed">Yes</span>' : '<span class="pill pill-failed">No</span>'}</td>
    </tr>
  `).join('');
}

// ─── Evaluate Tab ─────────────────────────────────────────────────────────────

document.getElementById('runEvalBtn').addEventListener('click', async () => {
  const agent   = document.getElementById('evalAgent').value;
  const output  = document.getElementById('evalOutput').value;
  const taskName = document.getElementById('evalTaskName').value || 'Ad-hoc evaluation';
  let toolCalls = [];
  try {
    const raw = document.getElementById('evalTools').value.trim();
    if (raw) toolCalls = JSON.parse(raw);
  } catch (e) {
    alert('Tool calls must be valid JSON array.');
    return;
  }

  const btn = document.getElementById('runEvalBtn');
  btn.textContent = '⏳ Evaluating…';
  btn.disabled = true;

  try {
    const res  = await fetch('/api/v1/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent, output, task_name: taskName, tool_calls: toolCalls }),
    });
    const data = await res.json();
    renderEvalResult(data);
  } catch(e) {
    alert('Evaluation failed: ' + e.message);
  } finally {
    btn.textContent = '▶ Run Evaluation';
    btn.disabled = false;
  }
});

function renderEvalResult(data) {
  const box = document.getElementById('evalResults');
  const body = document.getElementById('evalResultBody');
  box.style.display = '';

  const status = data.task_status === 'passed' ? 'pill-passed' : 'pill-failed';
  const r = data.reasoning || {};
  const a = data.action    || {};
  const o = data.outcome   || {};

  body.innerHTML = `
    <div class="eval-score-row">
      <div class="eval-score-box">
        <div class="score-label">Overall Score</div>
        <div class="score-num ${scoreClass(data.overall_score)}">${fmt(data.overall_score)}</div>
      </div>
      <div class="eval-score-box">
        <div class="score-label">Status</div>
        <div style="margin-top:4px"><span class="pill ${status}">${data.task_status}</span></div>
      </div>
      <div class="eval-score-box">
        <div class="score-label">Gov Checks</div>
        <div class="score-num ${data.governance.failed_checks > 0 ? 'score-low' : 'score-high'}">
          ${data.governance.passed_checks}/${data.governance.total_checks}
        </div>
      </div>
    </div>

    <div class="eval-layer-grid">
      <div class="eval-layer-card">
        <div class="eval-layer-title">Layer A – Reasoning</div>
        ${Object.entries(r).map(([k,v]) => `
          <div class="eval-layer-metric">
            <span class="ml">${k.replace(/_/g,' ')}</span>
            <span class="mv ${scoreClass(v)}">${typeof v === 'number' ? fmt(v) : v}</span>
          </div>
        `).join('')}
      </div>
      <div class="eval-layer-card">
        <div class="eval-layer-title">Layer B – Action</div>
        ${Object.entries(a).map(([k,v]) => `
          <div class="eval-layer-metric">
            <span class="ml">${k.replace(/_/g,' ')}</span>
            <span class="mv ${scoreClass(v)}">${typeof v === 'number' ? fmt(v) : v}</span>
          </div>
        `).join('')}
      </div>
      <div class="eval-layer-card">
        <div class="eval-layer-title">Layer C – Outcomes</div>
        ${Object.entries(o).map(([k,v]) => `
          <div class="eval-layer-metric">
            <span class="ml">${k.replace(/_/g,' ')}</span>
            <span class="mv ${scoreClass(v)}">${typeof v === 'number' ? fmt(v) : v}</span>
          </div>
        `).join('')}
      </div>
    </div>

    <div style="font-size:11px;color:var(--muted);margin-top:8px">
      Eval ID: <span style="font-family:var(--mono)">${data.eval_id}</span>
    </div>
  `;
}

// ─── Live SSE Stream ──────────────────────────────────────────────────────────

function connectStream() {
  const ticker = document.getElementById('tickerText');
  try {
    const es = new EventSource('/api/v1/stream');
    es.onmessage = e => {
      try {
        const d = JSON.parse(e.data);
        const best = d.summaries.reduce((a, b) => a.overall_score > b.overall_score ? a : b, d.summaries[0]);
        ticker.textContent =
          `Live · ${d.timestamp.replace('T',' ').slice(0,19)} · `
          + `${d.total_evals} evals · `
          + `Best: ${best?.agent || '?'} @ ${fmt(best?.overall_score)} · `
          + `${d.alerts} alert${d.alerts !== 1 ? 's' : ''}`;
      } catch (_) {}
    };
    es.onerror = () => { ticker.textContent = 'Stream disconnected. Reconnecting…'; };
  } catch (e) {
    ticker.textContent = 'Live stream not available.';
  }
}

// ─── Refresh button ───────────────────────────────────────────────────────────

document.getElementById('refreshBtn').addEventListener('click', () => {
  loadSnapshot();
  loadHistory();
});

// ─── Boot ─────────────────────────────────────────────────────────────────────

(async function init() {
  await loadSnapshot();
  await loadHistory();
  connectStream();
})();
