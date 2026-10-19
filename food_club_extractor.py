import requests
from pathlib import Path
import browser_cookie3
from bs4 import BeautifulSoup
from pathlib import Path
import re
import gspread

URL = "https://grundos.cafe/games/foodclub/bet/"
WINNER_BASE_URL = "https://grundos.cafe/games/foodclub/previous_round/?id="


def duplicate_and_paste(spreadsheet, source_tab, new_tab, values, paste_cell="B1"):
    # Find the original tab
    source = spreadsheet.worksheet(source_tab)

    # Prevent duplicate tab names
    if new_tab in [ws.title for ws in spreadsheet.worksheets()]:
        raise ValueError(f"Tab '{new_tab}' already exists.")

    # Duplicate the original tab and rename it
    new_sheet = spreadsheet.duplicate_sheet(
        source_sheet_id=source.id,
        new_sheet_name=new_tab,
        insert_sheet_index=source.index+1
    )

    paste_values(spreadsheet, new_tab, values, paste_cell)
    paste_values(spreadsheet, new_tab, [[max_bet]], "Q26")
    
    return new_sheet


def paste_values(spreadsheet, source_tab, values, paste_cell="B1"):
    if not (source_tab in [ws.title for ws in spreadsheet.worksheets()]):
            raise ValueError(f"Tab '{source_tab}' doesn't exists.")
    source = spreadsheet.worksheet(source_tab)
    # Paste the values into the new tab
    if values:
        source.update(
            values=values,
            range_name=paste_cell,
            value_input_option="RAW"
        )
        


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

max_bet_match = re.search(
    r"You can only place up to\s+(\d+)",
    page_text
)

max_bet = int(max_bet_match.group(1)) if max_bet_match else None


if not match:
    raise RuntimeError(
        "Could not find the Food Club round.\n"
        "Make sure you are logged into Grundo's Cafe."
    )

round_number = int(match.group(1))


# --------------------------------------------------
# Find all five dropdowns
# --------------------------------------------------
pirates_list = []
pirates_list.append([f"Round {round_number}",""])
pirates_list.append(["Pirate","Odds"])

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

        pirates_list.append(
            [name,f"{odds}:1"]
        )
# --------------------------------------------------
# Download the previous round winners
# --------------------------------------------------
winners_list=[]
winner_round=round_number-1
for i in range(1, 6):
    response = session.get(f"{WINNER_BASE_URL}{i}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    winner_pirate = soup.select_one("#fc_table p.bold.nomargin").get_text(strip=True)
    winners_list.append([winner_pirate])

# --------------------------------------------------
# Google sheet stuff
# --------------------------------------------------
gc = gspread.service_account(
    filename="../credentials.json"
)

spreadsheet = gc.open("GC food club bets")

new_sheet = duplicate_and_paste(
    spreadsheet=spreadsheet,
    source_tab="blank",
    new_tab=f"{round_number}",
    values=pirates_list
)

# put winners in previous sheet
paste_values(spreadsheet=spreadsheet,source_tab=f"{round_number-1}",values=winners_list,paste_cell="P19")




# --------------------------------------------------
# send discord message to my server
# --------------------------------------------------
webhook_path = Path(__file__).resolve().parent / ".." / "bot_server_fc_webhook.txt"
WEBHOOK_URL = webhook_path.read_text().strip()

url = f"{spreadsheet.url}#gid={new_sheet.id}"
payload = {
    "content": f"Grundo's Food Club\n[Open Round {round_number} in Google Sheets]({url})"
}

# Send the POST request to Discord
response = requests.post(WEBHOOK_URL, json=payload)

# Discord webhooks return a 204 status code on success
if response.status_code == 204:
    print("Message sent successfully!")
else:
    print(f"Failed to send message. Status code: {response.status_code}")