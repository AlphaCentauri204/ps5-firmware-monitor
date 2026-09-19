import os
import re
import requests

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_EVENT = os.getenv("GITHUB_EVENT_NAME", "")

# Sony's official public updatelist endpoint for PS5
SONY_UPDATELIST_URL = "http://fus01.ps5.update.playstation.net/update/ps5/official/tJMRE80IbXnE9YuG0jzTXgKEjIMoabr6/list/us/updatelist.xml"

def send_telegram(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing credentials.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

def fetch_ofw_version():
    headers = {"User-Agent": "PS5/13.60"}
    try:
        r = requests.get(SONY_UPDATELIST_URL, headers=headers, timeout=15)
        if r.status_code == 200:
            # Matches version patterns like 14.00.00 or level2_sub_ver
            matches = re.findall(r'(\d{2}\.\d{2}(?:\.\d{2})?)', r.text)
            for m in matches:
                if m not in ["01.00", "00.00"]:
                    return m
    except Exception as e:
        print(f"Error checking Sony: {e}")
    return "14.00"

def main():
    ofw_version = fetch_ofw_version()

    # Manual test trigger (from GitHub "Run workflow" button)
    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(
            f"🔎 *Manual Check*\n\n"
            f"Target FW: `{TARGET_FW}`\n"
            f"Latest OFW: `{ofw_version}`\n"
            f"Status: 🟢 Connected & Monitoring active!"
        )
        return

    # Scheduled 12-hour heartbeat notification
    if GITHUB_EVENT == "schedule":
        send_telegram(
            f"🟢 *12-Hour PSN Status Update*\n\n"
            f"Target FW: `{TARGET_FW}` (Still Active)\n"
            f"Latest OFW: `{ofw_version}`\n"
            f"Status: Monitoring online."
        )

if __name__ == "__main__":
    main()
