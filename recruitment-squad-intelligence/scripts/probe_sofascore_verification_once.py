"""One-page Scrapling check that stops when human verification is visible."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from scrapling.fetchers import DynamicSession


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if not args.url.startswith("https://www.sofascore.com/football/match/"):
        parser.error("Expected a Sofascore match webpage URL")
    if not args.label.replace("-", "").replace("_", "").isalnum():
        parser.error("Invalid label")
    output = ROOT / "csl_2026_capture" / args.label
    output.mkdir(parents=True, exist_ok=True)
    runtime_temp = ROOT / "csl_2026_capture" / "runtime_temp"
    runtime_temp.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = tempfile.tempdir = str(runtime_temp)
    report = {"requested_url": args.url,
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "status": "pending"}

    def capture(page):
        page.wait_for_timeout(6000)
        body = page.locator("body").inner_text()
        challenge_frames = page.locator('iframe[src*="challenges.cloudflare.com"], '
                                        'iframe[title*="hallenge"]').count()
        verification_text = "verify you are human" in body.lower()
        turnstile_widget = page.locator('input[name="cf-turnstile-response"]').count()
        page.screenshot(path=str(output / "page.png"), full_page=False)
        (output / "page.txt").write_text(body, encoding="utf-8")
        (output / "page.html").write_text(page.content(), encoding="utf-8")
        report.update(observed_url=page.url, title=page.title(),
                      verification_frame_count=challenge_frames,
                      verification_text_visible=verification_text,
                      turnstile_widget_count=turnstile_widget,
                      tabs=page.get_by_role("tab").all_text_contents(),
                      status="verification_stop" if challenge_frames or verification_text or turnstile_widget
                      else "page_observed")

    try:
        with DynamicSession(real_chrome=True, headless=False, google_search=False,
                            network_idle=False, timeout=60000, retries=1,
                            locale="en-GB", timezone_id="Asia/Shanghai",
                            disable_resources=False,
                            additional_args={"viewport": {"width": 1440, "height": 1000}}) as session:
            response = session.fetch(args.url, page_action=capture)
            report["http_status"] = response.status
    except Exception as exc:
        report.update(status="fetch_error", error=f"{type(exc).__name__}: {exc}")
    (output / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
