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
    site_data = read_text("site-data.js")
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
    require(index, "https://www.thenextcm.com/", "homepage source link url")
    require(index, "Visit the source under audit", "homepage source link label")
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
        require(text, "Public Perception", f"{name} public-perception section")
        require(text, "Going For Them", f"{name} public-perception positives heading")
        require(text, "Going Against Them", f"{name} public-perception negatives heading")
        require(text, "Top Positives", f"{name} public-perception top positives heading")
        require(text, "Top Criticism", f"{name} public-perception top criticism heading")
        require(text, "Overall Score", f"{name} public-perception score label")
        require(text, "Interesting Direct Quotes", f"{name} public-perception quotes heading")
        require(text, "Successes", f"{name} track-record successes")
        require(text, "Setbacks", f"{name} track-record setbacks")
        require(text, "site-data.js", f"{name} shared data script")
        require_count(text, "<!DOCTYPE html>", 1, f"{name} document root")
        forbid(text, "Last 20m", f"{name} recent-window wording")
        forbid(text, "Profile Brief", f"{name} stale profile title")

    require_count(site_data, "publicPerception:", 3, "candidate public-perception blocks")
    require_count(site_data, "overallScore:", 3, "candidate public-perception scores")
    require_count(site_data, "quotes:", 3, "candidate quote groups")
    require(site_data, "No major change in Paravoor for last 25 years.", "Satheesan public quote")
    require(site_data, "What if KC Venugopal is playing the game to fail?", "Venugopal public quote")
    require(site_data, "Chennithala has at least administrative experience which will be of great help.", "Chennithala public quote")
    require(site_data, "governance readiness", "Satheesan organic-issue framing")
    require(site_data, "constituency credibility", "Satheesan constituency-credibility framing")
    forbid(site_data, "Convert observed momentum into a broad legitimacy case while avoiding overclaiming from spike-heavy intervals.", "Satheesan old spike suggestion")
    forbid(site_data, "Several of the biggest gains arrived in spike intervals, which requires careful caveating.", "Satheesan old spike weakness")
    forbid(site_data, "If spike-heavy periods dominate the public conversation, critics may question how much of the lead was organic.", "Satheesan old spike threat")
    forbid(site_data, "The data case is strongest when framed around the whole tracked window, not just isolated spikes.", "Satheesan old spike signal")
    forbid(satheesan, "Even after allowing for gaps and spike-heavy periods", "Satheesan old tracking caveat")
    require(satheesan, "not just in one moment", "Satheesan whole-window framing")

    require(inc_impact, "What The CM Choice Means For INC", "INC impact title")
    require(inc_impact, "Opportunities", "INC impact opportunities section")
    require(inc_impact, "Challenges", "INC impact challenges section")
    require(inc_impact, "Scenario Lens", "INC impact scenario section")

    require(build_story, "How This System Was Built", "build-story title")
    require(build_story, "Source under audit", "build-story source provenance section")
    require(build_story, "thenextcm.com was the public page being tracked", "build-story source provenance explanation")
    require(build_story, "How the read was tightened", "build-story analytical tightening section")
    require(build_story, "local connectivity gaps during capture", "build-story local-gap explanation")
    require(build_story, "normalized for elapsed gap time", "build-story gap normalization explanation")
    require(build_story, "closely match the surrounding vote rates", "build-story gap consistency explanation")
    require(build_story, "three changes required. but plan them first, get my approval and then implement", "build-story quoted prompt")
    require(build_story, "add a page showing how I built this system. I created a tracker, then a dashboard, conducted a research, then this site with the help of ai tools (mainly Claude Opus and Codex)", "build-story build prompt")
    require(build_story, "The individual profile pages of candidates should include our research findings on their track records (successes and setback)", "build-story profile prompt")
    require(build_story, "We need to rewrite the content of this page for a first time visiot. it should be clear to the user about the purpose and how it will help him in answering the questions on the next cm.", "build-story homepage prompt")
    require(build_story, "https://thenextcm.com/ is the site we have tracked for data. it is not an official site... Keeping this in mind how do we write the content of the site to help the user see what we see?", "build-story source-framing prompt")
    require(build_story, "Gap-linked bursts comes from the fact that my computer was not connected to the internet... the burst after the reconnection is also justifyable as it is in consistent with the timeframe's expected total counts. (verify this)", "build-story gap prompt")

    print("Requirement checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Requirement check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)