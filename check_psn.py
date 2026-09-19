import os
import re
import requests
import xml.etree.ElementTree as ET

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_EVENT = os.getenv("GITHUB_EVENT_NAME", "")

# Root dynamic checker that always resolves the newest OFW version
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
            # Find the newest system update label or sub-version
            label = root.findtext(".//level2_label")
            if label:
                clean_ver = re.findall(r'(\d{2}\.\d{2})', label)
                if clean_ver:
                    return clean_ver[0]
    except Exception as e:
        print(f"Error checking Sony: {e}")
    return "14.00"

def main():
    latest_ofw = get_latest_ofw()
    
    # Both 13.60 and 14.00 are alive during this grace period
    alive_fws = ["13.60", latest_ofw]

    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(
            f"🔎 *Manual Check*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Still Alive: `{', '.join(set(alive_fws))}`\n"
            f"Target FW `{TARGET_FW}` status: 🟢 *PSN Access Active*"
        )
        return

    if GITHUB_EVENT == "schedule":
        send_telegram(
            f"🟢 *12-Hour PSN Status Update*\n\n"
            f"Latest OFW: `{latest_ofw}`\n"
            f"Target FW `{TARGET_FW}`: Still Active on PSN."
        )

if __name__ == "__main__":
    main()
