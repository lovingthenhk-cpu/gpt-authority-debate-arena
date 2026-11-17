#!/usr/bin/env python3
"""Audit what GitHub's issue API can establish, without pretending to read history.

With no historical snapshots, issue creation order is observable but priority of
*original issue-body content* is NOT identified. Pure stdlib; optional offline input.
"""
import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime

API = 'https://api.github.com/repos/lovingthenhk-cpu/gpt-authority-debate-arena/issues/'


def parse_time(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def report(first, second, edits=None):
    a, b = parse_time(first['created_at']), parse_time(second['created_at'])
    delta = int((b - a).total_seconds())
    observations = []
    for issue in (first, second):
        body = issue.get('body') or ''
        observations.append({
            'number': issue['number'],
            'created_at': issue['created_at'],
            'current_body_sha256': hashlib.sha256(body.encode()).hexdigest(),
            'current_body_characters': len(body),
        })
    provenance = 'REST_ONLY_NO_EDIT_HISTORY'
    priority = 'UNDETERMINED'
    if edits is not None:
        a1, a2 = edits['issue1'], edits['issue2']
        if (a1['createdAt'] == first['created_at'] and a2['createdAt'] == second['created_at'] and a1['lastEditedAt'] is None and a2['lastEditedAt'] is None):
            provenance = 'NO_EDITS_REPORTED_BY_GITHUB'
            priority = 'HUMAN_SEMANTIC_REVIEW_REQUIRED'
    return {
        'observations': observations,
        'creation_time_delta_seconds_2_minus_1': delta,
        'creation_order': '1_before_2' if delta > 0 else ('2_before_1' if delta < 0 else 'tie'),
        'original_body_provenance': provenance,
        'first_explicit_standard': priority,
        'why': 'GraphQL no-edit metadata supports original content provenance; text semantics require human review.' if edits is not None and provenance == 'NO_EDITS_REPORTED_BY_GITHUB' else 'Without verified no-edit metadata, original issue text is unobserved.',
        'note': 'Body hashes describe ONLY the current retrieved versions; no semantic keyword inference is made.',
    }


def fetch(number):
    req = urllib.request.Request(API + str(number), headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'gpt-debate-observation-audit',
    })
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def fetch_edits(token):
    query = 'query { repository(owner:"lovingthenhk-cpu",name:"gpt-authority-debate-arena") { issue1:issue(number:1){createdAt lastEditedAt} issue2:issue(number:2){createdAt lastEditedAt} } }'
    request = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': query}).encode(), headers={'Authorization': 'Bearer ' + token, 'Content-Type':'application/json', 'User-Agent':'priority-evidence-review'}, method='POST')
    with urllib.request.urlopen(request,timeout=15) as r:
        return json.load(r)['data']['repository']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', help='Offline JSON with issue1 and issue2 objects')
    args = parser.parse_args()
    if args.fixture:
        with open(args.fixture, encoding='utf-8') as f:
            source = json.load(f)
        first, second = source['issue1'], source['issue2']
        edits = source.get('editMetadata')
    else:
        first, second = fetch(1), fetch(2)
        token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        edits = fetch_edits(token) if token else None
    print(json.dumps(report(first, second, edits), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
