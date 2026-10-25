files to acquire to run script:
- get credentials from IAM for service account accessing google sheet
- get webhook from discord server for the webhook

Schedule cron job:
- 5 4 * * * cd "/home/starbuck/source/grundo-script/grundo-food-club-extractor/" && ".venv/bin/python" "food_club_extractor.py" >> "/home/starbuck/source/grundo-script/food_club.log" 2>&1