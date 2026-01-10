import json, os, re, glob
from datetime import datetime, timedelta

DOMAIN = "https://tv.cricfoot.net"
NOW = datetime.now()
TODAY_DATE = NOW.date()

# Priority Leagues: Serie A (23) and Premier League (17)
TOP_LEAGUE_IDS = [23, 17]

# Friday to Thursday Logic
days_since_friday = (TODAY_DATE.weekday() - 4) % 7
START_WEEK = TODAY_DATE - timedelta(days=days_since_friday)

def slugify(t): 
    return re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')

# Load Templates
templates = {}
for name in ['home', 'match', 'channel']:
    with open(f'{name}_template.html', 'r', encoding='utf-8') as f:
        templates[name] = f.read()

# Load Data & De-duplicate by Match ID
all_matches = []
seen_match_ids = set()
for f_path in glob.glob("date/*.json"):
    with open(f_path, 'r', encoding='utf-8') as j:
        try:
            data = json.load(j)
            for m in data:
                mid = m.get('match_id')
                if mid not in seen_match_ids:
                    all_matches.append(m)
                    seen_match_ids.add(mid)
        except: continue

channels_data = {} 
sitemap_urls = [DOMAIN + "/"]

# 1. Generate Weekly Menu
menu_html = ""
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    active_class = "active" if day == TODAY_DATE else ""
    menu_html += f'<a href="{DOMAIN}/{fname}" class="date-btn {active_class}"><div>{day.strftime("%a")}</div><b>{day.strftime("%b %d")}</b></a>'

# 2. Generate Daily & Match Pages
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    sitemap_urls.append(f"{DOMAIN}/{fname}")
    
    # Precise Date Filtering (Fixes the Jan 11 issue)
    day_matches = [m for m in all_matches if datetime.fromtimestamp(m['kickoff']).date() == day]
    day_matches.sort(key=lambda x: (x.get('league_id') not in TOP_LEAGUE_IDS, x.get('match_id', 99999999), x['kickoff']))

    listing_html, last_league = "", ""
    for m in day_matches:
        league = m.get('league', 'Other')
        if league != last_league:
            listing_html += f'<div class="league-header">{league}</div>'
            last_league = league
        
        m_slug, m_date = slugify(m['fixture']), datetime.fromtimestamp(m['kickoff']).strftime('%Y%m%d')
        m_url = f"{DOMAIN}/match/{m_slug}/{m_date}/"
        pre_time = datetime.fromtimestamp(m['kickoff']).strftime('%H:%M')
        
        listing_html += f'''
        <a href="{m_url}" class="match-row flex items-center p-4 bg-white group">
            <div class="time-box">
                <span class="font-bold text-blue-600 text-sm local-time" data-unix="{m['kickoff']}">{pre_time}</span>
            </div>
            <div class="flex-1 px-4">
                <span class="text-slate-800 font-semibold text-sm md:text-base">{m['fixture']}</span>
            </div>
        </a>'''
        
        # Build Match Page
        m_path = f"match/{m_slug}/{m_date}"
        os.makedirs(m_path, exist_ok=True)
        rows = ""
        for c in m.get('tv_channels', []):
            pills = ""
            for ch_name in c['channels']:
                ch_slug = slugify(ch_name)
                pills += f'<a href="{DOMAIN}/channel/{ch_slug}/" class="mx-1 text-blue-600 underline text-xs">{ch_name}</a>'
                # Collect matches for Channel Pages
                if ch_name not in channels_data: channels_data[ch_name] = []
                if m not in channels_data[ch_name]: channels_data[ch_name].append(m)
            
            rows += f'<div class="flex justify-between p-4 border-b"><b>{c["country"]}</b><div>{pills}</div></div>'

        with open(f"{m_path}/index.html", "w", encoding='utf-8') as mf:
            mf.write(templates['match'].replace("{{FIXTURE}}", m['fixture'])
                     .replace("{{TIME}}", str(m['kickoff']))
                     .replace("{{VENUE}}", m.get('venue', 'TBA')).replace("{{BROADCAST_ROWS}}", rows)
                     .replace("{{LEAGUE}}", league).replace("{{DOMAIN}}", DOMAIN).replace("{{DATE}}", day.strftime('%d %b %Y')))

    with open(fname, "w", encoding='utf-8') as df:
        df.write(templates['home'].replace("{{MATCH_LISTING}}", listing_html).replace("{{WEEKLY_MENU}}", menu_html).replace("{{DOMAIN}}", DOMAIN).replace("{{PAGE_TITLE}}", f"Soccer TV Schedule {day.strftime('%Y-%m-%d')}"))

# 3. Build Channel Pages using channel_template.html
for ch_name, ms in channels_data.items():
    c_slug = slugify(ch_name)
    c_dir = f"channel/{c_slug}"
    os.makedirs(c_dir, exist_ok=True)
    
    s_url = f"{DOMAIN}/channel/{c_slug}/"
    sitemap_urls.append(s_url)
    
    c_listing = ""
    for x in ms:
        x_slug, x_date = slugify(x['fixture']), datetime.fromtimestamp(x['kickoff']).strftime('%Y%m%d')
        x_url = f"{DOMAIN}/match/{x_slug}/{x_date}/"
        c_listing += f'''
        <a href="{x_url}" class="match-row flex items-center p-4 bg-white group">
            <div class="time-box">
                <span class="font-bold text-blue-600 text-sm local-time" data-unix="{x['kickoff']}">{datetime.fromtimestamp(x['kickoff']).strftime('%H:%M')}</span>
            </div>
            <div class="flex-1 px-4">
                <span class="text-slate-800 font-semibold text-sm">{x['fixture']}</span>
                <div class="text-[10px] text-gray-400 uppercase font-bold">{x.get('league', 'Football')}</div>
            </div>
        </a>'''

    with open(f"{c_dir}/index.html", "w", encoding='utf-8') as cf:
        cf.write(templates['channel'].replace("{{CHANNEL_NAME}}", ch_name).replace("{{MATCH_LISTING}}", c_listing).replace("{{DOMAIN}}", DOMAIN))

# 4. Sitemap Generation
with open("sitemap.xml", "w", encoding='utf-8') as sm:
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for u in sitemap_urls: xml += f'<url><loc>{u}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
    sm.write(xml + '</urlset>')

print(f"Build Finished: Created {len(channels_data)} channel pages.")
