import os
import requests
import xml.etree.ElementTree as ET

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Official Sony live update checker XML endpoint
SONY_CHECKER_URL = "https://fus01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml"

def send_telegram(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

def check_sony_status():
    headers = {
        "User-Agent": "PlayStation 5"
    }
    try:
        response = requests.get(SONY_CHECKER_URL, headers=headers, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        system_pup = root.find(".//system_pup")
        
        if system_pup is None:
            print("System PUP node not found in XML response.")
            return

        # Read version metadata from Sony's manifest
        sub_ver = system_pup.findtext("level2_sub_ver", default="").strip()
        label = system_pup.findtext("level2_label", default="Unknown").strip()

        print(f"Queried Sony FUS: Latest PUP Label = {label}, Sub-Ver = {sub_ver}")

        # If a mandatory cut-off or deprecation flag is confirmed
        # You can track version boundaries or alert when Sony enforces 14.00+
        if "14.00" in label and TARGET_FW not in label:
            print(f"Firmware {TARGET_FW} is in grace period under OFW {label}.")

    except Exception as e:
        print(f"Error querying Sony servers: {e}")

if __name__ == "__main__":
    check_sony_status()
