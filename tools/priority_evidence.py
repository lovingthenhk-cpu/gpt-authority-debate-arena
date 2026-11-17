#!/usr/bin/env python3
"""Audit what GitHub's issue API can establish, without pretending to read history.

With no historical snapshots, issue creation order is observable but priority of
*original issue-body content* is NOT identified. Pure stdlib; optional offline input.
"""
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime

API = 'https://api.github.com/repos/lovingthenhk-cpu/gpt-authority-debate-arena/issues/'


def parse_time(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def report(first, second):
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
    return {
        'observations': observations,
        'creation_time_delta_seconds_2_minus_1': delta,
        'creation_order': '1_before_2' if delta > 0 else ('2_before_1' if delta < 0 else 'tie'),
        'original_body_content_at_creation': 'NOT_OBSERVED',
        'first_explicit_standard': 'UNDETERMINED',
        'why': 'Issue bodies can change; creation timestamps plus current bodies do not identify the original texts.',
        'note': 'Body hashes describe ONLY the current retrieved versions; no semantic keyword inference is made.',
    }


def fetch(number):
    req = urllib.request.Request(API + str(number), headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'gpt-debate-observation-audit',
    })
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', help='Offline JSON with issue1 and issue2 objects')
    args = parser.parse_args()
    if args.fixture:
        with open(args.fixture, encoding='utf-8') as f:
            source = json.load(f)
        first, second = source['issue1'], source['issue2']
    else:
        first, second = fetch(1), fetch(2)
    print(json.dumps(report(first, second), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
