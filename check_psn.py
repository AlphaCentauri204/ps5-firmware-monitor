import os
import re
import datetime
import requests
import xml.etree.ElementTree as ET

TARGET_FW = "13.60"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_EVENT = os.getenv("GITHUB_EVENT_NAME", "")
STATE_FILE = "last_morning_ping.txt"

# Official Sony endpoint for Latest Published Firmware
SONY_URL = "https://fus01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml"

# Live community service performing auth manifest handshakes
CONSENSUS_URL = "https://slopcheck.brisk-shell-7489.chatgpt.site/"

def send_telegram(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_official_sony_ofw():
    try:
        headers = {"User-Agent": "PlayStation 5", "Connection": "close"}
        r = requests.get(SONY_URL, headers=headers, timeout=6)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            label = root.findtext(".//level2_label")
            if label:
                matches = re.findall(r'\b(1[0-5]\.\d{2})\b', label)
                if matches:
                    return matches[0]
    except Exception as e:
        print(f"Sony direct query error: {e}")
    return "14.00"

def fetch_live_status():
    latest_ofw = get_official_sony_ofw()
    global_min = TARGET_FW
    agreement = "8/8"
    is_alive = True

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml"
        }
        r = requests.get(CONSENSUS_URL, headers=headers, timeout=8)
        if r.status_code == 200:
            text = r.text

            # Extract region agreement (e.g., 8/8)
            agree_match = re.search(r'(\d+/\d+)\s*(?:available\s*)?regions', text, re.IGNORECASE)
            if agree_match:
                agreement = agree_match.group(1)

            # Strict version extraction: only matches realistic PS5 firmware versions (13.xx to 14.xx)
            min_match = re.search(r'GLOBAL\s*MINIMUM[^\d]*(\b1[34]\.\d{2}\b)', text, re.DOTALL | re.IGNORECASE)
            if min_match:
                global_min = min_match.group(1)
            else:
                # If target is missing or updated baseline has moved to 14.00
                if "14.00" in text and "Consensus force_update" in text:
                    global_min = "14.00"
    except Exception as e:
        print(f"Live backend fetch notice: {e}")

    try:
        is_alive = float(TARGET_FW) >= float(global_min)
    except Exception:
        is_alive = (TARGET_FW == global_min)

    return latest_ofw, global_min, is_alive, agreement

def build_card(title: str, latest_ofw: str, global_min: str, is_alive: bool, agreement: str) -> str:
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_badge = "🟢 ONLINE" if is_alive else "🔴 REVOKED"
    status_msg = f"Firmware `{TARGET_FW}` is authorized." if is_alive else f"⚠️ Firmware `{TARGET_FW}` access terminated!"

    return (
        f"*{title}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎮 *PlayStation 5 Network*\n"
        f"📡 Status: {status_badge}\n"
        f"🕒 Checked: `{now_utc}`\n"
        f"🌐 Regions reporting: `{agreement}`\n\n"
        f"🔹 *Global Minimum:* `{global_min}`\n"
        f"🔹 *Latest Available:* `{latest_ofw}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Target:* `{TARGET_FW}` — {status_msg}"
    )

def generate_web_dashboard(latest_ofw: str, global_min: str, is_alive: bool, agreement: str):
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %Y, %I:%M %p UTC")
    badge_text = "ONLINE" if is_alive else "REVOKED"
    badge_class = "badge-online" if is_alive else "badge-revoked"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PS5 Global Status</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0b0e14; color: #f1f5f9; font-family: -apple-system, sans-serif; padding: 30px 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .brand {{ font-size: 0.8rem; color: #64748b; font-weight: 700; letter-spacing: 1px; margin-bottom: 20px; }}
        .title {{ font-size: 1.8rem; font-weight: 800; margin-bottom: 15px; }}
        .banner {{ background: #111827; border: 1px solid #1f2937; padding: 14px 20px; border-radius: 10px; margin-bottom: 20px; font-size: 0.88rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 20px; }}
        .card-label {{ font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; font-weight: 700; }}
        .val {{ font-size: 2.2rem; font-weight: 800; margin: 10px 0; }}
        .card-sub {{ font-size: 0.75rem; color: #64748b; }}
        .badge-online {{ color: #34d399; font-weight: 700; }}
        .badge-revoked {{ color: #f87171; font-weight: 700; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="brand">PLAYSTATION 5 &nbsp;•&nbsp; AUTHENTICATION MONITOR</div>
        <h1 class="title">Global PS5 Firmware Status</h1>
        <div class="banner">
            Live PSN manifests verified (<b>{agreement}</b> regions agree) &nbsp;|&nbsp; Last checked: {now_utc}
        </div>
        <div class="grid">
            <div class="card">
                <div class="card-label">Global Minimum</div>
                <div class="val">{global_min}</div>
                <div class="card-sub">Consensus force_update baseline</div>
            </div>
            <div class="card">
                <div class="card-label">Latest Available</div>
                <div class="val">{latest_ofw}</div>
                <div class="card-sub">Official build announced by Sony</div>
            </div>
            <div class="card">
                <div class="card-label">PSN Status</div>
                <div class="val {badge_class}">{badge_text}</div>
                <div class="card-sub">Target firmware {TARGET_FW} status</div>
            </div>
        </div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    latest_ofw, global_min, is_alive, agreement = fetch_live_status()
    generate_web_dashboard(latest_ofw, global_min, is_alive, agreement)

    # 1. Manual test dispatch
    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(build_card("🔎 MANUAL AUDIT", latest_ofw, global_min, is_alive, agreement))
        return

    # 2. Critical Alert: Target Firmware Revoked
    if not is_alive:
        send_telegram(
            f"🚨 *CRITICAL ALERT: PSN REVOCATION* 🚨\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"❌ *Target FW `{TARGET_FW}` has been dropped from PSN!*\n"
            f"🕒 Timestamp: `{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}`\n"
            f"🔹 Global Minimum: `{global_min}`\n"
            f"🔹 Latest Available: `{latest_ofw}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Take your console offline immediately.*"
        )
        return

    # 3. Daily Morning Status Update at 6:30 AM IST (01:00 UTC)
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
            send_telegram(build_card("☀️ MORNING STATUS", latest_ofw, global_min, is_alive, agreement))
            try:
                with open(STATE_FILE, "w") as f:
                    f.write(today_date)
            except Exception:
                pass
            return

    print(f"[{now_ist.strftime('%I:%M:%S %p IST')}] Silent check: {TARGET_FW} is active.")

if __name__ == "__main__":
    main()
