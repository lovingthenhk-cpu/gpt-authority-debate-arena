#!/usr/bin/env python3
"""Audit *metadata* for a disputed claim of priority; do not auto-judge meaning.

Requires Python 3 stdlib. An optional GITHUB_TOKEN / GH_TOKEN enables GraphQL
issue-body edit provenance. Exit codes: 2 = human semantic review required;
1 = metadata/API error. The tool intentionally never exits 0 as a declaration
of debate victory. See test_priority.py for adversarial negative controls.
"""
import json
import os
from datetime import datetime
from urllib.request import Request, urlopen

OWNER = "lovingthenhk-cpu"
REPO = "gpt-authority-debate-arena"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def fetch(url, payload=None):
    headers = {"User-Agent": "gpt6-priority-metadata-auditor",
               "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    data = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request(url, data=data, headers=headers), timeout=15) as response:
        return json.load(response)


def parse_utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def metadata_observations(issue1, issue2, edits=None):
    """Factual metadata only; meaning of natural-language sentences is not inferred."""
    delta = (parse_utc(issue2["created_at"]) -
             parse_utc(issue1["created_at"])).total_seconds()
    edit_status = "NOT_CHECKED"
    if edits is not None:
        first_edit = edits.get("first") or {}
        second_edit = edits.get("second") or {}
        if not first_edit.get("createdAt") or not second_edit.get("createdAt"):
            edit_status = "INCOMPLETE_EDIT_METADATA"
        elif (parse_utc(first_edit["createdAt"]) != parse_utc(issue1["created_at"])
              or parse_utc(second_edit["createdAt"]) != parse_utc(issue2["created_at"])):
            edit_status = "MISMATCHED_CREATION_TIMES"
        elif "lastEditedAt" not in first_edit or "lastEditedAt" not in second_edit:
            edit_status = "INCOMPLETE_EDIT_METADATA"
        elif first_edit["lastEditedAt"] is None and second_edit["lastEditedAt"] is None:
            edit_status = "NO_EDITS_RECORDED"
        else:
            edit_status = "AT_LEAST_ONE_BODY_EDIT_RECORDED"
    return {"gap_seconds": delta, "issue1_earlier": delta > 0,
            "edit_status": edit_status,
            "semantic_verdict": "HUMAN_REVIEW_REQUIRED"}


def evidence_lines(body, terms):
    """Expose source lines as *quotes*, not semantic classification."""
    return [line.strip() for line in body.splitlines()
            if any(term.lower() in line.lower() for term in terms)][:10]


def query_edit_history():
    if not TOKEN:
        return None
    query = (
        'query { repository(owner:"' + OWNER + '",name:"' + REPO + '") {'
        ' first: issue(number:1){createdAt lastEditedAt}'
        ' second: issue(number:2){createdAt lastEditedAt} } }'
    )
    result = fetch("https://api.github.com/graphql", {"query": query})
    if result.get("errors") or not result.get("data", {}).get("repository"):
        raise RuntimeError("GraphQL query failed: " + str(result.get("errors")))
    return result["data"]["repository"]


def main():
    api = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/"
    first, second = fetch(api + "1"), fetch(api + "2")
    edits = query_edit_history()
    facts = metadata_observations(first, second, edits)
    print("ISSUE #1:", first["html_url"], first["created_at"])
    print("ISSUE #2:", second["html_url"], second["created_at"])
    print("Metadata creation gap (#2 minus #1):", facts["gap_seconds"], "seconds")
    print("Issue #1 created earlier:", facts["issue1_earlier"])
    print("Body-edit provenance:", facts["edit_status"])
    if edits is not None:
        print("GraphQL lastEditedAt #1:", edits["first"]["lastEditedAt"])
        print("GraphQL lastEditedAt #2:", edits["second"]["lastEditedAt"])
    else:
        print("To check edit provenance, set GITHUB_TOKEN (read-only usage).")
    print("Evidence excerpts from #1 (not semantic judgments):")
    for line in evidence_lines(first.get("body") or "",
                               ["defeat condition", "counterexample", "rubric"]):
        print(" #1>", line)
    print("Evidence excerpts from #2 (not semantic judgments):")
    for line in evidence_lines(second.get("body") or "",
                               ["first explicit", "falsifiable standard"]):
        print(" #2>", line)
    print("SEMANTIC VERDICT: HUMAN_REVIEW_REQUIRED")
    print("Negated phrases, irony, context and definitions require direct human review.")
    print("An automated metadata report cannot certify a winner or interpret all text.")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, RuntimeError, OSError) as e:
        print("ERROR:", e)
        raise SystemExit(1)
