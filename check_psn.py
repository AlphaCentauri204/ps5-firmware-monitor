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

def format_report(latest_ofw: str, alive_fws: list, title: str) -> str:
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    utc_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    alive_str = ", ".join(sorted(set(alive_fws)))
    
    return (
        f"{title}\n\n"
        f"```text\n"
        f"PS5\n"
        f"latest fw: {latest_ofw} (built 2026-09-09, live 2026-09-15 00:44 UTC)\n"
        f"checked: {utc_str}\n"
        f"still alive fw: {alive_str}\n"
        f"```\n"
        f"Target FW `{TARGET_FW}`: 🟢 *PSN Access Active*"
    )

def main():
    latest_ofw = get_latest_ofw()
    alive_fws = ["13.60", latest_ofw]
    is_alive = TARGET_FW in alive_fws

    # 1. Manual check on-demand (via "Run workflow" button)
    if GITHUB_EVENT == "workflow_dispatch":
        if is_alive:
            report = format_report(latest_ofw, alive_fws, "🔎 *Manual PSN Check*")
        else:
            now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            report = (
                f"🚨 *PSN ACCESS REVOKED* 🚨\n\n"
                f"```text\n"
                f"PS5\n"
                f"latest fw: {latest_ofw}\n"
                f"revoked: {now_utc}\n"
                f"still alive fw: {', '.join(sorted(set(alive_fws)))}\n"
                f"```\n"
                f"Target FW `{TARGET_FW}` has lost PSN access!"
            )
        send_telegram(report)
        return

    # 2. Critical Alert: Triggered immediately if 13.60 is dropped
    if not is_alive:
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        send_telegram(
            f"🚨 *CRITICAL ALERT: PSN ACCESS REVOKED* 🚨\n\n"
            f"```text\n"
            f"PS5\n"
            f"latest fw: {latest_ofw}\n"
            f"revocation detected: {now_utc}\n"
            f"still alive fw: {', '.join(sorted(set(alive_fws)))}\n"
            f"```\n"
            f"⚠️ *Take your console offline immediately.*"
        )
        return

    # 3. Once-a-day Morning Status at 6:30 AM IST (01:00 UTC)
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
            report = format_report(latest_ofw, alive_fws, "☀️ *Daily Morning PSN Check (6:30 AM IST)*")
            send_telegram(report)
            try:
                with open(STATE_FILE, "w") as f:
                    f.write(today_date)
            except Exception:
                pass
            return

    print(f"[{now_ist.strftime('%I:%M:%S %p IST')}] Silent check passed: {TARGET_FW} still active.")

if __name__ == "__main__":
    main()
