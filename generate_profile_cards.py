
#!/usr/bin/env python3
"""Generate animated GitHub profile statistics cards."""

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

    repositories(
      first: 100,
      ownerAffiliations: OWNER,
      privacy: PUBLIC,
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      totalCount
      nodes {
        stargazerCount
      }
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


# -------------------- API REQUEST --------------------

def request_json(url, data=None):

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "nawrin30-profile-cards",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if data is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:

        detail = exc.read().decode("utf-8", errors="replace")

        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code}: {detail}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc


# -------------------- FETCH PROFILE --------------------

def fetch_profile():

    if not TOKEN:
        raise RuntimeError(
            "GH_TOKEN is missing. Add GITHUB_TOKEN secret in Actions."
        )

    result = request_json(
        "https://api.github.com/graphql",
        json.dumps({
            "query": QUERY,
            "variables": {"login": USERNAME}
        }).encode("utf-8")
    )

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"]))

    user = result.get("data", {}).get("user")

    if not user:
        raise RuntimeError(
            f"GitHub user @{USERNAME} was not found."
        )

    return user


# -------------------- FETCH ALL PUBLIC REPOSITORIES --------------------

def fetch_repositories():

    repos = []
    page = 1

    while True:

        batch = request_json(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=owner"
        )

        if not batch:
            break

        repos.extend(
            repo for repo in batch
            if not repo.get("private", True)
        )

        page += 1

    return repos


# -------------------- TOP LANGUAGES BY REPOSITORY --------------------

def fetch_languages(repos=None):
    """Calculate language usage from all public repositories."""

    if repos is None:
        repos = fetch_repositories()

    totals = Counter()

    for repo in repos:

        try:
            langs = request_json(repo["languages_url"])
            totals.update(langs)

        except Exception as exc:
            print(
                f"Skipping languages for {repo['name']}: {exc}"
            )

    return totals


# -------------------- ALL-TIME COMMIT LANGUAGES --------------------

def fetch_commit_languages(repos=None):
    """
    Calculate language usage from all public commit file changes.

    This measures changed lines (additions + deletions),
    not the number of commits.
    """

    if repos is None:
        repos = fetch_repositories()

    totals = Counter()

    extension_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".c": "C",
        ".h": "C",
        ".hpp": "C++",
        ".cs": "C#",
        ".php": "PHP",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".dart": "Dart",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bat": "Batchfile",
        ".json": "JSON",
        ".xml": "XML",
        ".yml": "YAML",
        ".yaml": "YAML",
        ".md": "Markdown",
        ".vue": "Vue",
        ".ipynb": "Jupyter Notebook",
    }

    for repo in repos:

        repo_name = repo["name"]

        print(f"Analyzing commits: {repo_name}")

        page = 1

        while True:

            commits = request_json(
                f"https://api.github.com/repos/{USERNAME}/"
                f"{repo_name}/commits?per_page=100&page={page}"
            )

            if not commits:
                break

            for commit in commits:

                try:

                    details = request_json(
                        f"https://api.github.com/repos/{USERNAME}/"
                        f"{repo_name}/commits/{commit['sha']}"
                    )

                    for file in details.get("files", []):

                        filename = file.get("filename", "")

                        extension = os.path.splitext(
                            filename
                        )[1].lower()

                        language = extension_map.get(extension)

                        if language:
                            totals[language] += (
                                file.get("additions", 0)
                                + file.get("deletions", 0)
                            )

                except Exception as exc:

                    print(
                        f"Skipping commit {commit['sha'][:7]} "
                        f"in {repo_name}: {exc}"
                    )

            page += 1

    return totals


# -------------------- SVG CARD --------------------

def svg_card(title, width=495, height=190):

    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        '<defs>'
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#7aa2f7"/>'
        '<stop offset="1" stop-color="#bb9af7"/>'
        '</linearGradient>'
        '</defs>',

        f'<rect x="1" y="1" width="{width-2}" '
        f'height="{height-2}" rx="12" fill="{BG}" '
        f'stroke="#414868"/>',

        f'<text x="24" y="34" fill="{ACCENT}" '
        f'font-family="Segoe UI,Arial,sans-serif" '
        f'font-size="17" font-weight="700">'
        f'{escape(title)}</text>',
    ]


def label_value(parts, x, y, label, value,
                color=TEXT, size=23):

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


# -------------------- ANIMATED CIRCULAR LANGUAGE CARD --------------------

def circular_language_card(
    title,
    language_data,
    filename,
    center_label,
    center_value,
    width=495,
    height=270
):
    """Generate an animated neon circular language statistics card."""

    colors = [
        "#38bdf8",
        "#a855f7",
        "#f59e0b",
        "#22c55e",
        "#ec4899",
        "#818cf8",
    ]

    total = sum(language_data.values())

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        """
        <defs>

          <linearGradient id="border" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#a855f7"/>
            <stop offset="50%" stop-color="#3b82f6"/>
            <stop offset="100%" stop-color="#22c55e"/>
          </linearGradient>

          <radialGradient id="background">
            <stop offset="0%" stop-color="#10172e"/>
            <stop offset="100%" stop-color="#080d20"/>
          </radialGradient>

          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge>
              <feMergeNode in="blur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>

          <style>

            @keyframes pulse {
              0%, 100% { opacity: .35; }
              50% { opacity: .9; }
            }

            @keyframes appear {
              from {
                opacity: 0;
                stroke-dashoffset: 500;
              }
              to {
                opacity: 1;
              }
            }

            .card {
              transition: filter .3s ease;
            }

            .card:hover {
              filter: brightness(1.2);
            }

            .donut-segment {
              animation: appear 1.8s ease both;
              filter: url(#glow);
              transition: opacity .3s ease;
            }

            .donut-segment:hover {
              opacity: .7;
            }

            .outer-glow {
              animation: pulse 3s ease-in-out infinite;
            }

            .legend {
              font-family: Segoe UI, Arial, sans-serif;
            }

          </style>

        </defs>
        """,

        f'<rect class="card" x="1" y="1" '
        f'width="{width-2}" height="{height-2}" '
        f'rx="22" fill="url(#background)" '
        f'stroke="url(#border)" stroke-width="1.5"/>',

        f'<text x="25" y="36" fill="#e0e7ff" '
        f'font-family="Segoe UI,Arial" '
        f'font-size="18" font-weight="700">'
        f'{escape(title)}</text>',

        '<line x1="25" y1="52" x2="470" y2="52" '
        'stroke="#293657" stroke-width="1"/>',
    ]

    if not total:

        p.append(
            '<text x="247" y="145" text-anchor="middle" '
            'fill="#a9b1d6" font-size="14">'
            'No language data available.</text>'
        )

        write_svg(filename, p)
        return

    # Top five languages and remaining languages.
    top = language_data.most_common(5)

    others = total - sum(
        amount for _, amount in top
    )

    if others > 0:
        top.append(("Others", others))

    chart_total = sum(
        amount for _, amount in top
    )

    # Donut chart settings.
    cx, cy = 125, 158
    radius = 73

    circumference = 2 * 3.141592653589793 * radius

    # Outer animated glow.
    p.append(
        f'<circle class="outer-glow" cx="{cx}" cy="{cy}" '
        f'r="{radius+13}" fill="none" '
        f'stroke="#7c3aed" stroke-width="2"/>'
    )

    # Donut background.
    p.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        f'fill="none" stroke="#29334f" stroke-width="17"/>'
    )

    # Donut segments.
    gap = 3
    available = circumference - gap * len(top)
    offset = 0

    for idx, (lang, amount) in enumerate(top):

        segment = available * amount / chart_total

        color = colors[idx % len(colors)]

        p.append(
            f'<circle class="donut-segment" '
            f'cx="{cx}" cy="{cy}" r="{radius}" '
            f'fill="none" stroke="{color}" '
            f'stroke-width="17" '
            f'stroke-dasharray="{segment:.2f} '
            f'{circumference-segment:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 {cx} {cy})" '
            f'stroke-linecap="round" '
            f'style="animation-delay:{idx * 0.15}s"/>'
        )

        offset += segment + gap

    # Center value.
    center_display = f"{center_value:,}"

    p.append(
        f'<text x="{cx}" y="{cy-4}" '
        f'text-anchor="middle" fill="#ffffff" '
        f'font-family="Segoe UI,Arial" '
        f'font-size="22" font-weight="700">'
        f'{escape(center_display)}</text>'
    )

    p.append(
        f'<text x="{cx}" y="{cy+17}" '
        f'text-anchor="middle" fill="#a5b4fc" '
        f'font-family="Segoe UI,Arial" '
        f'font-size="11">{escape(center_label)}</text>'
    )

    # Language legend.
    legend_x = 235
    legend_y = 91
    row_gap = 30

    for idx, (lang, amount) in enumerate(top):

        y = legend_y + idx * row_gap

        pct = amount / chart_total * 100

        color = colors[idx % len(colors)]

        p.append(
            f'<circle cx="{legend_x}" cy="{y-4}" '
            f'r="5" fill="{color}"/>'
        )

        p.append(
            f'<text class="legend" x="{legend_x+15}" '
            f'y="{y}" fill="#e0e7ff" '
            f'font-size="13">{escape(lang)}</text>'
        )

        p.append(
            f'<text class="legend" x="465" y="{y}" '
            f'text-anchor="end" fill="{color}" '
            f'font-size="13" font-weight="700">'
            f'{pct:.1f}%</text>'
        )

    write_svg(filename, p)


# -------------------- STREAK CALCULATION --------------------

def streak_values(days):

    counts = [
        d["contributionCount"]
        for d in days
    ]

    current = 0

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

    longest = 0
    run = 0

    for count in counts:

        run = run + 1 if count > 0 else 0

        longest = max(longest, run)

    return current, longest


# -------------------- MAIN FUNCTION --------------------

def main():

    print(f"Fetching GitHub profile for @{USERNAME}...")

    user = fetch_profile()

    collection = user["contributionsCollection"]

    calendar = collection["contributionCalendar"]

    days = [
        day
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]

    repos = fetch_repositories()

    languages = fetch_languages(repos)

    commit_languages = fetch_commit_languages(repos)

    public_repos = len(repos)

    stars = sum(
        repo.get("stargazers_count", 0)
        for repo in repos
    )

    total = calendar["totalContributions"]

    # -------------------- MAIN STATISTICS CARD --------------------

    p = svg_card(
        f"{USERNAME}'s GitHub Stats",
        width=495,
        height=210
    )

    stat_items = [
        ("TOTAL CONTRIBUTIONS", f"{total:,}", "#ff3e8a"),
        ("PUBLIC REPOSITORIES", public_repos, "#7dcfff"),
        ("TOTAL STARS", stars, "#ffd43b"),
        ("COMMITS", collection["totalCommitContributions"], "#bb9af7"),
        ("PULL REQUESTS", collection["totalPullRequestContributions"], "#9ece6a"),
        ("ISSUES", collection["totalIssueContributions"], "#f7768e"),
    ]

    positions = [
        (90, 91),
        (247, 91),
        (405, 91),
        (90, 165),
        (247, 165),
        (405, 165)
    ]

    for (label, value, color), (cx, cy) in zip(
        stat_items,
        positions
    ):

        p.append(
            f'<text x="{cx}" y="{cy-20}" '
            f'text-anchor="middle" fill="{MUTED}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="10" font-weight="600">'
            f'{escape(label)}</text>'
        )

        p.append(
            f'<text x="{cx}" y="{cy+13}" '
            f'text-anchor="middle" fill="{color}" '
            f'font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="27" font-weight="700">'
            f'{escape(str(value))}</text>'
        )

    for x in (168, 326):

        p.append(
            f'<line x1="{x}" y1="57" x2="{x}" y2="185" '
            f'stroke="#343044" stroke-width="1"/>'
        )

    p.append(
        '<line x1="20" y1="124" x2="475" y2="124" '
        'stroke="#343044" stroke-width="1"/>'
    )

    write_svg("github-stats.svg", p)

    # -------------------- CIRCULAR LANGUAGE CARDS --------------------

    circular_language_card(
        title="Top Language by Repository",
        language_data=languages,
        filename="top-langs.svg",
        center_label="Repositories",
        center_value=public_repos
    )

    circular_language_card(
        title="Top Language by Commit",
        language_data=commit_languages,
        filename="top-langs-commits.svg",
        center_label="Changed Lines",
        center_value=sum(commit_languages.values())
    )

    # -------------------- CONTRIBUTION STREAK CARD --------------------

    current, longest = streak_values(days)

    width, height = 1000, 220

    p = svg_card(
        "GitHub Contribution Streak",
        width,
        height
    )

    p.append(
        '<line x1="333" y1="55" x2="333" y2="195" '
        'stroke="#414868" stroke-width="1.5"/>'
    )

    p.append(
        '<line x1="667" y1="55" x2="667" y2="195" '
        'stroke="#414868" stroke-width="1.5"/>'
    )

    p.append(
        f'<text x="166" y="105" text-anchor="middle" '
        f'fill="#ff3e8a" font-family="Arial" '
        f'font-size="34" font-weight="700">'
        f'{calendar["totalContributions"]:,}</text>'
    )

    p.append(
        '<text x="166" y="135" text-anchor="middle" '
        'fill="#ff3e8a" font-family="Arial" '
        'font-size="15">Total Contributions</text>'
    )

    date_start = days[0]["date"] if days else ""
    date_end = days[-1]["date"] if days else ""

    p.append(
        f'<text x="166" y="165" text-anchor="middle" '
        f'fill="#a9b1d6" font-family="Arial" '
        f'font-size="12">{date_start} - {date_end}</text>'
    )

    cx, cy, radius = 500, 112, 39

    circumference = 2 * 3.14159 * radius

    progress = current / max(longest, current, 1)

    offset = circumference * (1 - progress)

    p.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        f'fill="none" stroke="#49233e" stroke-width="6"/>'
    )

    p.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        f'fill="none" stroke="#ff3e8a" stroke-width="6" '
        f'stroke-dasharray="{circumference:.2f}" '
        f'stroke-dashoffset="{offset:.2f}" '
        f'stroke-linecap="round" '
        f'transform="rotate(-90 {cx} {cy})"/>'
    )

    p.append(
        f'<text x="{cx}" y="{cy+9}" text-anchor="middle" '
        f'fill="#ffd43b" font-family="Arial" '
        f'font-size="27" font-weight="700">'
        f'{current}</text>'
    )

    p.append(
        '<text x="500" y="170" text-anchor="middle" '
        'fill="#ffd43b" font-family="Arial" '
        'font-size="15" font-weight="700">'
        'Current Streak</text>'
    )

    p.append(
        '<text x="500" y="192" text-anchor="middle" '
        'fill="#a9b1d6" font-family="Arial" '
        'font-size="12">Consecutive days</text>'
    )

    p.append(
        f'<text x="834" y="105" text-anchor="middle" '
        f'fill="#ff3e8a" font-family="Arial" '
        f'font-size="34" font-weight="700">'
        f'{longest}</text>'
    )

    p.append(
        '<text x="834" y="135" text-anchor="middle" '
        'fill="#ff3e8a" font-family="Arial" '
        'font-size="15">Longest Streak</text>'
    )

    p.append(
        '<text x="834" y="165" text-anchor="middle" '
        'fill="#a9b1d6" font-family="Arial" '
        'font-size="12">Best consecutive days</text>'
    )

    write_svg("github-streak.svg", p)

    # -------------------- CONTRIBUTION GRAPH --------------------

    display_name = user.get("name") or user["login"]

    location = user.get("location") or "Location not set"

    joined = date.fromisoformat(
        user["createdAt"][:10]
    )

    joined_text = joined.strftime("%B %Y")

    chart_days = days[-365:]

    total = calendar["totalContributions"]

    width, height = 1000, 300

    left, top, plot_w, plot_h = 665, 75, 270, 175

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

        '<rect width="1000" height="300" '
        'rx="12" fill="#171426"/>',

        f'<text x="40" y="48" fill="#ff4081" '
        f'font-family="Arial,sans-serif" '
        f'font-size="29">'
        f'{escape(display_name)} ({escape(USERNAME)})</text>',

        f'<text x="40" y="115" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" '
        f'font-size="19">'
        f'● {total:,} Contributions on GitHub</text>',

        f'<text x="40" y="165" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" '
        f'font-size="19">'
        f'▣ {public_repos} Public Repos</text>',

        f'<text x="40" y="215" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" '
        f'font-size="19">'
        f'◷ Joined GitHub {escape(joined_text)}</text>',

        f'<text x="40" y="265" fill="#8be9fd" '
        f'font-family="Arial,sans-serif" '
        f'font-size="17">'
        f'⌖ {escape(location[:42])}</text>',

        '<text x="800" y="40" fill="#8be9fd" '
        'font-family="Arial,sans-serif" '
        'font-size="13" text-anchor="middle">'
        'contributions in the last year</text>',
    ]

    # Y-axis and grid.

    step = max(1, axis_max // 4)

    for value in range(0, axis_max + 1, step):

        y = baseline - (value / axis_max) * plot_h

        p.append(
            f'<line x1="{left}" y1="{y:.1f}" '
            f'x2="{left + plot_w}" y2="{y:.1f}" '
            'stroke="#39334f" stroke-width="1"/>'
        )

        p.append(
            f'<text x="{left + plot_w + 12}" '
            f'y="{y + 4:.1f}" fill="#8be9fd" '
            f'font-size="12">{value}</text>'
        )

    # Contribution graph points.

    points = []

    for i, day in enumerate(chart_days):

        x = (
            left
            + (i / max(1, len(chart_days) - 1)) * plot_w
        )

        y = (
            baseline
            - (day["contributionCount"] / axis_max) * plot_h
        )

        points.append((x, y))

    # Filled area graph.

    if points:

        area = (
            f'M {points[0][0]:.1f},{baseline} '
            + ' '.join(
                f'L {x:.1f},{y:.1f}'
                for x, y in points
            )
            + f' L {points[-1][0]:.1f},{baseline} Z'
        )

        p.append(
            f'<path d="{area}" fill="#a879f7" '
            'stroke="none" opacity="0.95"/>'
        )

    # X-axis date labels.

    if chart_days:

        for i in range(7):

            index = round(
                i * (len(chart_days) - 1) / 6
            )

            x = (
                left
                + (
                    index / max(1, len(chart_days) - 1)
                ) * plot_w
            )

            month = date.fromisoformat(
                chart_days[index]["date"]
            ).strftime("%d/%m")

            p.append(
                f'<text x="{x:.1f}" '
                f'y="{baseline + 24}" '
                f'fill="#8be9fd" font-size="11" '
                f'text-anchor="middle">'
                f'{month}</text>'
            )

    write_svg("contributions.svg", p)

    # -------------------- FINISHED --------------------

    print(f"\nGenerated profile cards for @{USERNAME}.")

    print(f"Public repositories: {public_repos}")
    print(f"Total stars: {stars}")
    print(f"Current streak: {current} days")
    print(f"Longest streak: {longest} days")

    print("\nTop repository languages:")

    for lang, amount in languages.most_common(5):
        print(f"{lang}: {amount:,}")

    print("\nTop commit-change languages:")

    for lang, amount in commit_languages.most_common(5):
        print(f"{lang}: {amount:,}")

    print("\nAll SVG cards generated successfully!")


# -------------------- RUN SCRIPT --------------------

if __name__ == "__main__":

    try:
        main()

    except Exception as exc:

        print(f"\nERROR: {exc}")

        raise
