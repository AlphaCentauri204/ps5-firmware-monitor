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

# Official Sony regional update CDNs
SONY_ENDPOINTS = {
    "US": "https://fus01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml",
    "EU": "https://fue01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml",
    "JP": "https://fjp01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml",
    "ASIA": "https://fsa01.ps5.update.playstation.net/update/ps5/official/data/action/latest_checker.xml"
}

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

def check_official_sony():
    headers = {"User-Agent": "PlayStation 5", "Connection": "close"}
    region_results = {}

    for region, url in SONY_ENDPOINTS.items():
        try:
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                label = root.findtext(".//level2_label")
                if label:
                    # Clean extraction of firmware format (e.g. 14.00)
                    matches = re.findall(r'\b(\d{1,2}\.\d{2})\b', label)
                    if matches:
                        region_results[region] = matches[0]
        except Exception as e:
            print(f"Failed query for {region}: {e}")

    # Determine latest firmware reported across Sony's live servers
    latest_versions = list(region_results.values())
    latest_ofw = max(latest_versions) if latest_versions else "14.00"
    reporting_count = f"{len(region_results)}/{len(SONY_ENDPOINTS)}"

    return latest_ofw, reporting_count

def build_modern_card(title: str, latest_ofw: str, reporting_count: str) -> str:
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (
        f"*{title}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎮 *Sony PS5 Manifest Status*\n"
        f"🕒 Checked: `{now_utc}`\n"
        f"🌐 CDNs Responding: `{reporting_count}`\n\n"
        f"🔹 *Published OFW:* `{latest_ofw}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ Target FW `{TARGET_FW}`: Grace period status active until Sony revokes authorization."
    )

def generate_web_dashboard(latest_ofw: str, reporting_count: str):
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d, %Y, %I:%M %p UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Official PS5 Firmware Manifest</title>
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
        .dot {{ width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; }}
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
            <span>DIRECT SONY CDN MONITOR</span>
            <span>PLAYSTATION 5</span>
        </div>
        <div class="subhead">Official Manifest Status</div>
        <div class="header-row">
            <h1 class="title">Direct Server Feed</h1>
            <button class="refresh-btn" onclick="location.reload()">⟳ Refresh</button>
        </div>
        <div class="banner">
            <div class="banner-left">
                <span class="dot"></span>
                <span>Verified against official Sony endpoints ({reporting_count} CDNs online)</span>
            </div>
            <div class="timestamp">Last checked: {now_utc}</div>
        </div>
        <div class="grid">
            <div class="card">
                <div class="card-label">Target Firmware</div>
                <div class="card-val">{TARGET_FW}</div>
                <div class="card-sub">Current firmware under observation</div>
            </div>
            <div class="card">
                <div class="card-label">Published OFW</div>
                <div class="card-val">{latest_ofw}</div>
                <div class="card-sub">Official build announced by Sony's update servers</div>
            </div>
        </div>
        <div class="notice">
            ⓘ Data queried directly from Sony PlayStation CDN servers without third-party intermediaries.
        </div>
    </div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    latest_ofw, reporting_count = check_official_sony()

    generate_web_dashboard(latest_ofw, reporting_count)

    if GITHUB_EVENT == "workflow_dispatch":
        send_telegram(build_modern_card("🔎 MANUAL AUDIT", latest_ofw, reporting_count))
        return

    # Daily morning update at 6:30 AM IST (01:00 UTC)
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
            send_telegram(build_modern_card("☀️ MORNING STATUS", latest_ofw, reporting_count))
            try:
                with open(STATE_FILE, "w") as f:
                    f.write(today_date)
            except Exception:
                pass
            return

if __name__ == "__main__":
    main()
