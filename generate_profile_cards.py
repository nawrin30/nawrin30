
#!/usr/bin/env python3
"""Generate self-hosted GitHub profile cards using GitHub's API."""

import json
import os
import urllib.request
import urllib.error
from collections import Counter
from datetime import date
from html import escape

USERNAME = os.getenv("GH_USERNAME", "nawrin30")
TOKEN = os.getenv("GH_TOKEN")
OUT = "assets"

# Theme colors
BG = "#0d1117"
CARD = "#151323"
TEXT = "#e6edf3"
MUTED = "#9ff3ed"
ACCENT = "#ff3b91"
PURPLE = "#7136a2"
GREEN = "#3282ce"

QUERY = """
query($login: String!) {
  user(login: $login) {
    login name followers { totalCount } following { totalCount }
    repositories(
      first: 100,
      ownerAffiliations: OWNER,
      privacy: PUBLIC,
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def request_json(url, data=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "nawrin30-profile-cards",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if data is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code}: {detail}"
        ) from exc


def fetch_profile():
    if not TOKEN:
        raise RuntimeError(
            "GH_TOKEN is missing. Enable the GITHUB_TOKEN secret in Actions."
        )

    result = request_json(
        "https://api.github.com/graphql",
        json.dumps({
            "query": QUERY,
            "variables": {"login": USERNAME}
        }).encode()
    )

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"]))

    user = result.get("data", {}).get("user")

    if not user:
        raise RuntimeError(f"GitHub user @{USERNAME} was not found.")

    return user


def fetch_languages():
    repos = request_json(
        f"https://api.github.com/users/{USERNAME}/repos"
        "?per_page=100&sort=updated&type=owner"
    )

    totals = Counter()

    for repo in repos:
        if not repo.get("fork"):
            try:
                langs = request_json(repo["languages_url"])
                totals.update(langs)

            except Exception as exc:
                print(
                    f"Skipping languages for {repo.get('name')}: {exc}"
                )

    return totals


def svg_card(title, width=495, height=190):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        '<defs>'
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#ff3b91"/>'
        '<stop offset="1" stop-color="#7136a2"/>'
        '</linearGradient>'
        '</defs>',

        f'<rect x="1" y="1" width="{width-2}" '
        f'height="{height-2}" rx="16" fill="{CARD}"/>',

        f'<text x="28" y="48" fill="{ACCENT}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="27" font-weight="700">'
        f'{escape(title)}</text>',
    ]


def label_value(parts, x, y, label, value, color=TEXT, size=23):
    parts.append(
        f'<text x="{x}" y="{y}" fill="{MUTED}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="12">{escape(label)}</text>'
    )

    parts.append(
        f'<text x="{x}" y="{y+29}" fill="{color}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="{size}" font-weight="700">'
        f'{escape(str(value))}</text>'
    )


def write_svg(name, parts):
    parts.append("</svg>")

    os.makedirs(OUT, exist_ok=True)

    with open(
        os.path.join(OUT, name),
        "w",
        encoding="utf-8"
    ) as file:
        file.write("\n".join(parts))


def streak_values(days):
    counts = [d["contributionCount"] for d in days]

    current = 0

    # If today has no contribution yet,
    # a streak ending yesterday is still active.
    start = len(counts) - 1

    if (
        counts
        and counts[-1] == 0
        and date.fromisoformat(days[-1]["date"]) == date.today()
    ):
        start -= 1

    for index in range(start, -1, -1):
        if counts[index] > 0:
            current += 1
        else:
            break

    longest = run = 0

    for count in counts:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)

    return current, longest


def main():
    user = fetch_profile()

    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]

    days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]

    languages = fetch_languages()

    public_repos = user["repositories"]["totalCount"]

    stars = sum(
        repo["stargazerCount"]
        for repo in user["repositories"]["nodes"]
    )

    total = calendar["totalContributions"]

    # ==========================================
    # GITHUB STATISTICS DASHBOARD
    # ==========================================

    width, height = 1000, 300

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        f'<rect width="{width}" height="{height}" '
        f'rx="18" fill="{CARD}"/>',

        f'<text x="42" y="52" fill="{ACCENT}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="30" font-weight="700">'
        f'{escape(USERNAME)}&#39;s GitHub Stats</text>',

        '<line x1="520" y1="82" x2="520" y2="260" '
        'stroke="#454052" stroke-width="1.5"/>',
    ]

    stat_rows = [
        ("TOTAL STARS EARNED", stars, "#f4d94e"),
        (
            "TOTAL COMMITS",
            collection["totalCommitContributions"],
            "#ff3b91"
        ),
        (
            "TOTAL PULL REQUESTS",
            collection["totalPullRequestContributions"],
            "#f4d94e"
        ),
        (
            "TOTAL ISSUES",
            collection["totalIssueContributions"],
            "#9b59b6"
        ),
        ("PUBLIC REPOSITORIES", public_repos, "#3282ce"),
    ]

    for i, (label, value, color) in enumerate(stat_rows):
        y = 105 + i * 34

        p.append(
            f'<circle cx="52" cy="{y-5}" r="6" fill="{color}"/>'
        )

        p.append(
            f'<text x="72" y="{y}" fill="{MUTED}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="15" font-weight="600">'
            f'{escape(label)}:</text>'
        )

        p.append(
            f'<text x="390" y="{y}" fill="{TEXT}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="17" font-weight="700">'
            f'{escape(str(value))}</text>'
        )

    # Donut chart
    contribution_parts = [
        (
            "Commits",
            collection["totalCommitContributions"],
            "#ff3b91"
        ),
        (
            "Pull requests",
            collection["totalPullRequestContributions"],
            "#7136a2"
        ),
        (
            "Issues",
            collection["totalIssueContributions"],
            "#3282ce"
        ),
        (
            "Reviews",
            collection["totalPullRequestReviewContributions"],
            "#f4d94e"
        ),
    ]

    contribution_sum = sum(
        value for _, value, _ in contribution_parts
    )

    radius = 53
    circumference = 2 * 3.141592653589793 * radius
    offset = 0

    cx, cy = 445, 170

    p.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        f'fill="none" stroke="#30283d" stroke-width="13"/>'
    )

    if contribution_sum:
        for label, value, color in contribution_parts:
            if value <= 0:
                continue

            segment = circumference * value / contribution_sum

            p.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
                f'fill="none" stroke="{color}" stroke-width="13" '
                f'stroke-dasharray="{segment:.2f} '
                f'{circumference-segment:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" '
                f'transform="rotate(-90 {cx} {cy})"/>'
            )

            offset += segment

    p.append(
        f'<text x="{cx}" y="{cy+5}" text-anchor="middle" '
        f'fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="22" font-weight="700">{total:,}</text>'
    )

    p.append(
        f'<text x="{cx}" y="{cy+25}" text-anchor="middle" '
        f'fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="10">CONTRIBUTIONS</text>'
    )

    # Right side statistics
    current, longest = streak_values(days)

    right_stats = [
        ("TOTAL CONTRIBUTIONS", f"{total:,}", ACCENT),
        ("CURRENT STREAK", f"{current} days", "#f4d94e"),
        ("LONGEST STREAK", f"{longest} days", ACCENT),
    ]

    for i, (label, value, color) in enumerate(right_stats):
        x = 565 + i * 140

        p.append(
            f'<text x="{x+55}" y="130" text-anchor="middle" '
            f'fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="26" font-weight="700">'
            f'{escape(value)}</text>'
        )

        p.append(
            f'<text x="{x+55}" y="160" text-anchor="middle" '
            f'fill="{color}" font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="13" font-weight="600">'
            f'{escape(label)}</text>'
        )

        if i < 2:
            p.append(
                f'<line x1="{x+125}" y1="95" '
                f'x2="{x+125}" y2="205" stroke="#454052"/>'
            )

    p.append(
        f'<text x="565" y="245" fill="{MUTED}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="12">'
        f'Based on your GitHub contribution calendar (last 12 months)'
        f'</text>'
    )

    write_svg("github-stats.svg", p)

    # ==========================================
    # MOST USED LANGUAGES
    # ==========================================

    width, height = 580, 320

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        f'<rect width="{width}" height="{height}" '
        f'rx="16" fill="{CARD}"/>',

        f'<text x="48" y="68" fill="{ACCENT}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="34" font-weight="500">'
        f'Most Used Languages</text>',
    ]

    top = languages.most_common(5)

    total_bytes = sum(languages.values()) or 1

    colors = [
        "#f4df4e",
        "#3178c6",
        "#6f35a5",
        "#e34c26",
        "#3572a5"
    ]

    bar_x, bar_y = 48, 108
    bar_w, bar_h = 484, 15

    used = 0

    for idx, (lang, amount) in enumerate(top):
        segment_w = bar_w * amount / total_bytes

        if segment_w > 0:
            p.append(
                f'<rect x="{bar_x+used:.2f}" '
                f'y="{bar_y}" '
                f'width="{segment_w+0.5:.2f}" '
                f'height="{bar_h}" '
                f'fill="{colors[idx]}"/>'
            )

        used += segment_w

    if top:
        p.append(
            f'<rect x="{bar_x}" y="{bar_y}" '
            f'width="{bar_w}" height="{bar_h}" '
            f'rx="8" fill="none" stroke="{CARD}" stroke-width="1"/>'
        )

    for idx, (lang, amount) in enumerate(top):
        col = idx % 2
        row = idx // 2

        lx = 48 + col * 290
        ly = 168 + row * 48

        p.append(
            f'<circle cx="{lx+9}" cy="{ly-5}" '
            f'r="9" fill="{colors[idx]}"/>'
        )

        p.append(
            f'<text x="{lx+28}" y="{ly}" fill="{MUTED}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="19">'
            f'{escape(lang)} {amount/total_bytes*100:.2f}%'
            f'</text>'
        )

    if not top:
        p.append(
            f'<text x="48" y="165" fill="{MUTED}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="16">'
            f'No language data available yet.</text>'
        )

    write_svg("top-langs.svg", p)

    # ==========================================
    # GITHUB CONTRIBUTION STREAK
    # ==========================================

    current, longest = streak_values(days)

    p = svg_card("GitHub Contribution Streak")

    label_value(
        p, 55, 92,
        "CURRENT STREAK",
        f"{current} days",
        ACCENT, 27
    )

    label_value(
        p, 275, 92,
        "LONGEST STREAK",
        f"{longest} days",
        PURPLE, 27
    )

    p.append(
        f'<text x="55" y="157" fill="{MUTED}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="12">'
        f'Based on your GitHub contribution calendar (last 12 months).'
        f'</text>'
    )

    write_svg("github-streak.svg", p)

    # ==========================================
    # CONTRIBUTION ACTIVITY GRAPH
    # ==========================================

    p = svg_card(
        "Contribution Activity — Last 12 Months",
        width=1000,
        height=300
    )

    chart_days = days[-365:]

    left, top, plot_w, plot_h = 48, 65, 920, 175

    max_count = max(
        [d["contributionCount"] for d in chart_days] or [1]
    ) or 1

    points = []

    for i, day in enumerate(chart_days):
        x = left + (
            i / max(1, len(chart_days)-1)
        ) * plot_w

        y = top + plot_h - (
            day["contributionCount"] / max_count
        ) * plot_h

        points.append(f"{x:.1f},{y:.1f}")

    p.append(
        f'<line x1="{left}" y1="{top+plot_h}" '
        f'x2="{left+plot_w}" y2="{top+plot_h}" '
        f'stroke="#414868"/>'
    )

    if points:
        p.append(
            f'<polyline points="{" ".join(points)}" '
            f'fill="none" stroke="url(#g)" '
            f'stroke-width="2.5" '
            f'stroke-linejoin="round" '
            f'stroke-linecap="round"/>'
        )

    p.append(
        f'<text x="{left}" y="270" fill="{MUTED}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="11">'
        f'{escape(chart_days[0]["date"] if chart_days else "")}'
        f'</text>'
    )

    p.append(
        f'<text x="{left+plot_w}" y="270" '
        f'text-anchor="end" fill="{MUTED}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="11">'
        f'{escape(chart_days[-1]["date"] if chart_days else "")}'
        f'</text>'
    )

    write_svg("contributions.svg", p)

    print(f"Generated profile cards for @{USERNAME}.")


if __name__ == "__main__":
    main()
