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
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {e}", flush=True)

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
