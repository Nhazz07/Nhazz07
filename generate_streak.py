import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# GitHub authentication
# ============================================================

TOKEN = os.environ["GH_PAT"]
USERNAME = os.environ["GITHUB_USERNAME"]


# ============================================================
# GitHub GraphQL query
# ============================================================

QUERY = """
query($userName: String!) {
  user(login: $userName) {
    contributionsCollection {
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


# ============================================================
# GitHub GraphQL request
# ============================================================

response = requests.post(
    "https://api.github.com/graphql",
    json={
        "query": QUERY,
        "variables": {
            "userName": USERNAME
        },
    },
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
    timeout=30,
)

response.raise_for_status()

data = response.json()


# ============================================================
# Check GraphQL errors
# ============================================================

if "errors" in data:
    raise RuntimeError(
        f"GitHub GraphQL error: {data['errors']}"
    )


user = data.get("data", {}).get("user")

if user is None:
    raise RuntimeError(
        f"GitHub user '{USERNAME}' was not found."
    )


calendar = user["contributionsCollection"]["contributionCalendar"]

weeks = calendar["weeks"]

total_contributions = calendar["totalContributions"]


# ============================================================
# Build contribution days
# ============================================================

days = []

for week in weeks:

    for day in week["contributionDays"]:

        days.append(
            {
                "date": datetime.strptime(
                    day["date"],
                    "%Y-%m-%d"
                ).date(),

                "count": day["contributionCount"],
            }
        )


days.sort(
    key=lambda x: x["date"]
)


# ============================================================
# Current date
# Cambodia timezone
# ============================================================

today = datetime.now(
    ZoneInfo("Asia/Phnom_Penh")
).date()


print("=" * 50)
print("GitHub Contribution Streak")
print("=" * 50)

print(f"User: {USERNAME}")
print(f"Today: {today}")
print(f"Total contributions: {total_contributions}")

print()


# ============================================================
# Debug recent contribution days
# ============================================================

print("Recent contribution days:")

debug_start = today - timedelta(days=14)

for day in days:

    if debug_start <= day["date"] <= today:

        print(
            f"{day['date']} -> "
            f"{day['count']} contributions"
        )


print()


# ============================================================
# Contribution dates
# ============================================================

contribution_dates = {
    day["date"]
    for day in days
    if day["count"] > 0
}


# ============================================================
# Current streak
# ============================================================

if today in contribution_dates:

    streak_end = today

elif (
    today - timedelta(days=1)
    in contribution_dates
):

    streak_end = today - timedelta(days=1)

else:

    streak_end = None


current_streak = 0


if streak_end is not None:

    check_date = streak_end

    while check_date in contribution_dates:

        current_streak += 1

        check_date -= timedelta(days=1)


# ============================================================
# Longest streak
# ============================================================

longest_streak = 0

running = 0

previous = None


for date in sorted(contribution_dates):

    if (
        previous is not None
        and date == previous + timedelta(days=1)
    ):

        running += 1

    else:

        running = 1

    longest_streak = max(
        longest_streak,
        running
    )

    previous = date


# ============================================================
# Current streak dates
# ============================================================

if current_streak > 0:

    streak_start = (
        streak_end
        - timedelta(
            days=current_streak - 1
        )
    )

    date_text = (
        f"{streak_start.strftime('%b %-d')} - "
        f"{streak_end.strftime('%b %-d')}"
    )

else:

    streak_start = None

    streak_end = None

    date_text = "No current streak"


# ============================================================
# Print final result
# ============================================================

print("=" * 50)

print(
    f"Current streak: "
    f"{current_streak}"
)

print(
    f"Longest streak: "
    f"{longest_streak}"
)

print(
    f"Streak period: "
    f"{date_text}"
)

print("=" * 50)


# ============================================================
# Create SVG
# ============================================================

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="700"
height="220"
viewBox="0 0 700 220">

<rect
    width="700"
    height="220"
    rx="16"
    fill="#0d1117"
/>

<text
    x="350"
    y="48"
    text-anchor="middle"
    font-family="Arial, sans-serif"
    font-size="25"
    font-weight="bold"
    fill="#ffffff">
    GitHub Contribution Streak
</text>

<text
    x="350"
    y="105"
    text-anchor="middle"
    font-family="Arial, sans-serif"
    font-size="42"
    font-weight="bold"
    fill="#58a6ff">
    {current_streak} days
</text>

<text
    x="350"
    y="135"
    text-anchor="middle"
    font-family="Arial, sans-serif"
    font-size="17"
    fill="#8b949e">
    {date_text}
</text>

<text
    x="350"
    y="175"
    text-anchor="middle"
    font-family="Arial, sans-serif"
    font-size="16"
    fill="#8b949e">
    Longest streak: {longest_streak} days
</text>

</svg>
"""


# ============================================================
# Write SVG
# ============================================================

Path("profile").mkdir(
    exist_ok=True
)

Path(
    "profile/streak.svg"
).write_text(
    svg,
    encoding="utf-8"
)


print()
print("SVG successfully generated.")
