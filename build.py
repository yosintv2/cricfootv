import json, os, re
from datetime import datetime

# CONFIGURATION
DOMAIN = "https://tv.cricfoot.net" # Change this!

# Load Files
with open('matches.json', 'r') as f: matches = json.load(f)
with open('home_template.html', 'r') as f: home_temp = f.read()
with open('match_template.html', 'r') as f: match_temp = f.read()

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

channel_map, leagues, sitemap_urls = {}, {}, [DOMAIN]

# 1. GENERATE MATCH PAGES
for m in matches:
    dt = datetime.fromtimestamp(m['kickoff'])
    t_str, d_str, iso_d = dt.strftime('%H:%M'), dt.strftime('%d %b %Y'), dt.isoformat()
    venue, league = m.get('venue', 'Global Stadium'), m.get('league', 'Football')
    
    match_slug = slugify(m['fixture'])
    date_path = dt.strftime('%d-%b-%Y').lower()
    rel_path = f"match/{match_slug}/{date_path}"
    os.makedirs(rel_path, exist_ok=True)

    rows_html, top_ch = "", []
    for c in m['tv_channels']:
        btns = ""
        for ch in c['channels']:
            ch_slug = slugify(ch)
            btns += f'<a href="/channel/{ch_slug}/" class="ch-pill">{ch}</a>'
            channel_map.setdefault(ch, []).append(m)
            if ch not in top_ch: top_ch.append(ch)
        rows_html += f'<div class="country-cell">{c["country"]}</div><div class="channel-cell">{btns}</div>'

    # FULL SEO SCHEMA
    schema = f'''
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "SportsEvent",
      "name": "{m['fixture']}",
      "startDate": "{iso_d}",
      "location": {{ "@type": "Place", "name": "{venue}" }},
      "competitor": [{{ "@type": "SportsTeam", "name": "{m['fixture'].split(' vs ')[0]}" }}, {{ "@type": "SportsTeam", "name": "{m['fixture'].split(' vs ')[1]}" }}],
      "description": "Live broadcast guide for {m['fixture']} in {league}."
    }}
    </script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "Where to watch {m['fixture']} live?", "acceptedAnswer": {{ "@type": "Answer", "text": "Live on {', '.join(top_ch[:3])}." }} }}
      ]
    }}
    </script>'''

    page_content = match_temp.replace("{{FIXTURE}}", m['fixture']).replace("{{LEAGUE}}", league) \
                             .replace("{{TIME}}", t_str).replace("{{DATE}}", d_str) \
                             .replace("{{VENUE}}", venue).replace("{{BROADCAST_ROWS}}", rows_html) \
                             .replace("{{TOP_CHANNELS}}", ", ".join(top_ch[:3])) \
                             .replace("{{TITLE}}", f"{m['fixture']} - {league} TV Guide - {d_str}") \
                             .replace("{{SCHEMA}}", schema)
    
    with open(f"{rel_path}/index.html", "w") as f: f.write(page_content)
    sitemap_urls.append(f"{DOMAIN}/{rel_path}/")
    leagues.setdefault(league, []).append({"time": t_str, "date": d_str, "venue": venue, "fixture": m['fixture'], "url": f"/{rel_path}/"})

# 2. GENERATE HOME PAGE
listing_html = ""
for l_name, m_list in leagues.items():
    listing_html += f'<div class="league-card"><div class="bg-slate-100 dark:bg-slate-800 px-4 py-2 text-[10px] font-900 uppercase tracking-widest text-slate-500">{l_name}</div>'
    for match in m_list:
        listing_html += f'''
        <a href="{match["url"]}" class="match-row">
            <div class="flex flex-col min-w-[75px]"><span class="text-sky-500 font-800 text-lg leading-none">{match["time"]}</span><span class="text-[9px] font-bold text-slate-400 uppercase mt-1">{match["date"]}</span></div>
            <div class="ml-4 flex flex-col"><span class="font-bold text-slate-800 dark:text-white text-sm md:text-base">{match["fixture"]}</span><span class="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{match["venue"]} | {l_name}</span></div>
        </a>'''
    listing_html += '</div>'

with open("index.html", "w") as f: f.write(home_temp.replace("{{MATCH_LISTING}}", listing_html))

# 3. GENERATE CHANNEL PAGES
for ch_name, ch_matches in channel_map.items():
    ch_slug = slugify(ch_name)
    path = f"channel/{ch_slug}"
    os.makedirs(path, exist_ok=True)
    cards = "".join([f'<div class="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl mb-4 shadow-sm"><p class="text-sky-500 font-bold">{m["fixture"]}</p><p class="text-xs text-slate-400 uppercase font-bold">{m["league"]} | {datetime.fromtimestamp(m["kickoff"]).strftime("%H:%M")}</p></div>' for m in ch_matches])
    ch_html = home_temp.replace("{{MATCH_LISTING}}", f'<h1 class="text-3xl font-800 mb-8">Matches on {ch_name}</h1>{cards}')
    with open(f"{path}/index.html", "w") as f: f.write(ch_html)
    sitemap_urls.append(f"{DOMAIN}/{path}/")

# 4. GENERATE SITEMAP
xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for url in sitemap_urls: xml += f'<url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
xml += '</urlset>'
with open("sitemap.xml", "w") as f: f.write(xml)

print("Build Complete!")
