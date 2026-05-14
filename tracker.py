"""
Kerala CM 2026 Poll Tracker
Fetches live vote data from https://www.thenextcm.com/ every 1 minute,
logs to CSV, and flags anomalous vote spikes (possible bot activity).
"""

import csv
import json
import os
import time
import urllib.request
from collections import deque
from datetime import datetime

API_URL = "https://votekerala-cm.emergent.host/api/results"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "poll_data.csv")
ALERT_LOG = os.path.join(BASE_DIR, "alerts.csv")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")
INTERVAL_SECONDS = 60  # 1 minute

# Anomaly detection settings
WINDOW_SIZE = 10          # rolling window of last N deltas
SPIKE_MULTIPLIER = 3.0    # flag if delta > mean + multiplier * stdev
MIN_SPIKE_VOTES = 200     # ignore tiny absolute jumps even if ratio is high

CANDIDATE_IDS = ["kc-venugopal", "vd-satheesan", "ramesh-chennithala"]
CANDIDATE_LABELS = {
    "kc-venugopal": "Venugopal",
    "vd-satheesan": "Satheesan",
    "ramesh-chennithala": "Chennithala",
}


def fetch_results():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "PollTracker/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def ensure_csv(path, header):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)


def append_csv(path, row):
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def mean_std(values):
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    m = sum(values) / n
    if n < 2:
        return m, 0.0
    variance = sum((x - m) ** 2 for x in values) / (n - 1)
    return m, variance ** 0.5


class AnomalyDetector:
    """Tracks per-candidate vote deltas and flags spikes."""

    def __init__(self):
        # rolling window of deltas per candidate
        self.history = {cid: deque(maxlen=WINDOW_SIZE) for cid in CANDIDATE_IDS}
        self.prev = None  # previous snapshot {candidate_id: votes}

    def check(self, candidates_dict, ts):
        """Compare with previous snapshot, return list of alert strings."""
        current = {cid: candidates_dict[cid]["votes"] for cid in CANDIDATE_IDS}
        alerts = []

        if self.prev is not None:
            for cid in CANDIDATE_IDS:
                delta = current[cid] - self.prev[cid]
                if delta < 0:
                    alerts.append(
                        f"VOTE DECREASE {CANDIDATE_LABELS[cid]}: "
                        f"{self.prev[cid]} -> {current[cid]} (delta {delta})"
                    )
                hist = self.history[cid]
                if len(hist) >= 3 and delta >= MIN_SPIKE_VOTES:
                    m, s = mean_std(list(hist))
                    threshold = m + SPIKE_MULTIPLIER * max(s, 1)
                    if delta > threshold:
                        alerts.append(
                            f"SPIKE {CANDIDATE_LABELS[cid]}: "
                            f"+{delta} votes/min "
                            f"(avg {m:.0f}, std {s:.0f}, threshold {threshold:.0f})"
                        )
                hist.append(delta)

        self.prev = current
        return alerts


def generate_dashboard():
    """Generate a live dashboard HTML that fetches and parses poll_data.csv."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kerala CM Poll Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',system-ui,sans-serif; background:#0f172a; color:#e2e8f0; padding:20px; }
  h1 { font-size:1.6rem; color:#f8fafc; margin-bottom:4px; }
  .sub { color:#94a3b8; font-size:.85rem; margin-bottom:20px; }
  .top-row { margin-bottom:24px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }
  .card { background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; }
  .card .label { font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; color:#94a3b8; }
  .card .value { font-size:1.8rem; font-weight:700; margin-top:4px; }
  .card .delta { font-size:.8rem; color:#4ade80; margin-top:2px; }
  .pp-trend.up { color:#4ade80; }
  .pp-trend.down { color:#ef4444; }
  .pp-trend.flat { color:#fbbf24; }
  .card.saffron .value { color:#FF9933; }
  .card.green .value { color:#22c55e; }
  .card.red .value { color:#ef4444; }
  .momentum-box { background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; margin-bottom:20px; }
  .momentum-title { font-size:1rem; color:#cbd5e1; margin-bottom:8px; }
  .momentum-callout { color:#e2e8f0; font-size:.92rem; margin-bottom:10px; }
  .share-row { margin-bottom:8px; }
  .share-row:last-child { margin-bottom:0; }
  .share-head { display:flex; justify-content:space-between; font-size:.78rem; color:#cbd5e1; margin-bottom:4px; }
  .share-track { width:100%; height:8px; background:#0f172a; border-radius:999px; overflow:hidden; border:1px solid #334155; }
  .share-fill { height:100%; border-radius:999px; width:0%; transition:width .35s ease; }
  .share-fill.saffron { background:#FF9933; }
  .share-fill.green { background:#22c55e; }
  .share-fill.red { background:#ef4444; }
  .chart-box { background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; margin-bottom:20px; }
  .chart-box h2 { font-size:1rem; color:#cbd5e1; margin-bottom:12px; }
  canvas { width:100%!important; }
  .alerts { background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; }
  .alerts h2 { font-size:1rem; color:#fbbf24; margin-bottom:12px; }
  .alerts .empty { color:#64748b; font-style:italic; }
  .alert-row { padding:6px 0; border-bottom:1px solid #334155; font-size:.82rem; }
  .alert-row:last-child { border-bottom:none; }
  .alert-ts { color:#94a3b8; margin-right:8px; }
  .alert-msg { color:#fbbf24; }
  .alert-msg.error { color:#ef4444; }
  .refresh { color:#64748b; font-size:.75rem; margin-top:16px; text-align:center; }
</style>
</head>
<body>
<h1>Kerala CM 2026 — Poll Tracker</h1>
<p class="sub" id="meta">Loading...</p>

<div class="top-row">
  <div class="grid">
    <div class="card">
      <div class="label">Total Votes</div>
      <div class="value" id="total">-</div>
      <div class="delta" id="delta-total">-</div>
    </div>
    <div class="card saffron">
      <div class="label">K.C. Venugopal</div>
      <div class="value" id="venugopal">-</div>
      <div class="delta" id="delta-venugopal">-</div>
    </div>
    <div class="card green">
      <div class="label">V.D. Satheesan</div>
      <div class="value" id="satheesan">-</div>
      <div class="delta" id="delta-satheesan">-</div>
    </div>
    <div class="card red">
      <div class="label">Ramesh Chennithala</div>
      <div class="value" id="chennithala">-</div>
      <div class="delta" id="delta-chennithala">-</div>
    </div>
  </div>
</div>

<section class="momentum-box">
  <h2 class="momentum-title">Who Is Capturing New Votes?</h2>
  <p class="momentum-callout" id="dominance-callout">Loading momentum...</p>

  <div class="share-row">
    <div class="share-head"><span>Venugopal</span><span id="share-v-label">0%</span></div>
    <div class="share-track"><div id="share-v" class="share-fill saffron"></div></div>
  </div>
  <div class="share-row">
    <div class="share-head"><span>Satheesan</span><span id="share-s-label">0%</span></div>
    <div class="share-track"><div id="share-s" class="share-fill green"></div></div>
  </div>
  <div class="share-row">
    <div class="share-head"><span>Chennithala</span><span id="share-c-label">0%</span></div>
    <div class="share-track"><div id="share-c" class="share-fill red"></div></div>
  </div>
</section>

<div class="chart-box">
  <h2>Votes Per 10 Minutes (Δ) — Spike Detection</h2>
  <canvas id="deltaChart" height="200"></canvas>
</div>

<div class="alerts">
  <h2>Alerts &amp; Errors</h2>
  <div id="alertsContainer"><p class="empty">Loading alerts...</p></div>
</div>

<p class="refresh">Updates every 10 minutes. <a href="#" onclick="location.reload();return false;" style="color:#60a5fa;">Refresh</a> for immediate reload.</p>

<script>
let deltaChart;

function pctTrend(series, windowSize) {
  if (!series || series.length < 2) return 0;
  const slice = series.slice(-windowSize);
  if (slice.length < 2) return 0;
  return slice[slice.length - 1] - slice[0];
}

function avg(values) {
  if (!values || values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function trendMarkup(label, pp) {
  if (pp > 0.05) return `<span class="pp-trend up">${label} ▲ ${pp.toFixed(2)}pp</span>`;
  if (pp < -0.05) return `<span class="pp-trend down">${label} ▼ ${Math.abs(pp).toFixed(2)}pp</span>`;
  return `<span class="pp-trend flat">${label} → 0.00pp</span>`;
}

async function loadData() {
  try {
    // Fetch and parse poll_data.csv
    const csvResp = await fetch('poll_data.csv');
    const csvText = await csvResp.text();
    const rows = parseCSV(csvText);
    const dataRows = rows.filter(r => r.total_votes); // skip error rows
    
    if (dataRows.length === 0) return;

    // Build chart data
    const labels = dataRows.map(r => r.timestamp.substring(5));
    const totals = dataRows.map(r => parseInt(r.total_votes));
    const vVotes = dataRows.map(r => parseInt(r.kc_venugopal_votes));
    const sVotes = dataRows.map(r => parseInt(r.vd_satheesan_votes));
    const cVotes = dataRows.map(r => parseInt(r.ramesh_chennithala_votes));
    const pV = dataRows.map(r => parseFloat(r.kc_venugopal_pct));
    const pS = dataRows.map(r => parseFloat(r.vd_satheesan_pct));
    const pC = dataRows.map(r => parseFloat(r.ramesh_chennithala_pct));
    const dV = dataRows.map(r => parseInt(r.delta_venugopal));
    const dS = dataRows.map(r => parseInt(r.delta_satheesan));
    const dC = dataRows.map(r => parseInt(r.delta_chennithala));
    
    // 10-minute buckets
    const BUCKET = 10;
    const d10Labels = [], dV10 = [], dS10 = [], dC10 = [];
    for (let i = 0; i < dataRows.length; i += BUCKET) {
      const chunk = dataRows.slice(i, i + BUCKET);
      d10Labels.push(chunk[chunk.length-1].timestamp.substring(5));
      dV10.push(chunk.reduce((sum, r) => sum + parseInt(r.delta_venugopal), 0));
      dS10.push(chunk.reduce((sum, r) => sum + parseInt(r.delta_satheesan), 0));
      dC10.push(chunk.reduce((sum, r) => sum + parseInt(r.delta_chennithala), 0));
    }

    // Load alerts
    const alertResp = await fetch('alerts.csv');
    const alertText = await alertResp.text();
    const alertRows = parseCSV(alertText);
    
    // Update summary
    const latest = dataRows[dataRows.length - 1];
    document.getElementById('meta').textContent = 
      `Last updated: ${latest.timestamp} · ${dataRows.length} data points · ${alertRows.length} alerts`;
    
    document.getElementById('total').textContent = parseInt(latest.total_votes).toLocaleString();
    const dTotal = dataRows.map(r => parseInt(r.delta_total));
    const recentTotalAvg = avg(dTotal.slice(-20));
    const overallTotalAvg = avg(dTotal.slice(1));
    document.getElementById('delta-total').textContent =
      `20m avg +${recentTotalAvg.toFixed(1)}/min · overall avg +${overallTotalAvg.toFixed(1)}/min`;
    
    document.getElementById('venugopal').textContent = parseInt(latest.kc_venugopal_votes).toLocaleString();
    const vRecentPp = pctTrend(pV, 20);
    const vOverallPp = pctTrend(pV, pV.length);
    const vRecentAvg = avg(dV.slice(-20));
    document.getElementById('delta-venugopal').textContent =
      `${latest.kc_venugopal_pct}% · 20m avg +${vRecentAvg.toFixed(1)}/min`;
    document.getElementById('delta-venugopal').innerHTML +=
      ` · ${trendMarkup('20m', vRecentPp)} · ${trendMarkup('overall', vOverallPp)}`;
    
    document.getElementById('satheesan').textContent = parseInt(latest.vd_satheesan_votes).toLocaleString();
    const sRecentPp = pctTrend(pS, 20);
    const sOverallPp = pctTrend(pS, pS.length);
    const sRecentAvg = avg(dS.slice(-20));
    document.getElementById('delta-satheesan').textContent =
      `${latest.vd_satheesan_pct}% · 20m avg +${sRecentAvg.toFixed(1)}/min`;
    document.getElementById('delta-satheesan').innerHTML +=
      ` · ${trendMarkup('20m', sRecentPp)} · ${trendMarkup('overall', sOverallPp)}`;
    
    document.getElementById('chennithala').textContent = parseInt(latest.ramesh_chennithala_votes).toLocaleString();
    const cRecentPp = pctTrend(pC, 20);
    const cOverallPp = pctTrend(pC, pC.length);
    const cRecentAvg = avg(dC.slice(-20));
    document.getElementById('delta-chennithala').textContent =
      `${latest.ramesh_chennithala_pct}% · 20m avg +${cRecentAvg.toFixed(1)}/min`;
    document.getElementById('delta-chennithala').innerHTML +=
      ` · ${trendMarkup('20m', cRecentPp)} · ${trendMarkup('overall', cOverallPp)}`;

    // Clear point-of-comparison: who captured recent new votes
    const shareWindow = 20;
    const recentV = dV.slice(-shareWindow).reduce((a, b) => a + Math.max(0, b), 0);
    const recentS = dS.slice(-shareWindow).reduce((a, b) => a + Math.max(0, b), 0);
    const recentC = dC.slice(-shareWindow).reduce((a, b) => a + Math.max(0, b), 0);
    const recentTotal = Math.max(1, recentV + recentS + recentC);
    const shareV = (recentV / recentTotal) * 100;
    const shareS = (recentS / recentTotal) * 100;
    const shareC = (recentC / recentTotal) * 100;

    document.getElementById('share-v').style.width = `${shareV.toFixed(1)}%`;
    document.getElementById('share-s').style.width = `${shareS.toFixed(1)}%`;
    document.getElementById('share-c').style.width = `${shareC.toFixed(1)}%`;
    document.getElementById('share-v-label').textContent = `${shareV.toFixed(1)}%`;
    document.getElementById('share-s-label').textContent = `${shareS.toFixed(1)}%`;
    document.getElementById('share-c-label').textContent = `${shareC.toFixed(1)}%`;

    const leaders = [
      {name:'Venugopal', share:shareV},
      {name:'Satheesan', share:shareS},
      {name:'Chennithala', share:shareC},
    ].sort((a, b) => b.share - a.share);
    document.getElementById('dominance-callout').textContent =
      `${leaders[0].name} captured ${leaders[0].share.toFixed(1)}% of all new votes in the last ${shareWindow} minutes.`;

    // Update alerts
    const alertsDiv = document.getElementById('alertsContainer');
    if (alertRows.length > 0) {
      alertsDiv.innerHTML = alertRows.slice(-50).reverse()
        .map(a => `<div class="alert-row"><span class="alert-ts">${a.timestamp.substring(5)}</span><span class="alert-msg ${a.alert.startsWith('ERROR') ? 'error' : ''}">${a.alert}</span></div>`)
        .join('');
    } else {
      alertsDiv.innerHTML = '<p class="empty">No anomalies detected yet. Monitoring...</p>';
    }

    // Chart config
    const cfg = {
      responsive: true, interaction: {mode:'index',intersect:false},
      plugins: {legend: {labels: {color:'#94a3b8'}}},
      scales: {
        x: {ticks:{color:'#64748b',maxTicksLimit:20}, grid:{color:'#1e293b'}},
        y: {ticks:{color:'#64748b'}, grid:{color:'#334155'}, beginAtZero:false}
      }
    };

    // Destroy old chart
    if (deltaChart) deltaChart.destroy();

    // Delta chart
    deltaChart = new Chart(document.getElementById('deltaChart'), {
      type: 'bar',
      data: {
        labels: d10Labels,
        datasets: [
          {label:'Δ Venugopal (10m)', data:dV10, backgroundColor:'rgba(255,153,51,.7)'},
          {label:'Δ Satheesan (10m)', data:dS10, backgroundColor:'rgba(34,197,94,.7)'},
          {label:'Δ Chennithala (10m)', data:dC10, backgroundColor:'rgba(239,68,68,.7)'}
        ]
      },
      options: {...cfg, plugins: {...cfg.plugins, tooltip:{callbacks:{title:c => 'Time: '+c[0].label}}}, scales: {...cfg.scales, x:{...cfg.scales.x}, y:{...cfg.scales.y, ticks:{...cfg.scales.y.ticks, stepSize:10, autoSkip:false, font:{size:9}}}}}
    });

  } catch (err) {
    console.error('Error loading data:', err);
  }
}

function parseCSV(text) {
  const lines = text.trim().split('\\n');
  if (lines.length === 0) return [];
  
  const header = lines[0].split(',');
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',');
    const row = {};
    for (let j = 0; j < header.length; j++) {
      row[header[j]] = values[j] || '';
    }
    rows.push(row);
  }
  return rows;
}

// Load on startup and refresh every 10 minutes (600000ms)
loadData();
setInterval(loadData, 600000);
</script>
</body>
</html>"""

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    ensure_csv(CSV_FILE, [
        "timestamp", "total_votes",
        "kc_venugopal_votes", "kc_venugopal_pct",
        "vd_satheesan_votes", "vd_satheesan_pct",
        "ramesh_chennithala_votes", "ramesh_chennithala_pct",
        "delta_total", "delta_venugopal", "delta_satheesan", "delta_chennithala",
        "alert",
    ])
    ensure_csv(ALERT_LOG, ["timestamp", "alert"])

    detector = AnomalyDetector()
    prev_total = None

    print("=" * 80, flush=True)
    print("  KERALA CM POLL TRACKER  —  Bot / Manipulation Monitor", flush=True)
    print(f"  Logging to {CSV_FILE}", flush=True)
    print(f"  Alerts to  {ALERT_LOG}", flush=True)
    print(f"  Polling every {INTERVAL_SECONDS}s | Spike detection after {WINDOW_SIZE} samples", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    while True:
        try:
            data = fetch_results()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            candidates = {c["id"]: c for c in data["candidates"]}
            total = data["total_votes"]

            # Compute deltas
            dt = total - prev_total if prev_total is not None else 0
            dv = {cid: (candidates[cid]["votes"] - detector.prev[cid])
                  if detector.prev else 0 for cid in CANDIDATE_IDS}

            # Anomaly check
            alerts = detector.check(candidates, ts)
            alert_str = " | ".join(alerts) if alerts else ""

            # Write CSV row
            row = [
                ts, total,
                candidates["kc-venugopal"]["votes"],
                candidates["kc-venugopal"]["percentage"],
                candidates["vd-satheesan"]["votes"],
                candidates["vd-satheesan"]["percentage"],
                candidates["ramesh-chennithala"]["votes"],
                candidates["ramesh-chennithala"]["percentage"],
                dt,
                dv["kc-venugopal"],
                dv["vd-satheesan"],
                dv["ramesh-chennithala"],
                alert_str,
            ]
            append_csv(CSV_FILE, row)

            # Log alerts separately
            for a in alerts:
                append_csv(ALERT_LOG, [ts, a])

            # Console output
            delta_info = f"  Δ total: +{dt}" if prev_total is not None else ""
            print(
                f"[{ts}] Total: {total:>7} | "
                f"V: {candidates['kc-venugopal']['votes']:>7} ({candidates['kc-venugopal']['percentage']}%) "
                f"S: {candidates['vd-satheesan']['votes']:>7} ({candidates['vd-satheesan']['percentage']}%) "
                f"C: {candidates['ramesh-chennithala']['votes']:>7} ({candidates['ramesh-chennithala']['percentage']}%)"
                f"{delta_info}",
                flush=True,
            )
            if prev_total is not None:
                print(
                    f"         Δ/min  V: +{dv['kc-venugopal']:<5}  "
                    f"S: +{dv['vd-satheesan']:<5}  "
                    f"C: +{dv['ramesh-chennithala']:<5}",
                    flush=True,
                )
            if alerts:
                for a in alerts:
                    print(f"  ⚠️  ALERT: {a}", flush=True)

            prev_total = total

        except Exception as e:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            err_msg = f"ERROR: {e}"
            # Log error as a row with empty vote data
            error_row = [ts, "", "", "", "", "", "", "", "", "", "", "", err_msg]
            append_csv(CSV_FILE, error_row)
            append_csv(ALERT_LOG, [ts, err_msg])
            print(f"[{ts}] {err_msg}", flush=True)

        # Regenerate dashboard after every cycle
        try:
            generate_dashboard()
        except Exception as e:
            print(f"  Dashboard generation failed: {e}", flush=True)

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
