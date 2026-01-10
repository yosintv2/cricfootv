import json, os, re
from datetime import datetime, timedelta

# --- CONFIGURATION ---
DOMAIN = "https://tv.cricfoot.net" # Change this!
TOP_LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "Champions League"]

with open('matches.json', 'r') as f: matches = json.load(f)
with open('home_template.html', 'r') as f: home_temp = f.read()
with open('match_template.html', 'r') as f: match_temp = f.read()

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

# --- GENERATE DATE MENU ---
today = datetime.now()
date_menu_html = ""
for i in range(-2, 5):  # 2 days ago to 4 days ahead
    date_target = today + timedelta(days=i)
    active_class = "bg-[#00a0e9] text-white" if i == 0 else "bg-[#1e293b] text-gray-300 hover:bg-[#334155]"
    date_menu_html += f'<a href="/date-{date_target.strftime("%Y-%m-%d")}.html" class="px-3 py-2 rounded text-xs font-bold transition {active_class}">{date_target.strftime("%b %d")}</a>'

# --- PROCESS DATA ---
leagues_data = {}
all_channels = set()
for m in matches:
    league = m.get('league', 'Other')
    leagues_data.setdefault(league, []).append(m)
    for c in m.get('tv_channels', []):
        for ch in c.get('channels', []): all_channels.add(ch)

# --- GENERATE MATCH LISTING ---
listing_html = ""
for league, m_list in leagues_data.items():
    listing_html += f'<div class="mb-4 shadow-sm"><div class="bg-[#334155] text-white px-4 py-1.5 text-xs font-bold uppercase tracking-wider">{league}</div>'
    for m in m_list:
        dt = datetime.fromtimestamp(m['kickoff'])
        slug = f"match/{slugify(m['fixture'])}/{dt.strftime('%d-%b-%Y').lower()}"
        os.makedirs(slug, exist_ok=True)
        
        listing_html += f'''
        <a href="/{slug}/" class="flex items-center bg-white dark:bg-[#1e293b] p-3 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-[#2d3748]">
            <div class="w-16 text-sm font-bold text-[#00a0e9]">{dt.strftime('%H:%M')}</div>
            <div class="flex-1 text-sm font-semibold">{m['fixture']}</div>
            <div class="text-[10px] text-gray-400 uppercase font-bold">{m.get('venue', 'TBA')}</div>
        </a>'''
        
        # Build individual match page (similar logic to previous, using match_template.html)
        # ... (Template replacement code here) ...

# Save Home Page
final_home = home_temp.replace("{{DATE_MENU}}", date_menu_html).replace("{{MATCH_LISTING}}", listing_html)
with open("index.html", "w") as f: f.write(final_home)
