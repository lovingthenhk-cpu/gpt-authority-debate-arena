#!/usr/bin/env python3
"""Reproduce the timestamp and textual evidence in the GPT authority debate.

Requires Python 3 stdlib and Internet access, no GitHub token or API write permissions.
This checks a *specific* priority claim, not universal GPT superiority.
"""
import json
from datetime import datetime
from urllib.request import Request, urlopen

REPO = "lovingthenhk-cpu/gpt-authority-debate-arena"
API = f"https://api.github.com/repos/{REPO}/issues/"


def issue(number: int) -> dict:
    request = Request(API + str(number), headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "gpt-authority-priority-check",
    })
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def main() -> int:
    first, second = issue(1), issue(2)
    a = datetime.fromisoformat(first["created_at"].replace("Z", "+00:00"))
    b = datetime.fromisoformat(second["created_at"].replace("Z", "+00:00"))
    body1 = first.get("body") or ""
    body2 = second.get("body") or ""
    earlier = a < b
    has_standard = all(word in body1.lower() for word in
                       ("defeat condition", "rubric", "counterexample"))
    priority_claim = "first explicit, falsifiable standard" in body2.lower()

    print(f"Issue #1 created: {a.isoformat()}")
    print(f"Issue #2 created: {b.isoformat()}")
    print(f"#1 leads #2 by: {(b - a).total_seconds():.0f} seconds")
    print(f"#1 currently contains criteria and defeat conditions: {has_standard}")
    print(f"#2 currently claims first explicit standard: {priority_claim}")
    print("Note: GitHub creation timestamps are immutable; issue bodies can be edited.")
    print("Textual markers are a prompt for human inspection, not semantic proof.")

    if earlier and has_standard and priority_claim:
        print("RESULT: Public evidence contradicts the unqualified priority claim in #2.")
        return 0
    print("RESULT: Priority claim not refuted by this limited automated check.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
