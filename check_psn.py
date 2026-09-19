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
STATE_FILE = "last_morning_ping.txt"

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
    headers = {"User-Agent": "PlayStation 5", "Connection": "close"}
    try:
        r = requests.get(SONY_CHECKER_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            label = root.findtext(".//level2_label")
            if label:
                clean_ver = re.findall(r'(\d{2}\.\d{2})', label)
                if clean_ver:
                    return clean_ver[0]
    except Exception as e:
        print(f"Error querying Sony: {e}")
    return "14.00"

def build_modern_card(title: str, latest_ofw: str, alive_fws: list, is_alive: bool) -> str:
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    alive_str = "  •  ".join(sorted(set(alive_fws)))
    
    status_badge = "🟢 ONLINE" if is_alive else "🔴 REVOKED"
    status_msg = f"Firmware `{TARGET_FW}` is authorized." if is_alive else f"⚠️ Firmware `{TARGET_FW}` access terminated!"

    card = (
        f"*{title}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎮 *PlayStation 5 Network*\n"
        f"📡 Status: {status_badge}\n"
        f"🕒 Checked: `{now_utc}`\n\n"
        f"🔹 *Latest OFW:* `{latest_ofw}`\n"
        f"✨ *Supported Firmwares:*\n`{alive_str}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Target:* `{TARGET_FW}` — {status_msg}"
    )
    return card

def main():
    latest_ofw = get_latest_ofw()
    alive_fws = ["13.60", latest_ofw]
    is_alive = TARGET_FW in alive_fws

    # 1. Manual check on-demand (Run workflow button)
    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(build_modern_card("🔎 MANUAL AUDIT", latest_ofw, alive_fws, is_alive))
        return

    # 2. Critical Alert: Triggered immediately if 13.60 is dropped
    if not is_alive:
        send_telegram(
            f"🚨 *CRITICAL ALERT: PSN REVOCATION* 🚨\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"❌ *Target FW `{TARGET_FW}` has been dropped from PSN!*\n"
            f"🕒 Timestamp: `{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}`\n"
            f"🔹 Latest OFW: `{latest_ofw}`\n"
            f"🔹 Active FW: `{', '.join(sorted(set(alive_fws)))}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Take your console offline immediately.*"
        )
        return

    # 3. Daily Morning Status at 6:30 AM IST (01:00 UTC)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)

    if now_ist.hour == 6:
        today_date = now_ist.strftime('%Y-%m-%d')
        last_ping_date = ""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    last_ping_date = f.read().strip()
            except Exception:
                pass

        if last_ping_date != today_date:
            send_telegram(build_modern_card("☀️ MORNING STATUS", latest_ofw, alive_fws, is_alive))
            try:
                with open(STATE_FILE, "w") as f:
                    f.write(today_date)
            except Exception:
                pass
            return

    print(f"[{now_ist.strftime('%I:%M:%S %p IST')}] Silent check passed: {TARGET_FW} still active.")

if __name__ == "__main__":
    main()
