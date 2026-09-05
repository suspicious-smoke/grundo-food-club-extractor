import requests
import os
from pathlib import Path
import browser_cookie3
from bs4 import BeautifulSoup
from pathlib import Path
import re
import subprocess


URL = "https://grundos.cafe/games/foodclub/bet/"


# --------------------------------------------------
# Get logged-in Firefox cookies
# --------------------------------------------------
try:
    cookies = browser_cookie3.firefox()
except Exception as e:
    raise RuntimeError(
        "Could not read Firefox cookies.\n"
        "Try completely closing Firefox before running this script."
    ) from e


session = requests.Session()
session.cookies.update(cookies)


# --------------------------------------------------
# Download the Food Club page
# --------------------------------------------------
response = session.get(URL)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")


# --------------------------------------------------
# Find the current round
# --------------------------------------------------
page_text = soup.get_text(" ", strip=True)

match = re.search(
    r"It is currently\s+Round\s+(\d+)",
    page_text
)

if not match:
    raise RuntimeError(
        "Could not find the Food Club round.\n"
        "Make sure you are logged into Grundo's Cafe."
    )

round_number = int(match.group(1))


# --------------------------------------------------
# Find all five winner dropdowns
# --------------------------------------------------
pirates = []

for i in range(1, 6):

    select = soup.find(
        "select",
        {"name": f"winner{i}"}
    )

    if not select:
        raise RuntimeError(
            f"Could not find winner{i}."
        )

    for option in select.find_all("option"):

        value = option.get("value", "")
        text = option.get_text(" ", strip=True)

        # Skip the placeholder option
        if not value:
            continue

        # Find odds, e.g. (2:1)
        odds_match = re.search(
            r"\((\d+):1\)",
            text
        )

        if not odds_match:
            continue

        odds = odds_match.group(1)

        # Remove odds from the name
        name = re.sub(
            r"\s*\(\d+:1\)",
            "",
            text
        ).strip()

        pirates.append(
            f"{name} ({odds}:1)"
        )

lines = []

lines.append(f"Round   {round_number}")
lines.append("Pirate")

for pirate in pirates:
    name, odds = pirate.rsplit(" (", 1)
    odds = odds.rstrip(")")
    lines.append(f"{name}; {odds}")

output = "\n".join(lines)


# --------------------------------------------------
# Save as a text file
# --------------------------------------------------
filename = Path("bet_files") / f"food_club_round_{round_number}.txt"
filename.parent.mkdir(exist_ok=True)

with open(filename, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Saved: {filename}")
print()
print(output)
subprocess.Popen(["notepad.exe", str(filename.resolve())])