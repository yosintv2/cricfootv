import os
import json
from datetime import datetime, timedelta
from curl_cffi import requests

def get_tomorrow_date():
    # Gets the date for 1 day from now
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")

def fetch_sofascore(url):
    try:
        # impersonate="chrome120" makes the TLS fingerprint look like a real browser
        r = requests.get(url, impersonate="chrome120", timeout=30)
        if r.status_code == 200:
            return r.json()
        print(f"[-] Failed with status {r.status_code} at {url}")
        return None
    except Exception as e:
        print(f"[-] Request error: {e}")
        return None

def run():
    date_str = get_tomorrow_date()
    file_name = f"{date_str.replace('-', '')}.json"
    folder = "date"
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    print(f"🚀 Scraping fixtures for: {date_str} (Stealth Mode)")
    
    # Try the main API endpoint
    api_url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    data = fetch_sofascore(api_url)

    # Fallback to inverse
    if not data or not data.get("events"):
        print("[-] Primary feed blocked/empty, trying inverse...")
        api_url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}/inverse"
        data = fetch_sofascore(api_url)

    if not data or not data.get("events"):
        print("❌ CRITICAL: IP is still blocked. SofaScore has flagged this GitHub Runner.")
        return

    events = data["events"]
    results = []

    print(f"Found {len(events)} matches. Extracting data...")
    for ev in events:
        results.append({
            "match_id": ev.get("id"),
            "kickoff": ev.get("startTimestamp"),
            "fixture": f"{ev['homeTeam']['name']} vs {ev['awayTeam']['name']}",
            "league": ev['tournament']['name'],
            "league_id": ev.get('tournament', {}).get('uniqueTournament', {}).get('id', 0)
        })

    with open(f"{folder}/{file_name}", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    
    print(f"✅ SUCCESS! File created: {folder}/{file_name}")

if __name__ == "__main__":
    run()
