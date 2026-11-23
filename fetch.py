#!/usr/bin/env python3
"""
Fetch real GitHub contribution data and repository metadata.
Supports GitHub GraphQL API (authenticated via GH_TOKEN) and public HTML/REST fallback.
Never fabricates statistics or repository data.
"""

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)
CONTRIB_FILE = DATA_DIR / 'contributions.json'

DEFAULT_USER = 'krishanurastogi06-byte'
USERNAME = os.getenv('GH_USER', DEFAULT_USER).strip()
TOKEN = os.getenv('GH_TOKEN', os.getenv('GITHUB_TOKEN', '')).strip()

HEADERS = {
    'User-Agent': f'github-profile-svg-fetcher ({USERNAME})',
    'Accept': 'application/vnd.github.v3+json',
}
if TOKEN:
    HEADERS['Authorization'] = f'Bearer {TOKEN}'


def fetch_contributions_graphql(username: str, token: str):
    """Fetch 365-day contribution calendar using GitHub GraphQL API."""
    now = dt.datetime.now(dt.timezone.utc)
    begin = now - dt.timedelta(days=364)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({
        'query': query,
        'variables': {
            'login': username,
            'from': begin.isoformat(),
            'to': now.isoformat()
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': HEADERS['User-Agent']
        }
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.load(res)

    if data.get('errors') or not data.get('data', {}).get('user'):
        err = data.get('errors', [{'message': 'User not found'}])
        raise RuntimeError(f"GraphQL error: {err}")

    calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
    weeks = calendar.get('weeks', [])
    days = []
    for w in weeks:
        for d in w.get('contributionDays', []):
            days.append({
                'date': d['date'],
                'count': int(d['contributionCount'])
            })
    return days, calendar.get('totalContributions')


def fetch_contributions_public(username: str):
    """Fetch contribution calendar from public GitHub contributions page."""
    url = f'https://github.com/users/{username}/contributions'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=30) as res:
        html = res.read().decode('utf-8', errors='ignore')

    # Parse cells: <td ... data-date="YYYY-MM-DD" id="contribution-day-component-X-Y" ...>
    cell_re = re.compile(
        r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="([^"]+)"[^>]*data-level="(\d+)"',
        re.DOTALL
    )
    cells = cell_re.findall(html)
    if not cells:
        cell_re = re.compile(
            r'<td[^>]*id="([^"]+)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d+)"',
            re.DOTALL
        )
        cells = [(d, i, l) for (i, d, l) in cell_re.findall(html)]

    if not cells:
        raise RuntimeError("Failed to parse public contribution calendar HTML")

    # Parse tooltips for exact counts: <tool-tip for="id">X contribution(s) on ...</tool-tip>
    tip_re = re.compile(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', re.DOTALL)
    tips = dict(tip_re.findall(html))

    days = []
    for date_str, cid, _ in cells:
        tip = tips.get(cid, '').strip()
        m = re.search(r'(\d+)\s+contribution', tip)
        count = int(m.group(1)) if m else 0
        days.append({'date': date_str, 'count': count})

    return days, sum(d['count'] for d in days)


def fetch_public_repositories(username: str):
    """Fetch public repositories and metadata from GitHub REST API."""
    url = f'https://api.github.com/users/{username}/repos?per_page=100&sort=updated'
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            repos_raw = json.load(res)
    except Exception as exc:
        print(f"Warning: Could not fetch repositories from GitHub API: {exc}", file=sys.stderr)
        return []

    repos = []
    for r in repos_raw:
        if r.get('fork') and not r.get('stargazers_count'):
            # Skip fork repos unless starred
            continue
        repos.append({
            'name': r.get('name'),
            'description': r.get('description') or '',
            'language': r.get('language') or 'Code',
            'stars': r.get('stargazers_count', 0),
            'forks': r.get('forks_count', 0),
            'url': r.get('html_url'),
            'homepage': r.get('homepage') or '',
            'topics': r.get('topics', []),
            'updated_at': r.get('updated_at', '')
        })
    return repos


def calculate_analytics(days: list):
    """Calculate streaks, active days, busiest day, and monthly breakdowns."""
    if not days:
        return {
            'total_contributions': 0,
            'active_days': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'peak_day': {'date': '', 'count': 0},
            'monthly': []
        }

    # Sort days by date
    days_sorted = sorted(days, key=lambda d: d['date'])
    today_str = dt.date.today().isoformat()
    yesterday_str = (dt.date.today() - dt.timedelta(days=1)).isoformat()

    total_contributions = sum(d['count'] for d in days_sorted)
    active_days = sum(1 for d in days_sorted if d['count'] > 0)

    # Streaks
    current_streak = 0
    longest_streak = 0
    running_streak = 0
    for d in days_sorted:
        if d['count'] > 0:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 0

    # Active streak ending today or yesterday
    active_streak = 0
    for d in reversed(days_sorted):
        if d['count'] > 0:
            active_streak += 1
        elif d['date'] == today_str:
            # Current day might not have contributions yet
            continue
        elif d['date'] == yesterday_str:
            continue
        else:
            break

    peak_day = max(days_sorted, key=lambda d: d['count'])

    # Monthly breakdown (last 12 months)
    monthly_dict = defaultdict(int)
    for d in days_sorted:
        m = d['date'][:7]  # YYYY-MM
        monthly_dict[m] += d['count']

    monthly = []
    for ym in sorted(monthly_dict.keys()):
        try:
            m_dt = dt.datetime.strptime(ym, '%Y-%m')
            label = m_dt.strftime('%b')
        except ValueError:
            label = ym
        monthly.append({
            'year_month': ym,
            'label': label,
            'count': monthly_dict[ym]
        })

    return {
        'total_contributions': total_contributions,
        'active_days': active_days,
        'current_streak': active_streak,
        'longest_streak': longest_streak,
        'peak_day': peak_day,
        'monthly': monthly[-12:]  # keep trailing 12 months
    }


def main():
    print(f"Fetching GitHub data for user: {USERNAME}")
    days = None
    total = None

    # Try GraphQL first if token is available
    if TOKEN:
        try:
            print("Attempting GitHub GraphQL API...")
            days, total = fetch_contributions_graphql(USERNAME, TOKEN)
            print(f"GraphQL succeeded: {len(days)} days fetched.")
        except Exception as exc:
            print(f"GraphQL fetch failed ({exc}), falling back to public page...", file=sys.stderr)

    # Fallback to public contribution calendar
    if not days:
        try:
            print("Attempting public contribution calendar...")
            days, total = fetch_contributions_public(USERNAME)
            print(f"Public fetch succeeded: {len(days)} days fetched.")
        except Exception as exc:
            print(f"Public fetch failed ({exc})", file=sys.stderr)

    # If both failed, check existing contributions.json
    if not days:
        if CONTRIB_FILE.is_file():
            try:
                cached = json.loads(CONTRIB_FILE.read_text(encoding='utf-8'))
                if cached.get('days'):
                    print("Warning: Network failed. Retaining previously cached contribution data.")
                    return
            except Exception:
                pass
        raise SystemExit("Error: Unable to fetch contribution data from GitHub.")

    analytics = calculate_analytics(days)
    repos = fetch_public_repositories(USERNAME)

    result = {
        'username': USERNAME,
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'total_contributions': analytics['total_contributions'],
        'active_days': analytics['active_days'],
        'current_streak': analytics['current_streak'],
        'longest_streak': analytics['longest_streak'],
        'peak_day': analytics['peak_day'],
        'monthly': analytics['monthly'],
        'days': days,
        'repositories': repos
    }

    CONTRIB_FILE.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Successfully saved {len(days)} days ({analytics['total_contributions']} contributions, {analytics['active_days']} active days, {len(repos)} repos) to {CONTRIB_FILE}")


if __name__ == '__main__':
    main()
