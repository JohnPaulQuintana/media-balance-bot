import os
from dotenv import load_dotenv
from scraper import collect_ads_balance
from utils.alert_bot import MediaBot
from datetime import datetime
import asyncio

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def main():
    print("🔄 Collecting ads balance...")

    # Collect data from scraper.py
    data = collect_ads_balance()

    # Send an alert using MediaBot
    media_bot = MediaBot(TOKEN, CHANNEL_ID)

    # Wrap the call inside asyncio.run
    asyncio.run(media_bot.send_alert(data))

    # Print collected data
    result = {
        "brand": "True",
        "platform": "True",
        "balance": True,
        "currency": "True",
        "id": True,
        "collected_at": ''
    }
    print("✅ Data collected and alert sent:", result)

# Run the main function
if __name__ == "__main__":
    main()
