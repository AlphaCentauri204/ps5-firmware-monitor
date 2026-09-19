import os
import requests

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Source URL where live PSN firmware access status is retrieved
STATUS_URL = os.getenv("PSN_DATA_URL", "")

def send_telegram(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram BOT_TOKEN or CHAT_ID is missing!")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Telegram response status: {res.status_code}, response: {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"Failed to post to Telegram: {e}")
        return False

def check():
    # If no custom URL is provided yet, run a test ping to verify your bot
    if not STATUS_URL or "example" in STATUS_URL:
        print("No live STATUS_URL configured. Sending test ping...")
        send_telegram(
            f"✅ *PSN Tracker Connected!*\n\n"
            f"Your bot is actively running.\n"
            f"Currently monitoring target firmware: `{TARGET_FW}`\n\n"
            f"_Reply with your source feed/channel link to activate live checking._"
        )
        return

    try:
        response = requests.get(STATUS_URL, timeout=15)
        response.raise_for_status()
        data = response.json()

        alive_list = [str(x).strip() for x in data.get("alive", [])]
        latest_fw = data.get("latest", "Unknown")

        if TARGET_FW not in alive_list:
            message = (
                f"🚨 *PSN ACCESS REVOKED* 🚨\n\n"
                f"Firmware *{TARGET_FW}* has been dropped from PSN!\n"
                f"Latest FW: `{latest_fw}`\n"
                f"Still alive FW: `{', '.join(alive_list)}`"
            )
            send_telegram(message)
            print(f"Alert dispatched: {TARGET_FW} is dropped.")
        else:
            print(f"Firmware {TARGET_FW} is still alive on PSN.")

    except Exception as e:
        print(f"Error checking status: {e}")

if __name__ == "__main__":
    check()
