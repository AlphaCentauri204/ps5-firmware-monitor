import os
import re
import datetime
import requests
import xml.etree.ElementTree as ET

# Set to "13.20" to test revocation alert, or "13.60" for real tracking
TARGET_FW = "13.20"

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
    
    # Firmwares that currently have PSN access
    alive_fws = ["13.60", latest_ofw]
    
    # Dynamic check: Is our target firmware actually alive?
    is_alive = TARGET_FW in alive_fws

    # 1. Manual Check (when you tap "Run workflow")
    if GITHUB_EVENT == "workflow_dispatch":
        if is_alive:
            status_text = "🟢 *PSN Access Active*"
        else:
            status_text = "🚨 *PSN Access REVOKED*"

        send_telegram(
            f"🔎 *Manual Check*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Still Alive: `{', '.join(set(alive_fws))}`\n"
            f"Target FW `{TARGET_FW}` status: {status_text}"
        )
        return

    # 2. Automated Scheduled Check
    # If access is revoked, trigger an emergency alert immediately
    if not is_alive:
        send_telegram(
            f"🚨 *CRITICAL ALERT: PSN ACCESS REVOKED* 🚨\n\n"
            f"Target FW *{TARGET_FW}* has been dropped from PSN!\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Active FW: `{', '.join(set(alive_fws))}`"
        )
        return

    # 3. Scheduled Heartbeat (5:00 AM, 11:00 AM, 5:00 PM, 11:00 PM IST)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
    target_ist_hours = [5, 11, 17, 23]

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

if __name__ == "__main__":
    main()
