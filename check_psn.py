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

    return (
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

def generate_web_dashboard(latest_ofw: str, alive_fws: list, is_alive: bool):
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    alive_str = ", ".join(sorted(set(alive_fws)))
    status_text = "ONLINE" if is_alive else "REVOKED"
    badge_bg = "#059669" if is_alive else "#dc2626"
    card_msg = f"Firmware {TARGET_FW} is authorized for PSN." if is_alive else f"Firmware {TARGET_FW} access has been terminated!"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PS5 PSN Firmware Tracker</title>
    <style>
        body {{
            background-color: #0b0f19;
            color: #f3f4f6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            padding: 28px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .badge {{
            background: {badge_bg};
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        .metric {{
            background: #1f2937;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .label {{
            color: #9ca3af;
            font-size: 0.88rem;
        }}
        .value {{
            font-weight: 600;
            font-family: monospace;
            font-size: 0.95rem;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 0.85rem;
            text-align: center;
            color: #6b7280;
        }}
        .status-msg {{
            margin-top: 15px;
            padding: 12px;
            border-radius: 8px;
            font-size: 0.9rem;
            text-align: center;
            background: {'rgba(5,150,105,0.1)' if is_alive else 'rgba(220,38,38,0.1)'};
            color: {'#34d399' if is_alive else '#f87171'};
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <span class="title">🎮 PS5 PSN TRACKER</span>
            <span class="badge">{status_text}</span>
        </div>
        <div class="metric">
            <span class="label">Target Firmware</span>
            <span class="value">{TARGET_FW}</span>
        </div>
        <div class="metric">
            <span class="label">Latest OFW</span>
            <span class="value">{latest_ofw}</span>
        </div>
        <div class="metric">
            <span class="label">Active Firmwares</span>
            <span class="value">{alive_str}</span>
        </div>
        <div class="metric">
            <span class="label">Last Checked</span>
            <span class="value">{now_utc}</span>
        </div>
        <div class="status-msg">{card_msg}</div>
        <div class="footer">Refresh page to view live status</div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    latest_ofw = get_latest_ofw()
    alive_fws = ["13.60", latest_ofw]
    is_alive = TARGET_FW in alive_fws

    # Always generate the public website file
    generate_web_dashboard(latest_ofw, alive_fws, is_alive)

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
            f"🔹 Active FW: `{', '.join(sorted(set(alive_fws)))}\n"
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

if __name__ == "__main__":
    main()
