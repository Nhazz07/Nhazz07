import os
import requests
from datetime import datetime, timedelta
from pathlib import Path

TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_USERNAME"]

QUERY = """
query($userName: String!) {
  user(login: $userName) {
    contributionsCollection {
      contributionCalendar {
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

response = requests.post(
    "https://api.github.com/graphql",
    json={
        "query": QUERY,
        "variables": {
            "userName": USERNAME
        }
    },
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)

response.raise_for_status()

data = response.json()

if "errors" in data:
    raise RuntimeError(data["errors"])

weeks = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]["weeks"]

days = []

for week in weeks:
    for day in week["contributionDays"]:
        days.append({
            "date": datetime.strptime(
                day["date"], "%Y-%m-%d"
            ).date(),
            "count": day["contributionCount"]
        })

days.sort(key=lambda x: x["date"])

# Only days with at least one contribution count.
contribution_dates = {
    day["date"]
    for day in days
    if day["count"] > 0
}

today = datetime.utcnow().date()

current_streak = 0
check_date = today

while check_date in contribution_dates:
    current_streak += 1
    check_date -= timedelta(days=1)

# Longest streak
longest_streak = 0
running = 0
previous = None

for date in sorted(contribution_dates):
    if previous and date == previous + timedelta(days=1):
        running += 1
    else:
        running = 1

    longest_streak = max(longest_streak, running)
    previous = date

# Current streak start
if current_streak > 0:
    streak_start = today - timedelta(days=current_streak - 1)
    streak_end = today
else:
    streak_start = None
    streak_end = None

if streak_start:
    date_text = (
        f"{streak_start.strftime('%b %-d')} - "
        f"{streak_end.strftime('%b %-d')}"
    )
else:
    date_text = "No current streak"

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="700"
height="220"
viewBox="0 0 700 220">

<rect width="700" height="220"
rx="16"
fill="#0d1117"/>

<text x="350"
y="48"
text-anchor="middle"
font-family="Arial, sans-serif"
font-size="25"
font-weight="bold"
fill="#ffffff">
GitHub Contribution Streak
</text>

<text x="350"
y="105"
text-anchor="middle"
font-family="Arial, sans-serif"
font-size="42"
font-weight="bold"
fill="#58a6ff">
{current_streak} days
</text>

<text x="350"
y="135"
text-anchor="middle"
font-family="Arial, sans-serif"
font-size="17"
fill="#8b949e">
{date_text}
</text>

<text x="350"
y="175"
text-anchor="middle"
font-family="Arial, sans-serif"
font-size="16"
fill="#8b949e">
Longest streak: {longest_streak} days
</text>

</svg>
"""

Path("profile").mkdir(exist_ok=True)

Path("profile/streak.svg").write_text(
    svg,
    encoding="utf-8"
)

print(f"Current streak: {current_streak}")
print(f"Longest streak: {longest_streak}")
