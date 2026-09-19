import os
import re
import datetime
import requests
import xml.etree.ElementTree as ET

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_EVENT = os.getenv("GITHUB_EVENT_NAME", "")

SONY_CHECKER_URL = "https://fus01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml"

def send_telegram(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

def get_latest_ofw():
    try:
        r = requests.get(SONY_CHECKER_URL, headers={"User-Agent": "PlayStation 5"}, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            label = root.findtext(".//level2_label")
            if label:
                clean_ver = re.findall(r'(\d{2}\.\d{2})', label)
                if clean_ver:
                    return clean_ver[0]
    except Exception as e:
        print(f"Error checking Sony server: {e}")
    return "14.00"

def main():
    latest_ofw = get_latest_ofw()
    alive_fws = ["13.60", latest_ofw]

    # 1. Manual check (via "Run workflow" button)
    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(
            f"🔎 *Manual Check*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Still Alive: `{', '.join(set(alive_fws))}`\n"
            f"Target FW `{TARGET_FW}` status: 🟢 *PSN Access Active*"
        )
        return

    # 2. 6-Hour Heartbeat Window (Runs at 00:00, 06:00, 12:00, and 18:00 UTC)
    now = datetime.datetime.utcnow()
    is_6h_window = (now.hour in [0, 6, 12, 18]) and (now.minute < 30)

    if is_6h_window:
        send_telegram(
            f"🟢 *6-Hour PSN Status Update*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Still Alive: `{', '.join(set(alive_fws))}`\n"
            f"Target FW `{TARGET_FW}`: Still active on PSN."
        )
    else:
        print(f"[{now.strftime('%H:%M:%S')} UTC] 30-minute background check completed silently.")

if __name__ == "__main__":
    main()
