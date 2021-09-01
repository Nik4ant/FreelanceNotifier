import os
from dotenv import load_dotenv

# Loading secret vars from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Token for VK api
API_TOKEN = os.environ.get("API_TOKEN")
# Id of bot group
GROUP_ID = os.environ.get("GROUP_ID")
# Delay between parser checks for new orders
ORDERS_UPDATE_DELAY_SECONDS = 300
# Timeout for event check in bot_server.py (used to avoid blocking loop)
EVENT_CHECK_TIMEOUT = 1.5
# Send order timeout (used to avoid blocking loop)
HANDLE_ORDER_TIMEOUT = 1.5
# Titles of last orders from each category (for determining new orders after server startup)
# This is important for avoiding a lot of messages from bot
# (P.s. tested it myself without this. Over 350 messages for less than 5 minutes)
ORDER_LAST_TITLES_STARTUP = {
    "scripts": "2 страницы A5 на А4 в Python",
    "desktop": "Есть код функций на postgresql, нужны подобные на php",
}
