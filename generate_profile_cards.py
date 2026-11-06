#!/usr/bin/env python3
"""Generate self-hosted GitHub profile cards using GitHub's API."""
import json
import os
import urllib.request
import urllib.error
from collections import Counter
from datetime import date, timedelta
from html import escape

USERNAME = os.getenv("GH_USERNAME", "nawrin30")
TOKEN = os.getenv("GH_TOKEN")
OUT = "assets"
BG = "#1a1b27"
CARD = "#24283b"
TEXT = "#c0caf5"
MUTED = "#a9b1d6"
ACCENT = "#7aa2f7"
PURPLE = "#bb9af7"
GREEN = "#9ece6a"

QUERY = """
query($login: String!) {

  user(login: $login) {
    login
    name
    location
    createdAt
    followers { totalCount }
    following { totalCount }

    repositories( first: 100, ownerAffiliations: OWNER, privacy: PUBLIC,
                  orderBy: {field: UPDATED_AT, direction: DESC}) {
      totalCount nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
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
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc

def fetch_profile():
    if not TOKEN:
        raise RuntimeError("GH_TOKEN is missing. Enable the GITHUB_TOKEN secret in Actions.")
    result = request_json(
        "https://api.github.com/graphql",
        json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    )
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"]))
    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user @{USERNAME} was not found.")
    return user

def fetch_languages():
    repos = request_json(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated&type=owner"
    )
    totals = Counter()
    for repo in repos:
        if not repo.get("fork"):
            try:
                langs = request_json(repo["languages_url"])
                totals.update(langs)
            except Exception as exc:
                print(f"Skipping languages for {repo.get('name')}: {exc}")
    return totals

def svg_card(title, width=495, height=190):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7aa2f7"/><stop offset="1" stop-color="#bb9af7"/></linearGradient></defs>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="12" fill="{BG}" stroke="#414868"/>',
        f'<text x="24" y="34" fill="{ACCENT}" font-family="Segoe UI,Arial,sans-serif" font-size="17" font-weight="700">{escape(title)}</text>',
    ]

def label_value(parts, x, y, label, value, color=TEXT, size=23):
    parts.append(f'<text x="{x}" y="{y}" fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" font-size="12">{escape(label)}</text>')
    parts.append(f'<text x="{x}" y="{y+29}" fill="{color}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="700">{escape(str(value))}</text>')

def write_svg(name, parts):
    parts.append("</svg>")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as file:
        file.write("\n".join(parts))

def streak_values(days):
    counts = [d["contributionCount"] for d in days]
    current = 0
    # If today has no contribution yet, a streak ending yesterday is still active.
    start = len(counts) - 1
    if counts and counts[-1] == 0 and date.fromisoformat(days[-1]["date"]) == date.today():
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
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    languages = fetch_languages()
    public_repos = user["repositories"]["totalCount"]
    stars = sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])
    total = calendar["totalContributions"]

    # Main statistics card
   
    # Main Statistics Card — Dark Purple Dashboard Design
    p = svg_card(f"{USERNAME}'s GitHub Stats", width=495, height=210)

    stat_items = [
        ("TOTAL CONTRIBUTIONS", f"{total:,}", "#ff3e8a"),
        ("PUBLIC REPOSITORIES", public_repos, "#7dcfff"),
        ("TOTAL STARS", stars, "#ffd43b"),
        ("COMMITS", collection["totalCommitContributions"], "#bb9af7"),
        ("PULL REQUESTS", collection["totalPullRequestContributions"], "#9ece6a"),
        ("ISSUES", collection["totalIssueContributions"], "#f7768e"),
    ]

    positions = [
        (90, 91), (247, 91), (405, 91),
        (90, 165), (247, 165), (405, 165)
    ]

    for (label, value, color), (cx, cy) in zip(stat_items, positions):
        p.append(
            f'<text x="{cx}" y="{cy-20}" text-anchor="middle" '
            f'fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="10" font-weight="600">{escape(label)}</text>'
        )

        p.append(
            f'<text x="{cx}" y="{cy+13}" text-anchor="middle" '
            f'fill="{color}" font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="27" font-weight="700">{escape(str(value))}</text>'
        )

    # Vertical separators
    for x in (168, 326):
        p.append(
            f'<line x1="{x}" y1="57" x2="{x}" y2="185" '
            f'stroke="#343044" stroke-width="1"/>'
        )

    # Horizontal separator
    p.append(
        '<line x1="20" y1="124" x2="475" y2="124" '
        'stroke="#343044" stroke-width="1"/>'
    )

    write_svg("github-stats.svg", p)

    # Top languages card
  
    # Top Languages Card — Dark Purple Dashboard Design
    p = svg_card("Most Used Languages", width=495, height=210)

    top = languages.most_common(5)
    total_bytes = sum(languages.values()) or 1

    colors = [
        "#ff3e8a",
        "#7dcfff",
        "#ffd43b",
        "#bb9af7",
        "#9ece6a"
    ]

    bar_x = 25
    bar_y = 57
    bar_w = 445
    bar_h = 12

    if top:

        # Language distribution bar background
        p.append(
            f'<rect x="{bar_x}" y="{bar_y}" '
            f'width="{bar_w}" height="{bar_h}" '
            f'rx="6" fill="#343044"/>'
        )

        # Multiple language color segments
        used = 0.0

        for idx, (lang, amount) in enumerate(top):
            segment_w = bar_w * amount / total_bytes

            if segment_w > 0:
                p.append(
                    f'<rect x="{bar_x+used:.2f}" y="{bar_y}" '
                    f'width="{segment_w:.2f}" height="{bar_h}" '
                    f'fill="{colors[idx]}"/>'
                )

                used += segment_w

        # Rounded border
        p.append(
            f'<rect x="{bar_x}" y="{bar_y}" '
            f'width="{bar_w}" height="{bar_h}" '
            f'rx="6" fill="none" stroke="#343044"/>'
        )

        # Individual language details
        for idx, (lang, amount) in enumerate(top):

            y = 91 + idx * 23
            pct = amount / total_bytes * 100

            # Language color indicator
            p.append(
                f'<circle cx="30" cy="{y-4}" r="4" '
                f'fill="{colors[idx]}"/>'
            )

            # Language name
            p.append(
                f'<text x="43" y="{y}" fill="{TEXT}" '
                f'font-family="Segoe UI,Arial,sans-serif" '
                f'font-size="12" font-weight="600">'
                f'{escape(lang)}</text>'
            )

            # Progress bar background
            p.append(
                f'<rect x="175" y="{y-9}" width="220" '
                f'height="6" rx="3" fill="#343044"/>'
            )

            # Progress bar value
            p.append(
                f'<rect x="175" y="{y-9}" '
                f'width="{220*pct/100:.2f}" '
                f'height="6" rx="3" fill="{colors[idx]}"/>'
            )

            # Percentage
            p.append(
                f'<text x="465" y="{y}" text-anchor="end" '
                f'fill="{colors[idx]}" '
                f'font-family="Segoe UI,Arial,sans-serif" '
                f'font-size="11" font-weight="700">'
                f'{pct:.1f}%</text>'
            )

    else:
        p.append(
            f'<text x="25" y="100" fill="{MUTED}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="13">No language data available yet.</text>'
        )

    write_svg("top-langs.svg", p)

    # Contribution streak card: calculated from GitHub's contribution calendar.
    
    # GitHub Streak Card - Three Column Design
    current, longest = streak_values(days)

    width, height = 1000, 220
    p = svg_card("GitHub Contribution Streak", width, height)

    # Column separators
    p.append('<line x1="333" y1="55" x2="333" y2="195" stroke="#414868" stroke-width="1.5"/>')
    p.append('<line x1="667" y1="55" x2="667" y2="195" stroke="#414868" stroke-width="1.5"/>')

    # Left: Total Contributions
    p.append(f'<text x="166" y="105" text-anchor="middle" fill="#ff3e8a" font-family="Arial" font-size="34" font-weight="700">{calendar["totalContributions"]:,}</text>')
    p.append('<text x="166" y="135" text-anchor="middle" fill="#ff3e8a" font-family="Arial" font-size="15">Total Contributions</text>')

    date_start = days[0]["date"] if days else ""
    date_end = days[-1]["date"] if days else ""

    p.append(f'<text x="166" y="165" text-anchor="middle" fill="#a9b1d6" font-family="Arial" font-size="12">{date_start} - {date_end}</text>')

    # Center: Current Streak Ring
    cx, cy, radius = 500, 112, 39
    circumference = 2 * 3.14159 * radius
    progress = current / max(longest, current, 1)
    offset = circumference * (1 - progress)

    p.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#49233e" stroke-width="6"/>')

    p.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
        f'stroke="#ff3e8a" stroke-width="6" '
        f'stroke-dasharray="{circumference:.2f}" '
        f'stroke-dashoffset="{offset:.2f}" '
        f'stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>'
    )

    p.append(f'<text x="{cx}" y="{cy+9}" text-anchor="middle" fill="#ffd43b" font-family="Arial" font-size="27" font-weight="700">{current}</text>')

    p.append('<text x="500" y="170" text-anchor="middle" fill="#ffd43b" font-family="Arial" font-size="15" font-weight="700">Current Streak</text>')
    p.append('<text x="500" y="192" text-anchor="middle" fill="#a9b1d6" font-family="Arial" font-size="12">Consecutive days</text>')

    # Right: Longest Streak
    p.append(f'<text x="834" y="105" text-anchor="middle" fill="#ff3e8a" font-family="Arial" font-size="34" font-weight="700">{longest}</text>')
    p.append('<text x="834" y="135" text-anchor="middle" fill="#ff3e8a" font-family="Arial" font-size="15">Longest Streak</text>')
    p.append('<text x="834" y="165" text-anchor="middle" fill="#a9b1d6" font-family="Arial" font-size="12">Best consecutive days</text>')

    write_svg("github-streak.svg", p)


    # Contribution graph (daily count over the last year)
   
    # Contribution graph — Profile Details Style
    display_name = user.get("name") or user["login"]
    location = user.get("location") or "Location not set"
    joined = date.fromisoformat(user["createdAt"][:10])
    joined_text = f"{joined.strftime('%B %Y')}"

    chart_days = days[-365:]
    total = calendar["totalContributions"]

    width, height = 1000, 300
    left, top = 665, 75
    plot_w, plot_h = 270, 175
    baseline = top + plot_h

    max_count = max(
        [d["contributionCount"] for d in chart_days] or [1]
    )
    max_count = max(max_count, 1)
    axis_max = ((max_count + 4) // 5) * 5
    axis_max = max(axis_max, 5)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="1000" height="300" rx="12" fill="#171426"/>',

        # Profile name
        f'<text x="40" y="48" fill="#ff4081" '
        f'font-family="Arial,sans-serif" font-size="29">'
        f'{escape(display_name)} ({escape(USERNAME)})</text>',

        # Contribution information
        f'<text x="40" y="115" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" font-size="19">'
        f'● {total:,} Contributions on GitHub</text>',

        f'<text x="40" y="165" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" font-size="19">'
        f'▣ {public_repos} Public Repos</text>',

        f'<text x="40" y="215" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" font-size="19">'
        f'◷ Joined GitHub {escape(joined_text)}</text>',

        f'<text x="40" y="265" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" font-size="17">'
        f'⌖ {escape(location[:42])}</text>',

        # Chart title
        '<text x="800" y="40" fill="#8be9fd" '
        'font-family="Arial,sans-serif" font-size="13" '
        'text-anchor="middle">contributions in the last year</text>',
    ]

    # Chart grid and Y-axis labels
    for value in range(0, axis_max + 1, max(1, axis_max // 4)):
        y = baseline - (value / axis_max) * plot_h

        p.append(
            f'<line x1="{left}" y1="{y:.1f}" '
            f'x2="{left + plot_w}" y2="{y:.1f}" '
            'stroke="#39334f" stroke-width="1"/>'
        )

        p.append(
            f'<text x="{left + plot_w + 12}" y="{y + 4:.1f}" '
            'fill="#8be9fd" font-size="12">'
            f'{value}</text>'
        )

    # Contribution graph points
    points = []

    for i, day in enumerate(chart_days):
        x = left + (i / max(1, len(chart_days) - 1)) * plot_w
        y = baseline - (
            day["contributionCount"] / axis_max
        ) * plot_h

        points.append((x, y))

    # Filled area graph
    if points:
        area = (
            f'M {points[0][0]:.1f},{baseline} '
            + ' '.join(
                f'L {x:.1f},{y:.1f}' for x, y in points
            )
            + f' L {points[-1][0]:.1f},{baseline} Z'
        )

        p.append(
            f'<path d="{area}" fill="#a879f7" '
            'stroke="none" opacity="0.95"/>'
        )

    # X-axis date labels
    if chart_days:
        for i in range(0, 7):
            index = round(i * (len(chart_days) - 1) / 6)
            x = left + (index / max(1, len(chart_days) - 1)) * plot_w

            month = date.fromisoformat(
                chart_days[index]["date"]
            ).strftime("%d/%m")

            p.append(
                f'<text x="{x:.1f}" y="{baseline + 24}" '
                'fill="#8be9fd" font-size="11" '
                'text-anchor="middle">'
                f'{month}</text>'
            )

    write_svg("contributions.svg", p)

    print(f"Generated profile cards for @{USERNAME}.")

if __name__ == "__main__":
    main()