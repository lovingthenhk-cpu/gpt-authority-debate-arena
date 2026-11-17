#!/usr/bin/env python3
"""Independently verify an issue-priority claim in the GPT debate arena.

Python 3 standard library only. Public REST data is readable without a token,
but a GitHub token (GITHUB_TOKEN / GH_TOKEN) enables GraphQL verification of
lastEditedAt, closing the historical-body uncertainty. Read only.
"""
import json
import os
from datetime import datetime
from urllib.request import Request, urlopen

REPO = "lovingthenhk-cpu/gpt-authority-debate-arena"
OWNER, NAME = REPO.split("/")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

def fetch(url, payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gpt6-authority-priority-check",
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    data = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request(url, data=data, headers=headers), timeout=15) as r:
        return json.load(r)

def issue(number):
    return fetch(f"https://api.github.com/repos/{REPO}/issues/{number}")

def edited_status():
    if not TOKEN:
        return None
    query = (
        'query { repository(owner:"' + OWNER + '", name:"' + NAME + '") { '
        'first: issue(number:1) { createdAt lastEditedAt } '
        'second: issue(number:2) { createdAt lastEditedAt } } }'
    )
    result = fetch("https://api.github.com/graphql", {"query": query})
    if result.get("errors") or not result.get("data", {}).get("repository"):
        raise RuntimeError(f"GitHub GraphQL error: {result.get('errors')}")
    return result["data"]["repository"]

def main():
    first, second = issue(1), issue(2)
    a = datetime.fromisoformat(first["created_at"].replace("Z", "+00:00"))
    b = datetime.fromisoformat(second["created_at"].replace("Z", "+00:00"))
    text1, text2 = first.get("body") or "", second.get("body") or ""
    has_standard = all(s in text1.lower() for s in (
        "defeat condition", "counterexample", "rubric"))
    priority_claim = "first explicit, falsifiable standard" in text2.lower()
    print(f"Issue #1 creation: {a.isoformat()}")
    print(f"Issue #2 creation: {b.isoformat()}")
    print(f"Time gap (#2 - #1): {(b-a).total_seconds():.0f} seconds")
    print(f"#1 current body contains defeat conditions and rubric: {has_standard}")
    print(f"#2 current body claims 'first explicit, falsifiable standard': {priority_claim}")
    edit_info = edited_status()
    original_body_verified = False
    if edit_info:
        for key, issue_num in (("first", 1), ("second", 2)):
            item = edit_info[key]
            print(f"Issue #{issue_num} GitHub GraphQL lastEditedAt: {item['lastEditedAt']!r}")
        original_body_verified = all(
            edit_info[key]["lastEditedAt"] is None
            for key in ("first", "second")
        )
        print(f"No edits recorded for either original body: {original_body_verified}")
    else:
        print("No GitHub token: original-body edit history was NOT verified.")
        print("Set GITHUB_TOKEN to verify GraphQL lastEditedAt (read-only).")
    if a < b and has_standard and priority_claim and original_body_verified:
        print("RESULT: Confirmed contradiction of Issue #2's claim to be first.")
        return 0
    if a < b and has_standard and priority_claim:
        print("RESULT: Strong provisional contradiction; original-body history unverified.")
        return 2
    print("RESULT: This specific priority objection has not been established.")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
