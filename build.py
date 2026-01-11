import json, os, re, glob, urllib.request
from datetime import datetime, timedelta

DOMAIN = "https://tv.cricfoot.net"
NOW = datetime.now()
TODAY_DATE = NOW.date()

# 1. DEFINE DATE LOGIC FIRST (Fixes NameError)
# Calculates the most recent Friday
days_since_friday = (TODAY_DATE.weekday() - 4) % 7
START_WEEK = TODAY_DATE - timedelta(days=days_since_friday)

TOP_LEAGUE_IDS = [7, 35, 23, 17]

def slugify(t): 
    return re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')

# 2. LOAD TEMPLATES
templates = {}
for name in ['home', 'match', 'channel']:
    with open(f'{name}_template.html', 'r', encoding='utf-8') as f:
        templates[name] = f.read()

# 3. FETCH DATA
all_matches = []
seen_match_ids = set()
API_URL = "https://yosintv-api.pages.dev/api/date/"

try:
    with urllib.request.urlopen(API_URL) as response:
        data = json.loads(response.read().decode())
        for m in data:
            mid = m.get('match_id')
            if mid and mid not in seen_match_ids:
                all_matches.append(m)
                seen_match_ids.add(mid)
except Exception as e:
    print(f"API Error: {e}")

# 4. GENERATE PAGES (Using START_WEEK)
sitemap_urls = [DOMAIN + "/"]
channels_data = {}

for i in range(7):
    day = START_WEEK + timedelta(days=i) # Now it works!
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    
    # Generate Menu for this specific page
    current_page_menu = ""
    for j in range(7):
        m_day = START_WEEK + timedelta(days=j)
        m_fname = "index.html" if m_day == TODAY_DATE else f"{m_day.strftime('%Y-%m-%d')}.html"
        active_class = "active" if m_day == day else ""
        current_page_menu += f'<a href="{DOMAIN}/{m_fname}" class="date-btn {active_class}"><div>{m_day.strftime("%a")}</div><b>{m_day.strftime("%b %d")}</b></a>'

    # ... Rest of your filtering and file writing logic ...
