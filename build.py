import json, os, re, glob, time
from datetime import datetime, timedelta

# --- CONFIG ---
DOMAIN = "https://tv.cricfoot.net"
DATE_FOLDER = "date/*.json"
CURRENT_TIME = time.time() # Jan 11, 2026 

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

# 1. LOAD ALL DATA
all_matches = {}
for file_path in glob.glob(DATE_FOLDER):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for m in json.load(f):
                uid = f"{m['fixture']}-{m['kickoff']}"
                if uid not in all_matches: all_matches[uid] = m
    except: pass

# 2. HELPER: RENDER LISTING
def get_match_html(match_list, filter_date=None, live_only=False):
    output = ""
    grouped = {}
    for m in match_list:
        m_dt = datetime.fromtimestamp(m['kickoff'])
        # Filter by Date
        if filter_date and m_dt.date() != filter_date: continue
        # Filter by Live (Kickoff <= Now <= Kickoff + 2 hours)
        if live_only and not (m['kickoff'] <= CURRENT_TIME <= m['kickoff'] + 7200): continue
        
        l_name = m.get('league', 'Other')
        grouped.setdefault(l_name, []).append(m)

    for league, ms in grouped.items():
        output += f'<div class="league-title">{league}</div>'
        for mx in ms:
            t = datetime.fromtimestamp(mx['kickoff']).strftime('%H:%M')
            url = f"/match/{slugify(mx['fixture'])}/{datetime.fromtimestamp(mx['kickoff']).strftime('%Y%m%d')}/"
            output += f'<a href="{url}" class="match-card"><div class="time-col">{t}</div><div class="font-bold">{mx["fixture"]}</div></a>'
    return output if output else '<div class="p-10 text-center text-slate-400 font-bold">No matches found for this selection.</div>'

# 3. GENERATE PAGES
with open('home_template.html', 'r') as f: home_temp = f.read()

dates_to_gen = [
    ("yesterday.html", datetime.now().date() - timedelta(days=1), "Yesterday"),
    ("index.html", datetime.now().date(), "Today"),
    ("tomorrow.html", datetime.now().date() + timedelta(days=1), "Tomorrow"),
    ("live.html", None, "Live Now")
]

for filename, target_date, label in dates_to_gen:
    is_live = (filename == "live.html")
    content = get_match_html(all_matches.values(), filter_date=target_date, live_only=is_live)
    
    # Generate Date Menu
    menu = ""
    for fn, _, lbl in dates_to_gen:
        active = "bg-[#00a0e9] text-white" if lbl == label else "bg-slate-800 text-slate-400"
        menu += f'<a href="/{fn}" class="flex-1 text-center py-2 rounded text-[10px] font-black uppercase {active}">{lbl}</a>'

    page_html = home_temp.replace("{{MATCH_LISTING}}", content).replace("{{DATE_MENU}}", menu)
    with open(filename, "w") as f: f.write(page_html)

print("Build Successful: index, yesterday, tomorrow, and live pages generated.")
