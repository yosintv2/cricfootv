import json, os, re, glob
from datetime import datetime, timedelta, timezone

# --- CONFIGURATION ---
DOMAIN = "https://tv.cricfoot.net"
# Use UTC for "Now" to ensure consistency regardless of server location
NOW = datetime.now(timezone.utc)
TODAY_DATE = NOW.date()

# Friday to Thursday Logic
days_since_friday = (TODAY_DATE.weekday() - 4) % 7
START_WEEK = TODAY_DATE - timedelta(days=days_since_friday)

TOP_LEAGUE_IDS = [7, 35, 23, 17]

# YOUR SPECIFIC AD UNIT
AD_CODE = '''
<div class="ad-container py-4 bg-slate-50 border-b border-slate-200">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-5525538810839147"
         data-ad-slot="4345862479"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
'''

def slugify(t): 
    return re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')

# --- 1. LOAD TEMPLATES ---
templates = {}
for name in ['home', 'match', 'channel']:
    try:
        with open(f'{name}_template.html', 'r', encoding='utf-8') as f:
            templates[name] = f.read()
    except FileNotFoundError:
        print(f"CRITICAL ERROR: {name}_template.html not found.")

# --- 2. LOAD DATA FROM LOCAL JSON ---
all_matches = []
seen_match_ids = set()

for f in glob.glob("date/*.json"):
    with open(f, 'r', encoding='utf-8') as j:
        try:
            data = json.load(j)
            for m in data:
                mid = m.get('match_id')
                if mid and mid not in seen_match_ids:
                    all_matches.append(m)
                    seen_match_ids.add(mid)
        except Exception as e:
            print(f"Error reading {f}: {e}")

channels_data = {}
sitemap_urls = [DOMAIN + "/"]

# --- 3. GENERATE DAILY PAGES ---
for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    
    if fname != "index.html":
        sitemap_urls.append(f"{DOMAIN}/{fname}")

    # Build DYNAMIC MENU
    current_page_menu = ""
    for j in range(7):
        m_day = START_WEEK + timedelta(days=j)
        m_fname = "index.html" if m_day == TODAY_DATE else f"{m_day.strftime('%Y-%m-%d')}.html"
        active_class = "active" if m_day == day else ""
        current_page_menu += f'<a href="{DOMAIN}/{m_fname}" class="date-btn {active_class}"><div>{m_day.strftime("%a")}</div><b>{m_day.strftime("%b %d")}</b></a>'

    # FIX: Filter matches using UTC to prevent date jumping
    day_matches = []
    for m in all_matches:
        m_time = datetime.fromtimestamp(m['kickoff'], timezone.utc)
        if m_time.date() == day:
            day_matches.append(m)

    # Sort matches
    day_matches.sort(key=lambda x: (x.get('league_id') not in TOP_LEAGUE_IDS, x.get('match_id', 999999), x['kickoff']))

    listing_html, last_league = "", ""
    for m in day_matches:
        league = m.get('league', 'Other Football')
        
        # Insert Ad after league changes
        if league != last_league:
            if last_league != "":
                listing_html += AD_CODE
            listing_html += f'<div class="league-header">{league}</div>'
            last_league = league
        
        # Use UTC for formatted match data
        m_utc_time = datetime.fromtimestamp(m['kickoff'], timezone.utc)
        m_slug = slugify(m['fixture'])
        m_date_str = m_utc_time.strftime('%Y%m%d')
        
        m_url = f"{DOMAIN}/match/{m_slug}/{m_date_str}/"
        sitemap_urls.append(m_url)
        
        display_time = m_utc_time.strftime('%H:%M')
        
        listing_html += f'''
        <a href="{m_url}" class="match-row flex items-center p-4 bg-white group">
            <div class="time-box">
                <span class="font-bold text-blue-600 text-sm local-time" data-unix="{m['kickoff']}">{display_time}</span>
            </div>
            <div class="flex-1 px-4">
                <span class="text-slate-800 font-semibold text-sm md:text-base">{m['fixture']}</span>
            </div>
        </a>'''
        
        # --- 4. GENERATE MATCH PAGES ---
        m_path = f"match/{m_slug}/{m_date_str}"
        os.makedirs(m_path, exist_ok=True)
        venue_name = m.get('venue', 'To Be Announced')
        
        rows = ""
        for c in m.get('tv_channels', []):
            pills = ""
            for ch in c['channels']:
                ch_slug = slugify(ch)
                ch_url = f"{DOMAIN}/channel/{ch_slug}/"
                pills += f'<a href="{ch_url}" class="mx-1 text-blue-600 underline text-xs">{ch}</a>'
                if ch not in channels_data: channels_data[ch] = []
                if m not in channels_data[ch]: channels_data[ch].append(m)

            rows += f'<div class="flex justify-between p-4 border-b"><b>{c["country"]}</b><div>{pills}</div></div>'

        with open(f"{m_path}/index.html", "w", encoding='utf-8') as mf:
            m_html = templates['match'].replace("{{FIXTURE}}", m['fixture'])
            m_html = m_html.replace("{{TIME}}", str(m['kickoff']))
            m_html = m_html.replace("{{VENUE}}", venue_name)
            m_html = m_html.replace("{{DOMAIN}}", DOMAIN)
            m_html = m_html.replace("{{BROADCAST_ROWS}}", rows)
            m_html = m_html.replace("{{LEAGUE}}", league)
            # FIX: Match page now shows correct UTC date
            m_html = m_html.replace("{{DATE}}", m_utc_time.strftime('%d %b %Y'))
            mf.write(m_html)

    # Write the Final Daily/Home HTML
    with open(fname, "w", encoding='utf-8') as df:
        output = templates['home'].replace("{{MATCH_LISTING}}", listing_html)
        output = output.replace("{{WEEKLY_MENU}}", current_page_menu)
        output = output.replace("{{DOMAIN}}", DOMAIN)
        output = output.replace("{{SELECTED_DATE}}", day.strftime("%A, %b %d, %Y"))
        # NEW TITLE FORMAT
        output = output.replace("{{PAGE_TITLE}}", f"SocccerTV Live Streaming TV Channels For {day.strftime('%A, %b %d, %Y')} - CricFootTV")
        df.write(output)

# --- 5. GENERATE CHANNEL PAGES ---
for ch_name, ms in channels_data.items():
    c_slug = slugify(ch_name)
    c_dir = f"channel/{c_slug}"
    os.makedirs(c_dir, exist_ok=True)
    
    channel_menu = "".join([f'<a href="{DOMAIN}/{"index.html" if (START_WEEK + timedelta(days=j)) == TODAY_DATE else (START_WEEK + timedelta(days=j)).strftime("%Y-%m-%d") + ".html"}" class="date-btn"><div>{(START_WEEK + timedelta(days=j)).strftime("%a")}</div><b>{(START_WEEK + timedelta(days=j)).strftime("%b %d")}</b></a>' for j in range(7)])

    c_listing = ""
    for x in ms:
        x_utc = datetime.fromtimestamp(x['kickoff'], timezone.utc)
        x_slug, x_date = slugify(x['fixture']), x_utc.strftime('%Y%m%d')
        c_listing += f'''
        <a href="{DOMAIN}/match/{x_slug}/{x_date}/" class="match-row flex items-center p-4 bg-white group">
            <div class="time-box">
                <span class="font-bold text-blue-600 text-sm local-time" data-unix="{x['kickoff']}">{x_utc.strftime('%H:%M')}</span>
            </div>
            <div class="flex-1 px-4">
                <span class="text-slate-800 font-semibold text-sm">{x['fixture']}</span>
                <div class="text-[10px] text-gray-400 uppercase font-bold">{x.get('league', 'Football')}</div>
            </div>
        </a>'''

    with open(f"{c_dir}/index.html", "w", encoding='utf-8') as cf:
        cf.write(templates['channel'].replace("{{CHANNEL_NAME}}", ch_name)
                 .replace("{{MATCH_LISTING}}", c_listing)
                 .replace("{{WEEKLY_MENU}}", channel_menu)
                 .replace("{{DOMAIN}}", DOMAIN))

# --- 6. SITEMAP ---
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for url in sitemap_urls:
    sitemap_content += f'<url><loc>{url}</loc><lastmod>{NOW.strftime("%Y-%m-%d")}</lastmod></url>'
sitemap_content += '</urlset>'
with open("sitemap.xml", "w", encoding='utf-8') as sm:
    sm.write(sitemap_content)

print(f"Build Successful. UTC Time enforced.")
