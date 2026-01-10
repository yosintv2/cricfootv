import json, os, re, glob, logging
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring

# --- CONFIG ---
DOMAIN = "https://tv.cricfoot.net"
INPUT_FOLDER = "date"
OUTPUT_FOLDER = "public"
PRIORITY_IDS = [23, 17] # Serie A and Premier League

logging.basicConfig(level=logging.INFO, format='%(message)s')

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

def run():
    # Ensure folders exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 1. LOAD TEMPLATES
    try:
        with open('home_template.html', 'r', encoding='utf-8') as f: home_t = f.read()
        with open('match_template.html', 'r', encoding='utf-8') as f: match_t = f.read()
    except Exception as e:
        print(f"ERROR: Missing template files in root! {e}")
        return

    # 2. LOAD DATA FROM date/ FOLDER
    matches = []
    json_files = glob.glob(f"{INPUT_FOLDER}/*.json")
    print(f"Scanning {INPUT_FOLDER} folder... Found {len(json_files)} files.")

    for f_path in json_files:
        with open(f_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list): matches.extend(data)
            else: matches.append(data)

    if not matches:
        print("ALERT: No match data found in date/*.json. Page will be empty.")
        return

    # 3. SORT: Priority IDs first, then Time
    matches.sort(key=lambda x: (x.get('league_id') not in PRIORITY_IDS, x['kickoff']))

    # 4. GENERATE CONTENT
    listing_html = ""
    last_league = ""
    sitemap_urls = [f"{DOMAIN}/"]

    for m in matches:
        m_dt = datetime.fromtimestamp(m['kickoff'])
        m_slug = slugify(m['fixture'])
        date_id = m_dt.strftime('%Y%m%d')
        
        # Match Page Generation
        m_dir = os.path.join(OUTPUT_FOLDER, "match", m_slug, date_id)
        os.makedirs(m_dir, exist_ok=True)

        rows = ""
        for item in m.get('tv_channels', []):
            pills = "".join([f'<span style="padding:2px 8px; background:#e0f2fe; margin-right:5px; border-radius:4px; font-size:12px;">{ch}</span>' for ch in item['channels']])
            rows += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:10px;"><b>{item["country"]}</b></td><td>{pills}</td></tr>'

        m_page = match_t.replace("{{FIXTURE}}", m['fixture'])\
                        .replace("{{TIME_UNIX}}", str(m['kickoff']))\
                        .replace("{{LEAGUE}}", m.get('league', 'Football'))\
                        .replace("{{VENUE}}", m.get('venue', 'Stadium'))\
                        .replace("{{BROADCAST_ROWS}}", rows)\
                        .replace("{{DOMAIN}}", DOMAIN)
        
        with open(os.path.join(m_dir, "index.html"), "w", encoding='utf-8') as f: f.write(m_page)
        sitemap_urls.append(f"{DOMAIN}/match/{m_slug}/{date_id}/")

        # Home Page Listing
        if m['league'] != last_league:
            listing_html += f'<div class="league-header">{m["league"]}</div>'
            last_league = m['league']
        
        listing_html += f'''
        <a href="{DOMAIN}/match/{m_slug}/{date_id}/" class="match-row">
            <div class="match-time" data-unix="{m['kickoff']}"></div>
            <div class="match-info">{m['fixture']}</div>
        </a>'''

    # 5. SAVE HOME PAGE
    final_home = home_t.replace("{{MATCH_LISTING}}", listing_html).replace("{{DOMAIN}}", DOMAIN).replace("{{PAGE_TITLE}}", "Live Football TV Guide").replace("{{WEEKLY_MENU}}", "")
    with open(os.path.join(OUTPUT_FOLDER, "index.html"), "w", encoding='utf-8') as f: f.write(final_home)

    print(f"SUCCESS: {len(matches)} matches processed into /public")

if __name__ == "__main__":
    run()
