import json, os, re, glob
from datetime import datetime, timedelta

DOMAIN = "https://tv.cricfoot.net"
NOW = datetime.now()
TODAY_DATE = NOW.date()

# Week Logic: Find the most recent Friday
offset = (TODAY_DATE.weekday() - 4) % 7
START_WEEK = TODAY_DATE - timedelta(days=offset)

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

# Load Templates
with open('home_template.html', 'r') as f: home_temp = f.read()
with open('match_template.html', 'r') as f: match_temp = f.read()
with open('channel_template.html', 'r') as f: chan_temp = f.read()

# Load Data
all_matches = []
for f in glob.glob("date/*.json"):
    with open(f, 'r', encoding='utf-8') as j:
        all_matches.extend(json.load(j))

channels_data = {}
sitemap_urls = [DOMAIN + "/"]

# 1. Generate Weekly Menu
menu_html = ""
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    active = "active" if day == TODAY_DATE else ""
    menu_html += f'<a href="{DOMAIN}/{fname}" class="date-btn flex-1 text-center py-4 {active}"><div class="text-[9px] uppercase font-bold opacity-60">{day.strftime("%a")}</div><div class="text-sm font-black">{day.strftime("%b %d")}</div></a>'

# 2. Build Daily Pages
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    day_m = [m for m in all_matches if datetime.fromtimestamp(m['kickoff']).date() == day]
    day_m.sort(key=lambda x: (x.get('league') != "Premier League", x['kickoff'])) # Priority sorting

    listing_html, last_league = "", ""
    for m in day_m:
        league = m.get('league', 'International')
        if league != last_league:
            listing_html += f'<div class="league-header">{league}</div>'
            last_league = league
        
        m_slug, m_date = slugify(m['fixture']), datetime.fromtimestamp(m['kickoff']).strftime('%Y%m%d')
        m_url = f"{DOMAIN}/match/{m_slug}/{m_date}/"
        listing_html += f'<a href="{m_url}" class="match-row"><div class="match-time">{datetime.fromtimestamp(m["kickoff"]).strftime("%H:%M")}</div><div class="match-info">{m["fixture"]}</div></a>'
        
        # Match Page Generation
        m_path = f"match/{m_slug}/{m_date}"
        os.makedirs(m_path, exist_ok=True)
        rows = ""
        for c in m.get('tv_channels', []):
            pills = "".join([f'<a href="{DOMAIN}/channel/{slugify(ch)}/" class="channel-pill">{ch}</a>' for ch in c['channels']])
            rows += f'<div class="flex justify-between p-4"><span class="font-bold text-[10px] uppercase text-slate-400">{c["country"]}</span><div class="flex gap-2">{pills}</div></div>'
            for ch in c['channels']: channels_data.setdefault(ch, []).append(m)

        with open(f"{m_path}/index.html", "w") as mf:
            mf.write(match_template_filler(match_temp, m, rows, league, day))

    with open(fname, "w") as df:
        df.write(home_temp.replace("{{MATCH_LISTING}}", listing_html).replace("{{WEEKLY_MENU}}", menu_html).replace("{{DOMAIN}}", DOMAIN).replace("{{PAGE_TITLE}}", f"Football TV Guide {day.strftime('%Y-%m-%d')}"))

def match_template_filler(temp, m, rows, league, day):
    return temp.replace("{{FIXTURE}}", m['fixture']).replace("{{TIME}}", datetime.fromtimestamp(m['kickoff']).strftime('%H:%M'))\
               .replace("{{VENUE}}", m.get('venue', 'TBA')).replace("{{BROADCAST_ROWS}}", rows)\
               .replace("{{LEAGUE}}", league).replace("{{DOMAIN}}", DOMAIN).replace("{{DATE}}", day.strftime('%d %b %Y'))

# 3. Channel Pages
for ch, ms in channels_data.items():
    c_slug = slugify(ch)
    os.makedirs(f"channel/{c_slug}", exist_ok=True)
    c_listing = "".join([f'<a href="{DOMAIN}/match/{slugify(x["fixture"])}/{datetime.fromtimestamp(x["kickoff"]).strftime("%Y%m%d")}/" class="match-row"><div class="match-time">{datetime.fromtimestamp(x["kickoff"]).strftime("%H:%M")}</div><div class="match-info">{x["fixture"]}</div></a>' for x in ms])
    with open(f"channel/{c_slug}/index.html", "w") as cf:
        cf.write(chan_temp.replace("{{CHANNEL_NAME}}", ch).replace("{{MATCH_LISTING}}", c_listing).replace("{{DOMAIN}}", DOMAIN))

print("Build Successful. Friday-to-Thursday week generated.")
