import json, os, re, glob
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURATION ---
DOMAIN = "https://tv.cricfoot.net"
HOURS_OFFSET = 9 
LOCAL_OFFSET = timezone(timedelta(hours=HOURS_OFFSET)) 
NOW = datetime.now(LOCAL_OFFSET)
TODAY_DATE = NOW.date() 

# Center Logic for Menu (3 days back, 3 days forward)
MENU_START_DATE = TODAY_DATE - timedelta(days=3)
TOP_LEAGUE_IDS = [17, 35, 23, 7, 8, 34, 679]

# --- 2. GOOGLE ADS & CSS ---
ADS_CODE = '''
<div class="ad-container" style="margin: 20px 0; text-align: center;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5525538810839147" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-5525538810839147" data-ad-slot="4345862479" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>'''

MENU_CSS = '''
<style>
    .weekly-menu-container { display: flex; width: 100%; gap: 4px; padding: 10px 5px; box-sizing: border-box; justify-content: space-between; overflow-x: auto; }
    .date-btn { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 8px 2px; text-decoration: none; border-radius: 6px; background: #fff; border: 1px solid #e2e8f0; min-width: 65px; transition: all 0.2s; }
    .date-btn div { font-size: 9px; text-transform: uppercase; color: #64748b; font-weight: bold; }
    .date-btn b { font-size: 10px; color: #1e293b; white-space: nowrap; }
    .date-btn.active { background: #2563eb; border-color: #2563eb; }
    .date-btn.active div, .date-btn.active b { color: #fff; }
    .league-header { background: #1e293b; color: #fff; padding: 8px 15px; font-weight: bold; font-size: 12px; text-transform: uppercase; margin-top: 15px; }
    
    /* Sofa Data Layout */
    .sofa-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 15px; overflow: hidden; }
    .sofa-header { background: #f8fafc; padding: 10px 15px; border-bottom: 1px solid #e2e8f0; font-weight: 800; font-size: 12px; color: #475569; text-transform: uppercase; }
    .stat-row { display: flex; justify-content: space-between; padding: 8px 15px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
    .form-dot { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #fff; font-size: 11px; font-weight: 800; margin-left: 4px; }
    .form-w { background: #22c55e; } .form-d { background: #94a3b8; } .form-l { background: #ef4444; }
    .lineup-grid { display: grid; grid-template-columns: 1fr 1fr; }
    .team-col { padding: 10px; }
    .team-col:first-child { border-right: 1px solid #eee; }
    .team-col ul { list-style: none; padding: 0; margin: 0; font-size: 13px; }
</style>'''

# --- 3. DATA HELPERS ---
def slugify(t): 
    return re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')

def get_sofa_json(dtype, dstr, mid):
    path = f"data/{dtype}/{dstr}.json"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try: return json.load(f).get(str(mid))
            except: return None
    return None

def build_sofa_html(m_id, d_folder):
    # 1. Winning Odds
    odds = get_sofa_json("odds", d_folder, m_id)
    odds_html = f"<div class='p-4 text-center text-sm'>Win Probability: Home {odds.get('home',{}).get('expected','0')}% | Away {odds.get('away',{}).get('expected','0')}%</div>" if odds else ""

    # 2. Confirmed Lineups
    lineup = get_sofa_json("lineups", d_folder, m_id)
    line_html = "<div class='p-4 text-gray-400 italic text-sm'>Lineups not available yet</div>"
    if lineup and 'home' in lineup:
        h = "".join([f"<li>{p['player']['name']}</li>" for p in lineup['home'].get('players', [])[:11]])
        a = "".join([f"<li>{p['player']['name']}</li>" for p in lineup['away'].get('players', [])[:11]])
        line_html = f'<div class="lineup-grid"><div class="team-col"><b>Home XI</b><ul>{h}</ul></div><div class="team-col"><b>Away XI</b><ul>{a}</ul></div></div>'

    # 3. Match Statistics
    stats = get_sofa_json("statistics", d_folder, m_id)
    stat_html = "<div class='p-4 text-gray-400 italic text-sm'>Stats will update when live</div>"
    if stats and 'statistics' in stats:
        rows = ""
        for item in stats['statistics'][0]['groups'][0]['statisticsItems']:
            rows += f'<div class="stat-row"><span>{item["home"]}</span><b style="font-size:10px;color:#94a3b8;">{item["name"]}</b><span>{item["away"]}</span></div>'
        stat_html = rows

    # 4. H2H & Pre-Forms
    h2h = get_sofa_json("h2h", d_folder, m_id)
    h2h_html = ""
    if h2h:
        h_form = "".join([f'<span class="form-dot form-{f.lower()}">{f[0].upper()}</span>' for f in h2h.get('homeForm', [])])
        a_form = "".join([f'<span class="form-dot form-{f.lower()}">{f[0].upper()}</span>' for f in h2h.get('awayForm', [])])
        h2h_html = f'''<div class="stat-row"><b>Recent Form</b><div>{h_form}</div><div>{a_form}</div></div>
                       <div class="stat-row"><b>H2H Victories</b><span>{h2h.get("homeWins",0)}</span><span style="font-size:10px;color:#94a3b8;">VS</span><span>{h2h.get("awayWins",0)}</span></div>'''

    return f'''
    <div class="sofa-card"><div class="sofa-header">Winning Odds</div>{odds_html}</div>
    <div class="sofa-card"><div class="sofa-header">Confirmed Lineups</div>{line_html}</div>
    <div class="sofa-card"><div class="sofa-header">Match Statistics</div>{stat_html}</div>
    <div class="sofa-card"><div class="sofa-header">H2H & Team Form</div>{h2h_html}</div>'''

# --- 4. DATA LOADING ---
templates = {n: open(f'{n}_template.html', 'r', encoding='utf-8').read() for n in ['home','match','channel']}
all_matches = []
seen_ids = set()
for f in sorted(glob.glob("date/*.json")):
    with open(f, 'r', encoding='utf-8') as j:
        data = json.load(j)
        for m in data:
            if m.get('match_id') and m['match_id'] not in seen_ids:
                all_matches.append(m); seen_ids.add(m['match_id'])

channels_data, sitemap_urls = {}, [DOMAIN + "/"]

# --- 5. MATCH PAGE GENERATION ---
for m in all_matches:
    ts_raw = int(m['kickoff'])
    ts = ts_raw / 1000 if ts_raw > 10000000000 else ts_raw
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(LOCAL_OFFSET)
    slug, d_fold = slugify(m['fixture']), dt.strftime('%Y%m%d')
    m_url = f"{DOMAIN}/match/{slug}/{d_fold}/"
    sitemap_urls.append(m_url)

    # Individual Match Logic
    m_path = f"match/{slug}/{d_fold}"
    os.makedirs(m_path, exist_ok=True)
    rows, count = "", 0
    for c in m.get('tv_channels', []):
        count += 1
        pills = "".join([f'<a href="{DOMAIN}/channel/{slugify(ch)}/" style="display:inline-block;background:#f1f5f9;color:#2563eb;padding:4px 8px;border-radius:4px;margin:2px;text-decoration:none;font-weight:bold;border:1px solid #e2e8f0;font-size:12px;">{ch}</a>' for ch in c['channels']])
        rows += f'<div style="display:flex;padding:12px;border-bottom:1px solid #eee;background:#fff;"><div style="width:100px;font-weight:800;color:#64748b;font-size:11px;">{c["country"]}</div><div style="flex:1;">{pills}</div></div>'
        if count % 10 == 0: rows += ADS_CODE

    with open(f"{m_path}/index.html", "w", encoding='utf-8') as mf:
        html = templates['match'].replace("{{FIXTURE}}", m['fixture']).replace("{{DOMAIN}}", DOMAIN).replace("{{LEAGUE}}", m.get('league','Football'))
        html = html.replace("{{BROADCAST_ROWS}}", rows).replace("{{SOFA_DATA}}", build_sofa_html(m['match_id'], d_fold))
        html = html.replace("{{LOCAL_DATE}}", dt.strftime("%d %b %Y")).replace("{{LOCAL_TIME}}", dt.strftime("%H:%M")).replace("{{UNIX}}", str(int(ts))).replace("{{VENUE}}", m.get('venue','TBA'))
        mf.write(html)

    # Prep Channels
    for c in m.get('tv_channels', []):
        for ch in c['channels']:
            if ch not in channels_data: channels_data[ch] = []
            if ts > (NOW.timestamp() - 86400): channels_data[ch].append({'m':m,'dt':dt,'league':m.get('league')})

# --- 6. HOME & DAILY PAGES ---
for i in range(7):
    day = MENU_START_DATE + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    menu = f'{MENU_CSS}<div class="weekly-menu-container">'
    for j in range(7):
        d = MENU_START_DATE + timedelta(days=j)
        l = "index.html" if d == TODAY_DATE else f"{d.strftime('%Y-%m-%d')}.html"
        menu += f'<a href="{DOMAIN}/{l}" class="date-btn {"active" if d==day else ""}"><div>{d.strftime("%a")}</div><b>{d.strftime("%b %d")}</b></a>'
    menu += '</div>'

    day_matches = [m for m in all_matches if datetime.fromtimestamp(int(m['kickoff'])/1000 if int(m['kickoff']) > 10000000000 else int(m['kickoff']), tz=timezone.utc).astimezone(LOCAL_OFFSET).date() == day]
    day_matches.sort(key=lambda x: (x.get('league_id') not in TOP_LEAGUE_IDS, x.get('league',''), int(x['kickoff'])))

    listing, last_l, l_idx = "", "", 0
    for m in day_matches:
        dt = datetime.fromtimestamp(int(m['kickoff'])/1000 if int(m['kickoff']) > 10000000000 else int(m['kickoff']), tz=timezone.utc).astimezone(LOCAL_OFFSET)
        if m.get('league') != last_l:
            if last_l != "" and l_idx % 3 == 0: listing += ADS_CODE
            listing += f'<div class="league-header">{m.get("league")}</div>'
            last_l = m.get('league'); l_idx += 1
        listing += f'<a href="{DOMAIN}/match/{slugify(m["fixture"])}/{dt.strftime("%Y%m%d")}/" class="match-row" style="display:flex;align-items:center;padding:12px;background:#fff;border-bottom:1px solid #eee;text-decoration:none;"><div style="min-width:80px;text-align:center;border-right:1px solid #eee;margin-right:12px;"><div style="font-size:10px;color:#94a3b8;">{dt.strftime("%d %b")}</div><div style="font-weight:900;color:#2563eb;font-size:14px;">{dt.strftime("%H:%M")}</div></div><div style="font-weight:700;color:#1e293b;">{m["fixture"]}</div></a>'

    with open(fname, "w", encoding='utf-8') as f:
        f.write(templates['home'].replace("{{MATCH_LISTING}}", listing).replace("{{WEEKLY_MENU}}", menu).replace("{{DOMAIN}}", DOMAIN).replace("{{SELECTED_DATE}}", day.strftime("%A, %b %d")).replace("{{PAGE_TITLE}}", f"TV Channels For {day.strftime('%d %b')}"))

# --- 7. CHANNEL PAGES & SITEMAP ---
for ch, m_list in channels_data.items():
    c_dir = f"channel/{slugify(ch)}"
    os.makedirs(c_dir, exist_ok=True)
    c_list = "".join([f'<a href="{DOMAIN}/match/{slugify(x["m"]["fixture"])}/{x["dt"].strftime("%Y%m%d")}/" class="match-row" style="display:flex;align-items:center;padding:12px;background:#fff;border-bottom:1px solid #eee;text-decoration:none;"><div style="min-width:80px;text-align:center;border-right:1px solid #eee;margin-right:12px;"><div style="font-size:10px;color:#94a3b8;">{x["dt"].strftime("%d %b")}</div><div style="font-weight:900;color:#2563eb;font-size:14px;">{x["dt"].strftime("%H:%M")}</div></div><div><div style="font-weight:700;color:#1e293b;">{x["m"]["fixture"]}</div><div style="font-size:10px;color:#6366f1;">{x["league"]}</div></div></a>' for x in sorted(m_list, key=lambda x:x['dt'])])
    with open(f"{c_dir}/index.html", "w", encoding='utf-8') as f: f.write(templates['channel'].replace("{{CHANNEL_NAME}}", ch).replace("{{MATCH_LISTING}}", c_list).replace("{{DOMAIN}}", DOMAIN))

with open("sitemap.xml", "w", encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join([f'<url><loc>{u}</loc><lastmod>{NOW.strftime("%Y-%m-%d")}</lastmod></url>' for u in sorted(list(set(sitemap_urls)))]) + '</urlset>')

print(f"Build Finished. All data (Lineups, Stats, Odds, H2H, Forms) successfully integrated.")
