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
    """Read poll_data.csv and write a self-contained HTML dashboard."""
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["total_votes"]:  # skip error rows
                rows.append(r)

    if not rows:
        return

    # Build JSON arrays for the chart
    labels = [r["timestamp"][5:] for r in rows]  # trim year for brevity
    totals = [int(r["total_votes"]) for r in rows]
    v_votes = [int(r["kc_venugopal_votes"]) for r in rows]
    s_votes = [int(r["vd_satheesan_votes"]) for r in rows]
    c_votes = [int(r["ramesh_chennithala_votes"]) for r in rows]
    d_total = [int(r["delta_total"]) for r in rows]
    d_v = [int(r["delta_venugopal"]) for r in rows]
    d_s = [int(r["delta_satheesan"]) for r in rows]
    d_c = [int(r["delta_chennithala"]) for r in rows]

    # Aggregate deltas into 10-minute buckets
    BUCKET_SIZE = 10
    d_labels_10 = []
    d_v_10, d_s_10, d_c_10 = [], [], []
    for i in range(0, len(rows), BUCKET_SIZE):
        chunk = rows[i:i + BUCKET_SIZE]
        d_labels_10.append(chunk[-1]["timestamp"][5:])
        d_v_10.append(sum(int(r["delta_venugopal"]) for r in chunk))
        d_s_10.append(sum(int(r["delta_satheesan"]) for r in chunk))
        d_c_10.append(sum(int(r["delta_chennithala"]) for r in chunk))

    # Collect alerts
    alerts_data = []
    with open(ALERT_LOG, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            alerts_data.append({"ts": r["timestamp"], "msg": r["alert"]})

    latest = rows[-1]
    updated = latest["timestamp"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kerala CM Poll Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#0f172a; color:#e2e8f0; padding:20px; }}
  h1 {{ font-size:1.6rem; color:#f8fafc; margin-bottom:4px; }}
  .sub {{ color:#94a3b8; font-size:.85rem; margin-bottom:20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin-bottom:24px; }}
  .card {{ background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; }}
  .card .label {{ font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; color:#94a3b8; }}
  .card .value {{ font-size:1.8rem; font-weight:700; margin-top:4px; }}
  .card .delta {{ font-size:.8rem; color:#4ade80; margin-top:2px; }}
  .card.saffron .value {{ color:#FF9933; }}
  .card.green .value {{ color:#22c55e; }}
  .card.red .value {{ color:#ef4444; }}
  .chart-box {{ background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; margin-bottom:20px; }}
  .chart-box h2 {{ font-size:1rem; color:#cbd5e1; margin-bottom:12px; }}
  canvas {{ width:100%!important; }}
  .alerts {{ background:#1e293b; border-radius:10px; padding:16px; border:1px solid #334155; }}
  .alerts h2 {{ font-size:1rem; color:#fbbf24; margin-bottom:12px; }}
  .alerts .empty {{ color:#64748b; font-style:italic; }}
  .alert-row {{ padding:6px 0; border-bottom:1px solid #334155; font-size:.82rem; }}
  .alert-row:last-child {{ border-bottom:none; }}
  .alert-ts {{ color:#94a3b8; margin-right:8px; }}
  .alert-msg {{ color:#fbbf24; }}
  .alert-msg.error {{ color:#ef4444; }}
  .refresh {{ color:#64748b; font-size:.75rem; margin-top:16px; text-align:center; }}
</style>
</head>
<body>
<h1>Kerala CM 2026 — Poll Tracker</h1>
<p class="sub">Last updated: {updated} &nbsp;|&nbsp; {len(rows)} data points &nbsp;|&nbsp; {len(alerts_data)} alerts</p>

<div class="grid">
  <div class="card">
    <div class="label">Total Votes</div>
    <div class="value">{int(latest['total_votes']):,}</div>
    <div class="delta">+{latest['delta_total']}/min</div>
  </div>
  <div class="card saffron">
    <div class="label">K.C. Venugopal</div>
    <div class="value">{int(latest['kc_venugopal_votes']):,}</div>
    <div class="delta">{latest['kc_venugopal_pct']}% &nbsp; +{latest['delta_venugopal']}/min</div>
  </div>
  <div class="card green">
    <div class="label">V.D. Satheesan</div>
    <div class="value">{int(latest['vd_satheesan_votes']):,}</div>
    <div class="delta">{latest['vd_satheesan_pct']}% &nbsp; +{latest['delta_satheesan']}/min</div>
  </div>
  <div class="card red">
    <div class="label">Ramesh Chennithala</div>
    <div class="value">{int(latest['ramesh_chennithala_votes']):,}</div>
    <div class="delta">{latest['ramesh_chennithala_pct']}% &nbsp; +{latest['delta_chennithala']}/min</div>
  </div>
</div>

<div class="chart-box">
  <h2>Cumulative Votes Over Time</h2>
  <canvas id="cumChart" height="80"></canvas>
</div>

<div class="chart-box">
  <h2>Votes Per 10 Minutes (\u0394) \u2014 Spike Detection</h2>
  <canvas id="deltaChart" height="200"></canvas>
</div>

<div class="alerts">
  <h2>Alerts &amp; Errors</h2>
  {"".join(
    f'<div class="alert-row"><span class="alert-ts">{a["ts"][5:]}</span>'
    f'<span class="alert-msg {"error" if a["msg"].startswith("ERROR") else ""}">{a["msg"]}</span></div>'
    for a in reversed(alerts_data[-50:])
  ) if alerts_data else '<p class="empty">No anomalies detected yet. Monitoring...</p>'}
</div>

<p class="refresh">Dashboard auto-regenerates every poll cycle. Refresh browser to see latest.</p>

<script>
const labels = {json.dumps(labels)};
const cfg = {{ responsive:true, interaction:{{mode:'index',intersect:false}}, plugins:{{legend:{{labels:{{color:'#94a3b8'}}}}}}, scales:{{x:{{ticks:{{color:'#64748b',maxTicksLimit:20}},grid:{{color:'#1e293b'}}}},y:{{ticks:{{color:'#64748b'}},grid:{{color:'#334155'}},beginAtZero:false}}}} }};

new Chart(document.getElementById('cumChart'), {{
  type:'line',
  data:{{
    labels,
    datasets:[
      {{label:'Venugopal',data:{json.dumps(v_votes)},borderColor:'#FF9933',backgroundColor:'rgba(255,153,51,.1)',fill:false,tension:.3,pointRadius:0,borderWidth:2}},
      {{label:'Satheesan',data:{json.dumps(s_votes)},borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,.1)',fill:false,tension:.3,pointRadius:0,borderWidth:2}},
      {{label:'Chennithala',data:{json.dumps(c_votes)},borderColor:'#ef4444',backgroundColor:'rgba(239,68,68,.1)',fill:false,tension:.3,pointRadius:0,borderWidth:2,yAxisID:'y1'}}
    ]
  }},
  options:{{...cfg, scales:{{...cfg.scales, y:{{...cfg.scales.y, position:'left', title:{{display:true,text:'Venugopal / Satheesan',color:'#94a3b8'}}}}, y1:{{position:'right', ticks:{{color:'#ef4444'}}, grid:{{drawOnChartArea:false}}, title:{{display:true,text:'Chennithala',color:'#ef4444'}}, beginAtZero:false}} }} }}
}});

new Chart(document.getElementById('deltaChart'), {{
  type:'bar',
  data:{{
    labels:{json.dumps(d_labels_10)},
    datasets:[
      {{label:'\u0394 Venugopal (10m)',data:{json.dumps(d_v_10)},backgroundColor:'rgba(255,153,51,.7)'}},
      {{label:'\u0394 Satheesan (10m)',data:{json.dumps(d_s_10)},backgroundColor:'rgba(34,197,94,.7)'}},
      {{label:'\u0394 Chennithala (10m)',data:{json.dumps(d_c_10)},backgroundColor:'rgba(239,68,68,.7)'}}
    ]
  }},
  options:{{...cfg, plugins:{{...cfg.plugins, tooltip:{{callbacks:{{title:function(c){{return 'Time: '+c[0].label}}}}}}}}, scales:{{...cfg.scales, x:{{...cfg.scales.x}}, y:{{...cfg.scales.y, ticks:{{...cfg.scales.y.ticks, stepSize:10, autoSkip:false, font:{{size:9}}}}}}}}}}
}});
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
