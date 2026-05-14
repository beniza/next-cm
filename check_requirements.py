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
    build_story = read_text("how-it-was-built.html")

    require(index, "Tracking Window", "homepage tracked-window section")
    require(index, "Methodology & Caveats", "homepage caveat section")
    require(index, "Final Totals Comparison", "homepage final totals section")
    require(index, "inc-impact.html", "homepage INC implications link")
    require(index, "how-it-was-built.html", "homepage build-story link")
    require(index, "How This Was Built", "homepage build-story label")
    require(index, "Key Findings", "homepage insights section")
    require(index, "Start Here", "homepage first-visit section")
    require(index, "unofficial Kerala CM poll", "homepage source-status framing")
    require(index, "could not establish who owns thenextcm.com", "homepage ownership caveat")
    require(index, "public-facing vote stream", "homepage experiment framing")
    require(index, "hidden manipulation still cannot be ruled out", "homepage uncertainty framing")
    require(index, "about 90% of all newly observed votes", "homepage main finding")
    require(index, "opening base", "homepage unresolved mystery")
    require(index, "local connectivity gaps during capture", "homepage local-gap explanation")
    require(index, "normalized for elapsed gap time", "homepage gap normalization explanation")
    require(index, "closely match the surrounding vote rates", "homepage gap consistency explanation")
    forbid(index, "Last 20m", "homepage recent-window wording")
    forbid(index, "Dominant Momentum", "homepage recent-window framing")
    forbid(index, "batched source updates", "homepage old batching explanation")

    for name, text in [
        ("profile-venugopal.html", venugopal),
        ("profile-satheesan.html", satheesan),
        ("profile-chennithala.html", chennithala),
    ]:
        require(text, "SWOT Analysis", f"{name} SWOT section")
        require(text, "Tracking Window Reading", f"{name} tracking section")
        require(text, "Research Context", f"{name} research section")
        require(text, "Track Record", f"{name} track-record section")
        require(text, "Successes", f"{name} track-record successes")
        require(text, "Setbacks", f"{name} track-record setbacks")
        require(text, "site-data.js", f"{name} shared data script")
        require_count(text, "<!DOCTYPE html>", 1, f"{name} document root")
        forbid(text, "Last 20m", f"{name} recent-window wording")
        forbid(text, "Profile Brief", f"{name} stale profile title")

    require(inc_impact, "What The CM Choice Means For INC", "INC impact title")
    require(inc_impact, "Opportunities", "INC impact opportunities section")
    require(inc_impact, "Challenges", "INC impact challenges section")
    require(inc_impact, "Scenario Lens", "INC impact scenario section")

    require(build_story, "How This System Was Built", "build-story title")
    require(build_story, "three changes required. but plan them first, get my approval and then implement", "build-story quoted prompt")
    require(build_story, "add a page showing how I built this system. I created a tracker, then a dashboard, conducted a research, then this site with the help of ai tools (mainly Claude Opus and Codex)", "build-story build prompt")
    require(build_story, "The individual profile pages of candidates should include our research findings on their track records (successes and setback)", "build-story profile prompt")
    require(build_story, "We need to rewrite the content of this page for a first time visiot. it should be clear to the user about the purpose and how it will help him in answering the questions on the next cm.", "build-story homepage prompt")

    print("Requirement checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Requirement check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)