import json, os, re, glob
from datetime import datetime, timedelta

DOMAIN = "https://tv.cricfoot.net"
NOW = datetime.now()
TODAY_DATE = NOW.date()
START_WEEK = TODAY_DATE - timedelta(days=TODAY_DATE.weekday())

# High-priority leagues for Top Listing
TOP_LEAGUES = ["Premier League", "La Liga", "Champions League", "Serie A", "Bundesliga"]

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

# Load Data
all_matches = {}
for f in glob.glob("date/*.json"):
    with open(f, 'r', encoding='utf-8') as j:
        for m in json.load(j):
            all_matches[f"{m['fixture']}-{m['kickoff']}"] = m

with open('home_template.html', 'r') as f: home_temp = f.read()
with open('match_template.html', 'r') as f: match_temp = f.read()
with open('channel_template.html', 'r') as f: chan_temp = f.read()

sitemap_urls = [DOMAIN + "/"]
channels_data = {}

# Menu Generation
menu_html = ""
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    # URL Format: https://tv.cricfoot.net/2026-01-11
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    active = "bg-[#00a0e9] text-white" if day == TODAY_DATE else "text-slate-400"
    menu_html += f'<a href="{DOMAIN}/{fname}" class="flex-1 text-center py-4 px-2 {active}"><div class="text-[10px] uppercase font-bold">{day.strftime("%a")}</div><div class="text-sm font-black">{day.strftime("%b %d")}</div></a>'

# Generate Days
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    sitemap_urls.append(f"{DOMAIN}/{fname}")

    day_m = [m for m in all_matches.values() if datetime.fromtimestamp(m['kickoff']).date() == day]
    # Sort: Top Leagues first, then by time
    day_m.sort(key=lambda x: (x.get('league') not in TOP_LEAGUES, x['kickoff']))

    listing_html, last_league = "", ""
    for m in day_m:
        league = m.get('league', 'Other')
        if league != last_league:
            listing_html += f'<div class="league-header">{league}</div>'
            last_league = league
        
        is_top = "top-match" if league in TOP_LEAGUES else ""
        m_slug = slugify(m['fixture'])
        m_date = datetime.fromtimestamp(m['kickoff']).strftime('%Y%m%d')
        m_url = f"{DOMAIN}/match/{m_slug}/{m_date}/"
        sitemap_urls.append(m_url)

        listing_html += f'''
        <a href="{m_url}" class="match-row {is_top}">
            <div class="match-time" data-unix="{m['kickoff']}">--:--</div>
            <div class="match-info">{m['fixture']}</div>
        </a>'''
        
        # Build Deep Match Folder
        m_path = f"match/{m_slug}/{m_date}"
        os.makedirs(m_path, exist_ok=True)
        rows = ""
        for c in m.get('tv_channels', []):
            pills = "".join([f'<a href="{DOMAIN}/channel/{slugify(ch)}/" class="pill">{ch}</a>' for ch in c['channels']])
            rows += f'<div class="row"><div class="c-name">{c["country"]}</div><div class="ch-list">{pills}</div></div>'
            for ch in c['channels']: channels_data.setdefault(ch, []).append(m)
        
        with open(f"{m_path}/index.html", "w") as mf:
            mf.write(match_temp.replace("{{FIXTURE}}", m['fixture']).replace("{{UNIX}}", str(m['kickoff'])).replace("{{BROADCAST_ROWS}}", rows).replace("{{DOMAIN}}", DOMAIN).replace("{{LEAGUE}}", league).replace("{{DATE}}", day.strftime('%d %b %Y')))

    with open(fname, "w") as df:
        df.write(home_temp.replace("{{MATCH_LISTING}}", listing_html).replace("{{WEEKLY_MENU}}", menu_html).replace("{{DOMAIN}}", DOMAIN).replace("{{TODAY}}", day.strftime('%A, %b %d')))

# Channel Pages & Sitemap Final
for ch, ms in channels_data.items():
    c_slug = slugify(ch)
    os.makedirs(f"channel/{c_slug}", exist_ok=True)
    # ... logic to write channel index ...
    sitemap_urls.append(f"{DOMAIN}/channel/{c_slug}/")

with open("sitemap.xml", "w") as sm:
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in sitemap_urls: xml += f'<url><loc>{u}</loc><changefreq>daily</changefreq></url>'
    sm.write(xml + '</urlset>')

print("Build Complete.")
