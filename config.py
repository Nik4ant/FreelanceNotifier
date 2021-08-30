import os
from dotenv import load_dotenv

# Loading secret vars from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Token for VK api
API_TOKEN = os.environ.get("API_TOKEN")
# Id of bot group
GROUP_ID = os.environ.get("GROUP_ID")
# Delay between parser checks for new orders
ORDERS_UPDATE_DELAY_SECONDS = 5 * 60
# Timeout for event check in bot_server.py (used to avoid blocking loop)
EVENT_CHECK_TIMEOUT = 1.5
# Titles of last orders from each category (for determining new orders after server startup)
# Note(Nik4ant): This is important for avoiding a lot of messages from bot
# (P.s. tested it myself without this. Over 350 messages for less than 5 minutes)
ORDER_LAST_TITLES_STARTUP = {
    "scripts": "Реализовать парсер",
    "desktop": "Программа рассылки в Вайбер",
}
