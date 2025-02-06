import os
import requests
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Set the environment variables for the Telegram Bot API
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

def send_telegram_message(message: str):
    """
    Sends a message to the specified Telegram group using the Telegram Bot API.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": GROUP_CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print("Response:", response.text)

if __name__ == "__main__":
    test_message = "Hello!"
    send_telegram_message(test_message)
