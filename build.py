import json, os, re, glob, logging
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring

# --- CONFIG ---
DOMAIN = "https://tv.cricfoot.net"
INPUT_FOLDER = "date"
OUTPUT_FOLDER = "public"
# Add your priority league names or IDs here
TOP_LEAGUES = ["Serie A", "Premier League"] # You mentioned League 23 and 17

logging.basicConfig(level=logging.INFO, format='%(message)s')

class SoccerGenerator:
    def __init__(self):
        self.matches = []
        self.sitemap_urls = [f"{DOMAIN}/"]
        if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

    def slugify(self, text):
        return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

    def run(self):
        # Load your template
        with open('home_template.html', 'r', encoding='utf-8') as f:
            home_t = f.read()

        # Load Match Data
        for f_path in glob.glob(f"{INPUT_FOLDER}/*.json"):
            with open(f_path, 'r', encoding='utf-8') as f:
                self.matches.extend(json.load(f))

        # Sort Logic: Top Leagues First, then Kickoff Time
        # We use a tuple (is_not_top_league, kickoff_time) for sorting
        self.matches.sort(key=lambda x: (x.get('league') not in TOP_LEAGUES, x['kickoff']))

        # Generate the Listing
        listing_html = ""
        current_league = ""
        
        for m in self.matches:
            if m['league'] != current_league:
                listing_html += f'<div class="league-header">{m["league"]}</div>'
                current_league = m['league']
            
            m_time = datetime.fromtimestamp(m['kickoff']).strftime('%H:%M')
            m_slug = self.slugify(m['fixture'])
            date_id = datetime.fromtimestamp(m['kickoff']).strftime('%Y%m%d')
            
            listing_html += f'''
            <a href="{DOMAIN}/match/{m_slug}/{date_id}/" class="match-row">
                <div class="match-time">{m_time}</div>
                <div class="match-info">{m['fixture']}</div>
            </a>'''

        # Fill Template
        final_html = home_t.replace("{{DOMAIN}}", DOMAIN)\
                           .replace("{{MATCH_LISTING}}", listing_html)\
                           .replace("{{PAGE_TITLE}}", "Today's Live Football")\
                           .replace("{{WEEKLY_MENU}}", "") # Add menu logic as needed

        with open(os.path.join(OUTPUT_FOLDER, "index.html"), "w", encoding='utf-8') as f:
            f.write(final_html)
            
        logging.info("Build Successful: index.html generated with Top League priority.")

if __name__ == "__main__":
    SoccerGenerator().run()
