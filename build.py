import json, os, re, glob
from datetime import datetime, timedelta, timezone

# --- CONFIGURATION ---
DOMAIN = "https://tv.cricfoot.net"
OUT = "dist"
LOCAL_OFFSET = timezone(timedelta(hours=5))

NOW = datetime.now(LOCAL_OFFSET)
TODAY_DATE = NOW.date()

MENU_START_DATE = TODAY_DATE - timedelta(days=3)
MENU_END_DATE = TODAY_DATE + timedelta(days=3)

TOP_LEAGUE_IDS = [17, 35, 23, 7, 8, 34, 679]

ADS_CODE = '''
<div class="ad-container" style="margin: 20px 0; text-align: center;">
</div>
'''

MENU_CSS = '''
<style>
    .weekly-menu-container {
        display: flex;
        width: 100%;
        gap: 4px;
        padding: 10px 5px;
        box-sizing: border-box;
        justify-content: space-between;
    }
    .date-btn {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 8px 2px;
        text-decoration: none;
        border-radius: 6px;
        background: #fff;
        border: 1px solid #e2e8f0;
        min-width: 0;
        transition: all 0.2s;
    }
    .date-btn div { font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: bold; }
    .date-btn b { font-size: 10px; color: #1e293b; white-space: nowrap; }
    .date-btn.active { background: #2563eb; border-color: #2563eb; }
    .date-btn.active div, .date-btn.active b { color: #fff; }
</style>
'''

def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')

# --- PREP ---
os.makedirs(OUT, exist_ok=True)

# --- LOAD TEMPLATES ---
templates = {}
for name in ['home', 'match', 'channel']:
    with open(f'{name}_template.html', 'r', encoding='utf-8') as f:
        templates[name] = f.read()

# --- LOAD DATA ---
all_matches = []
seen_match_ids = set()

for f in glob.glob("date/*.json"):
    with open(f, 'r', encoding='utf-8') as j:
        try:
            for m in json.load(j):
                mid = m.get('match_id')
                if mid and mid not in seen_match_ids:
                    all_matches.append(m)
                    seen_match_ids.add(mid)
        except:
            continue

channels_data = {}
sitemap_urls = [DOMAIN + "/"]

# --- MATCH PAGES ---
for m in all_matches:
    m_dt = datetime.fromtimestamp(int(m['kickoff']), tz=timezone.utc).astimezone(LOCAL_OFFSET)
    slug = slugify(m['fixture'])
    folder = m_dt.strftime('%Y%m%d')

    url = f"{DOMAIN}/match/{slug}/{folder}/"
    sitemap_urls.append(url)

    league = m.get('league', 'Other Football')

    for c in m.get('tv_channels', []):
        for ch in c['channels']:
            channels_data.setdefault(ch, [])
            if int(m['kickoff']) > NOW.timestamp() - 86400:
                if not any(x['m']['match_id'] == m['match_id'] for x in channels_data[ch]):
                    channels_data[ch].append({'m': m, 'dt': m_dt, 'league': league})

    path = os.path.join(OUT, "match", slug, folder)
    os.makedirs(path, exist_ok=True)

    rows = ""
    count = 0
    for c in m.get('tv_channels', []):
        count += 1
        pills = "".join([
            f'<a href="{DOMAIN}/channel/{slugify(ch)}/" style="display:inline-block;background:#f1f5f9;color:#2563eb;padding:2px 8px;border-radius:4px;margin:2px;text-decoration:none;font-weight:600;border:1px solid #e2e8f0;">{ch}</a>'
            for ch in c['channels']
        ])
        rows += f'''
        <div style="display:flex;padding:12px;border-bottom:1px solid #edf2f7;">
            <div style="width:100px;font-weight:800;">{c["country"]}</div>
            <div>{pills}</div>
        </div>'''
        if count % 10 == 0:
            rows += ADS_CODE

    html = templates['match']
    html = html.replace("{{FIXTURE}}", m['fixture'])
    html = html.replace("{{LEAGUE}}", league)
    html = html.replace("{{DOMAIN}}", DOMAIN)
    html = html.replace("{{BROADCAST_ROWS}}", rows)
    html = html.replace("{{UNIX}}", str(m['kickoff']))
    html = html.replace("{{LOCAL_DATE}}", f'<span data-unix="{m["kickoff"]}">{m_dt.strftime("%d %b %Y")}</span>')
    html = html.replace("{{LOCAL_TIME}}", f'<span data-unix="{m["kickoff"]}">{m_dt.strftime("%H:%M")}</span>')

    with open(os.path.join(path, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

# --- DAILY PAGES (UNCHANGED LOGIC) ---
ALL_DATES = sorted({datetime.fromtimestamp(int(m['kickoff']), tz=timezone.utc).astimezone(LOCAL_OFFSET).date() for m in all_matches})

for day in ALL_DATES:
    fname = "index.html" if day == TODAY_DATE else f"{day}.html"
    out_file = os.path.join(OUT, fname)

    if fname != "index.html":
        sitemap_urls.append(f"{DOMAIN}/{fname}")

    menu = MENU_CSS + '<div class="weekly-menu-container">'
    for j in range(7):
        d = MENU_START_DATE + timedelta(days=j)
        fn = "index.html" if d == TODAY_DATE else f"{d}.html"
        menu += f'<a href="{DOMAIN}/{fn}" class="date-btn {"active" if d==day else ""}"><div>{d.strftime("%a")}</div><b>{d.strftime("%b %d")}</b></a>'
    menu += '</div>'

    listing, last_league, lc = "", "", 0
    for m in sorted(all_matches, key=lambda x: x['kickoff']):
        dt = datetime.fromtimestamp(int(m['kickoff']), tz=timezone.utc).astimezone(LOCAL_OFFSET)
        if dt.date() != day:
            continue

        league = m.get('league', 'Other Football')
        if league != last_league:
            if last_league:
                lc += 1
                if lc % 3 == 0:
                    listing += ADS_CODE
            listing += f'<div class="league-header">{league}</div>'
            last_league = league

        slug = slugify(m['fixture'])
        folder = dt.strftime('%Y%m%d')
        listing += f'''
        <a href="{DOMAIN}/match/{slug}/{folder}/" class="match-row">
            <div>{dt.strftime("%H:%M")}</div>
            <div>{m["fixture"]}</div>
        </a>'''

    html = templates['home']
    html = html.replace("{{MATCH_LISTING}}", listing)
    html = html.replace("{{WEEKLY_MENU}}", menu)
    html = html.replace("{{DOMAIN}}", DOMAIN)
    html = html.replace("{{SELECTED_DATE}}", day.strftime("%A, %b %d, %Y"))
    html = html.replace("{{PAGE_TITLE}}", f"TV Channels For {day.strftime('%A, %b %d, %Y')}")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

# --- CHANNEL PAGES ---
for ch, items in channels_data.items():
    cdir = os.path.join(OUT, "channel", slugify(ch))
    os.makedirs(cdir, exist_ok=True)
    sitemap_urls.append(f"{DOMAIN}/channel/{slugify(ch)}/")

    rows = ""
    for i in items:
        m, dt, league = i['m'], i['dt'], i['league']
        rows += f'''
        <a href="{DOMAIN}/match/{slugify(m["fixture"])}/{dt.strftime("%Y%m%d")}/">
            {dt.strftime("%H:%M")} - {m["fixture"]} ({league})
        </a>'''

    html = templates['channel']
    html = html.replace("{{CHANNEL_NAME}}", ch)
    html = html.replace("{{MATCH_LISTING}}", rows)
    html = html.replace("{{DOMAIN}}", DOMAIN)

    with open(os.path.join(cdir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

# --- SITEMAP ---
sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for u in sorted(set(sitemap_urls)):
    sm += f'<url><loc>{u}</loc><lastmod>{NOW.strftime("%Y-%m-%d")}</lastmod></url>'
sm += '</urlset>'

with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sm)

print("✅ Build complete → dist/ (HTML identical, CSS & JS untouched)")
