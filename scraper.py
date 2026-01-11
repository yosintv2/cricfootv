import os
import json
import time
import requests
from datetime import datetime, timedelta

# Realistic headers to mimic a genuine Chrome browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

def get_tomorrow_date():
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")

def fetch_data(url):
    try:
        # We use a session to maintain cookies like a real browser
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 403:
            print(f"[-] 403 Forbidden at {url}. IP Blocked.")
            return None
        return response.json()
    except Exception as e:
        print(f"[-] Error: {e}")
        return None

def run():
    date_str = get_tomorrow_date()
    file_name = f"{date_str.replace('-', '')}.json"
    folder = "date"
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    print(f"🚀 Scraping fixtures for: {date_str}")
    
    # Try the main API endpoint
    api_url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    data = fetch_data(api_url)

    # Fallback to 'inverse' if the first one fails or is empty
    if not data or not data.get("events"):
        print("[-] Primary feed failed, trying inverse...")
        api_url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}/inverse"
        data = fetch_data(api_url)

    if not data or not data.get("events"):
        print("❌ CRITICAL: SofaScore is blocking the GitHub Action IP.")
        return

    events = data["events"]
    results = []

    print(f"Found {len(events)} matches. Saving top 50...")
    for ev in events[:50]:
        results.append({
            "match_id": ev.get("id"),
            "kickoff": ev.get("startTimestamp"),
            "fixture": f"{ev['homeTeam']['name']} vs {ev['awayTeam']['name']}",
            "league": ev['tournament']['name'],
            "status": ev['status']['type']
        })

    with open(f"{folder}/{file_name}", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    
    print(f"✅ Success! Saved to {folder}/{file_name}")

if __name__ == "__main__":
    run()
