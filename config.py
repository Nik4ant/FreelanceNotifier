import os
from dotenv import load_dotenv

# Loading secret vars from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Token for VK api
API_TOKEN = os.environ.get("API_TOKEN")
# Id of bot group
GROUP_ID = os.environ.get("GROUP_ID")
# Delay between parser checks for new orders
ORDERS_UPDATE_DELAY_SECONDS = 5
# Timeout for event check in bot_server.py (used to avoid blocking loop)
EVENT_CHECK_TIMEOUT = 1.5
