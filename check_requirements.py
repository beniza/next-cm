from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent


def read_text(name: str) -> str:
    path = ROOT / name
    if not path.exists():
        raise AssertionError(f"Missing required file: {name}")
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {label}: {needle}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"Forbidden {label}: {needle}")


def require_count(text: str, needle: str, expected: int, label: str) -> None:
    actual = text.count(needle)
    if actual != expected:
        raise AssertionError(f"Unexpected {label}: expected {expected}, found {actual}")


def main() -> int:
    index = read_text("index.html")
    venugopal = read_text("profile-venugopal.html")
    satheesan = read_text("profile-satheesan.html")
    chennithala = read_text("profile-chennithala.html")
    inc_impact = read_text("inc-impact.html")

    require(index, "Tracking Window", "homepage tracked-window section")
    require(index, "Methodology & Caveats", "homepage caveat section")
    require(index, "Final Totals Comparison", "homepage final totals section")
    require(index, "inc-impact.html", "homepage INC implications link")
    require(index, "Key Findings", "homepage insights section")
    forbid(index, "Last 20m", "homepage recent-window wording")
    forbid(index, "Dominant Momentum", "homepage recent-window framing")

    for name, text in [
        ("profile-venugopal.html", venugopal),
        ("profile-satheesan.html", satheesan),
        ("profile-chennithala.html", chennithala),
    ]:
        require(text, "SWOT Analysis", f"{name} SWOT section")
        require(text, "Tracking Window Reading", f"{name} tracking section")
        require(text, "Research Context", f"{name} research section")
        require(text, "site-data.js", f"{name} shared data script")
        require_count(text, "<!DOCTYPE html>", 1, f"{name} document root")
        forbid(text, "Last 20m", f"{name} recent-window wording")
        forbid(text, "Profile Brief", f"{name} stale profile title")

    require(inc_impact, "What The CM Choice Means For INC", "INC impact title")
    require(inc_impact, "Opportunities", "INC impact opportunities section")
    require(inc_impact, "Challenges", "INC impact challenges section")
    require(inc_impact, "Scenario Lens", "INC impact scenario section")

    print("Requirement checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Requirement check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)