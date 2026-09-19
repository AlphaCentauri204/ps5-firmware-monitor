import os
import requests
import xml.etree.ElementTree as ET

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_EVENT = os.getenv("GITHUB_EVENT_NAME", "")

SONY_XML_URL = "https://fus01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml"

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

def main():
    headers = {"User-Agent": "PlayStation 5"}
    label = "Unknown"
    
    try:
        r = requests.get(SONY_XML_URL, headers=headers, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        system_pup = root.find(".//system_pup")
        if system_pup is not None:
            label = system_pup.findtext("level2_label", default="Unknown").strip()
    except Exception as e:
        print(f"Error checking Sony server: {e}")

    # 1. Manual check trigger (when you press "Run workflow" in GitHub)
    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(
            f"🔎 *Manual Check*\n\n"
            f"Target FW: `{TARGET_FW}`\n"
            f"Latest OFW: `{label}`\n"
            f"Status: Monitoring active. Telegram connected!"
        )
        return

    # 2. 12-Hour Scheduled Heartbeat trigger
    if GITHUB_EVENT == "schedule":
        send_telegram(
            f"🟢 *12-Hour PSN Status Update*\n\n"
            f"Target FW `{TARGET_FW}` is still running.\n"
            f"Latest OFW: `{label}`\n"
            f"Server check passed."
        )

if __name__ == "__main__":
    main()
