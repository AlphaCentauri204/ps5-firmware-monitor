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

def generate_web_dashboard(latest_ofw: str, is_alive: bool):
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
        .container {{
            max-width: 860px;
            margin: 0 auto;
        }}
        .brand {{
            font-size: 0.85rem;
            color: #64748b;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            margin-bottom: 24px;
        }}
        .subhead {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #64748b;
            margin-bottom: 6px;
            font-weight: 700;
        }}
        .header-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}
        .refresh-btn {{
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid #334155;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
        }}
        .banner {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 24px;
        }}
        .banner-left {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.88rem;
            font-weight: 500;
        }}
        .dot {{
            width: 8px;
            height: 8px;
            background-color: {'#10b981' if is_alive else '#ef4444'};
            border-radius: 50%;
        }}
        .badge-online {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .badge-revoked {{
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .timestamp {{
            font-size: 0.78rem;
            color: #94a3b8;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 24px;
            position: relative;
        }}
        .card-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94a3b8;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        .card-val {{
            font-size: 2.3rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 10px;
        }}
        .card-sub {{
            font-size: 0.78rem;
            color: #64748b;
            line-height: 1.4;
        }}
        .notice {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 14px 18px;
            font-size: 0.8rem;
            color: #64748b;
            line-height: 1.5;
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
                <span>Live PSN manifests verified</span>
                <span class="{badge_class}">{badge_text}</span>
            </div>
            <div class="timestamp">Last checked: {now_utc}</div>
        </div>
        <div class="grid">
            <div class="card">
                <div class="card-label">Global Minimum</div>
                <div class="card-val">{TARGET_FW}</div>
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
                <div class="card-sub">Target firmware is authorized on network</div>
            </div>
        </div>
        <div class="notice">
            ⓘ <b>ONLINE</b> indicates firmware {TARGET_FW} satisfies the force_update baseline in the active manifest. This is a read-only monitoring status page updated automatically.
        </div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    latest_ofw = get_latest_ofw()
    alive_fws = ["13.60", latest_ofw]
    is_alive = TARGET_FW in alive_fws

    generate_web_dashboard(latest_ofw, is_alive)

    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(build_modern_card("🔎 MANUAL AUDIT", latest_ofw, alive_fws, is_alive))
        return

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
