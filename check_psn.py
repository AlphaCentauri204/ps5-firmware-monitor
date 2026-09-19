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
STATE_FILE = "last_notified_hour.txt"

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

    # 1. Manual check (instant reply whenever you click "Run workflow")
    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(
            f"🔎 *Manual Check*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Still Alive: `{', '.join(set(alive_fws))}`\n"
            f"Target FW `{TARGET_FW}` status: 🟢 *PSN Access Active*"
        )
        return

    # 2. Convert UTC to exact India Standard Time (IST = UTC + 5h 30m)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset

    # Target hours in IST: 5:00 AM, 11:00 AM, 5:00 PM (17), 11:00 PM (23)
    target_ist_hours = [5, 11, 17, 23]

    # Read the last hour we sent a notification for to prevent duplicate alerts
    last_notified = ""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                last_notified = f.read().strip()
        except Exception:
            pass

    current_hour_key = f"{now_ist.strftime('%Y-%m-%d')}_{now_ist.hour}"

    if now_ist.hour in target_ist_hours and last_notified != current_hour_key:
        send_telegram(
            f"🟢 *PSN Status Update ({now_ist.strftime('%I:%M %p IST')})*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Still Alive: `{', '.join(set(alive_fws))}`\n"
            f"Target FW `{TARGET_FW}`: Still active on PSN."
        )
        try:
            with open(STATE_FILE, "w") as f:
                f.write(current_hour_key)
        except Exception:
            pass
    else:
        print(f"[{now_ist.strftime('%I:%M:%S %p IST')}] Background check completed silently.")

if __name__ == "__main__":
    main()
