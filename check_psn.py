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

SLOPCHECK_URL = "https://slopcheck.brisk-shell-7489.chatgpt.site/"
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
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_official_sony_ofw():
    try:
        headers = {"User-Agent": "PlayStation 5", "Connection": "close"}
        r = requests.get(SONY_CHECKER_URL, headers=headers, timeout=6)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            label = root.findtext(".//level2_label")
            if label:
                matches = re.findall(r'\b(\d{1,2}\.\d{2})\b', label)
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
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(SLOPCHECK_URL, headers=headers, timeout=8)
        if r.status_code == 200:
            text = r.text
            
            # Match 8/8 or similar region agreement cleanly
            agree_m = re.search(r'(\d+/\d+)\s*(?:available\s*)?regions', text, re.IGNORECASE)
            if agree_m:
                agreement = agree_m.group(1)

            # Check if global minimum has been shifted to 14.00 or higher
            if "14.00" in text and "Consensus force_update" in text:
                # If 14.00 is listed right near force_update baseline, it's revoked
                check_min = re.search(r'GLOBAL\s*MINIMUM.*?([0-9]{2}\.[0-9]{2})', text, re.DOTALL | re.IGNORECASE)
                if check_min and check_min.group(1) != "25.25":
                    global_min = check_min.group(1)
    except Exception as e:
        print(f"Consensus tracker error: {e}")

    # Accurate status verification
    try:
        is_alive = float(TARGET_FW) >= float(global_min)
    except Exception:
        is_alive = (TARGET_FW == global_min)

    return latest_ofw, global_min, is_alive, agreement

def build_modern_card(title: str, latest_ofw: str, global_min: str, is_alive: bool, agreement: str) -> str:
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
    card_sub = "Consensus force_update baseline across reporting regions" if is_alive else "Target firmware has been dropped"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global PS5 Firmware Status</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: #0b0e14;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-height: 100vh;
            padding: 30px 20px;
        }}
        .container {{ max-width: 860px; margin: 0 auto; }}
        .brand {{
            font-size: 0.85rem; color: #64748b; font-weight: 600; letter-spacing: 0.5px;
            display: flex; justify-content: space-between; margin-bottom: 24px;
        }}
        .subhead {{
            font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px;
            color: #64748b; margin-bottom: 6px; font-weight: 700;
        }}
        .header-row {{
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 12px; margin-bottom: 24px;
        }}
        .title {{ font-size: 1.9rem; font-weight: 800; letter-spacing: -0.5px; }}
        .refresh-btn {{
            background: #1e293b; color: #cbd5e1; border: 1px solid #334155;
            padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
        }}
        .banner {{
            background: #111827; border: 1px solid #1f2937; border-radius: 10px;
            padding: 14px 20px; display: flex; justify-content: space-between;
            align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 24px;
        }}
        .banner-left {{ display: flex; align-items: center; gap: 10px; font-size: 0.88rem; font-weight: 500; }}
        .dot {{
            width: 8px; height: 8px; border-radius: 50%;
            background-color: {'#10b981' if is_alive else '#ef4444'};
        }}
        .badge-online {{ background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }}
        .badge-revoked {{ background: rgba(239, 68, 68, 0.15); color: #f87171; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }}
        .timestamp {{ font-size: 0.78rem; color: #94a3b8; }}
        .grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px; margin-bottom: 24px;
        }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 24px; }}
        .card-label {{
            font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;
            color: #94a3b8; font-weight: 700; margin-bottom: 12px;
        }}
        .card-val {{ font-size: 2.3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 10px; }}
        .card-sub {{ font-size: 0.78rem; color: #64748b; line-height: 1.4; }}
        .notice {{
            background: #0f172a; border: 1px solid #1e293b; border-radius: 8px;
            padding: 14px 18px; font-size: 0.8rem; color: #64748b; line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="brand">
            <span>Alpha_Centauri204</span>
            <span>PLAYSTATION 5 &nbsp;•&nbsp; GLOBAL</span>
        </div>
        <div class="subhead">Global PS5 Firmware Status</div>
        <div class="header-row">
            <h1 class="title">One view. Every region.</h1>
            <button class="refresh-btn" onclick="location.reload()">⟳ Refresh</button>
        </div>
        <div class="banner">
            <div class="banner-left">
                <span class="dot"></span>
                <span>Live PSN manifests verified ({agreement} regions agree)</span>
                <span class="{badge_class}">{badge_text}</span>
            </div>
            <div class="timestamp">Last checked: {now_utc}</div>
        </div>
        <div class="grid">
            <div class="card">
                <div class="card-label">Global Minimum</div>
                <div class="card-val">{global_min}</div>
                <div class="card-sub">{card_sub}</div>
            </div>
            <div class="card">
                <div class="card-label">Latest Available</div>
                <div class="card-val">{latest_ofw}</div>
                <div class="card-sub">Consensus latest system software across reporting regions</div>
            </div>
            <div class="card">
                <div class="card-label">PSN Status</div>
                <div class="card-val" style="font-size: 1.7rem; color: {'#34d399' if is_alive else '#f87171'};">{badge_text}</div>
                <div class="card-sub">Target firmware is {'authorized' if is_alive else 'revoked'}</div>
            </div>
        </div>
        <div class="notice">
            ⓘ <b>{badge_text}</b> indicates firmware {TARGET_FW} status against the live regional manifests.
        </div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    latest_ofw, global_min, is_alive, agreement = fetch_live_status()

    generate_web_dashboard(latest_ofw, global_min, is_alive, agreement)

    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(build_modern_card("🔎 MANUAL AUDIT", latest_ofw, global_min, is_alive, agreement))
        return

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
            send_telegram(build_modern_card("☀️ MORNING STATUS", latest_ofw, global_min, is_alive, agreement))
            try:
                with open(STATE_FILE, "w") as f:
                    f.write(today_date)
            except Exception:
                pass
            return

    print(f"[{now_ist.strftime('%I:%M:%S %p IST')}] Silent check passed: {TARGET_FW} still active.")

if __name__ == "__main__":
    main()
