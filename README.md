# Kerala CM Vote Audit Tracker

## Purpose
This project monitors vote results from thenextcm and helps audit whether vote movement is consistent over time.

The goal is to:
- Track vote counts continuously at a fixed interval.
- Detect unusual spikes or suspicious changes in vote flow.
- Show what votes reflect over time (momentum, trend direction, and share of new votes).

## What This Tracks
The tracker polls:
- API endpoint: `https://votekerala-cm.emergent.host/api/results`
- Polling interval: once per minute

It records:
- Total votes
- Per-candidate votes and percentages
- Minute deltas per candidate and total
- Alerts for anomalies or errors

Dependencies:
- Uses only Python standard library packages (no third-party pip dependencies).

## Files
- `tracker.py`: polling loop, anomaly detection, dashboard generation
- `poll_data.csv`: time-series vote snapshots and deltas
- `alerts.csv`: spike/decrease/error alerts
- `dashboard.html`: live dashboard that reads local CSV files

## How to Run
1. Start tracking:

```bash
python -u tracker.py
```

2. Open dashboard:
- Open `dashboard.html` in a browser.
- The dashboard reload logic updates every minute.

## Audit Signals in Dashboard
Top cards show:
- Current share percentage
- 20-minute average vote rate (`/min`)
- 20-minute trend in percentage points (`pp`)
- Overall trend since tracking started

"Who Is Capturing New Votes?" shows:
- Recent share of newly added votes per candidate
- A direct comparison callout (for example, one candidate capturing ~90%+ of new votes)

"Votes Per 10 Minutes (Delta)" shows:
- Aggregated vote inflow per candidate by 10-minute bucket
- Useful to compare momentum concentration over time

## Interpreting Consistency
Use this tracker to verify whether voting looks structurally consistent:
- Smooth, stable deltas usually indicate normal accumulation.
- Sudden outsized spikes may require inspection.
- A persistent high share of new votes for one candidate indicates strong momentum concentration.
- Divergence between 20-minute trend and overall trend can indicate a recent shift.

## Notes
- This project is an audit/monitoring aid; it does not prove intent or manipulation by itself.
- Always combine numeric signals with contextual checks before drawing conclusions.
