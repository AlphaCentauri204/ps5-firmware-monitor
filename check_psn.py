import os
import requests

# Target firmware to verify
TARGET_FW = "13.60"

# Telegram credentials passed from GitHub Secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Replace this with the raw URL of the status source you are tracking
# (e.g. your community Discord/Twitter bot raw json endpoint, or status API)
STATUS_URL = os.getenv("PSN_DATA_URL", "https://raw.githubusercontent.com/example/psn-fw-tracker/main/status.json")

def send_telegram(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram configuration missing.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload, timeout=10)
    print(f"Telegram response: {res.status_code}")

def check():
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
        print(f"Failed to check firmware status: {e}")

if __name__ == "__main__":
    check()
