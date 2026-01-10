import json, os, re
from datetime import datetime

DOMAIN = "https://tv.cricfoot.net" # Change this!

# Templates Loading
with open('matches.json', 'r') as f: matches = json.load(f)
with open('home_template.html', 'r') as f: home_temp = f.read()
with open('match_template.html', 'r') as f: match_temp = f.read()

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

channel_map = {}
leagues = {}
sitemap_urls = [DOMAIN]

for m in matches:
    dt = datetime.fromtimestamp(m['kickoff'])
    time_str, date_str, iso_date = dt.strftime('%H:%M'), dt.strftime('%d %b %Y'), dt.isoformat()
    venue = m.get('venue', 'Global Stadium')
    league = m.get('league', 'Football')
    slug = f"match/{slugify(m['fixture'])}/{dt.strftime('%d-%b-%Y').lower()}"
    os.makedirs(slug, exist_ok=True)

    # Broadcast Table & Channel Mapping
    rows, top_ch = "", []
    for c in m['tv_channels']:
        btns = ""
        for ch in c['channels']:
            btns += f'<a href="/channel/{slugify(ch)}/" class="ch-link">{ch}</a>'
            channel_map.setdefault(ch, []).append(m)
            if ch not in top_ch: top_ch.append(ch)
        rows += f'<div class="country-box">{c["country"]}</div><div class="channel-box">{btns}</div>'

    # FULL SCHEMA DATA (SportsEvent + FAQ)
    schema = f'''
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "SportsEvent",
      "name": "{m['fixture']}",
      "startDate": "{iso_date}",
      "location": {{ "@type": "Place", "name": "{venue}" }},
      "competitor": [
        {{ "@type": "SportsTeam", "name": "{m['fixture'].split(' vs ')[0]}" }},
        {{ "@type": "SportsTeam", "name": "{m['fixture'].split(' vs ')[1]}" }}
      ],
      "subEvent": {{
        "@type": "BroadcastEvent",
        "name": "Live Broadcast of {m['fixture']}",
        "publishedOn": {{ "@type": "BroadcastService", "name": "{', '.join(top_ch[:2])}" }}
      }}
    }}
    </script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "How can I watch {m['fixture']} live?", "acceptedAnswer": {{ "@type": "Answer", "text": "You can watch {m['fixture']} on {', '.join(top_ch[:3])}." }} }},
        {{ "@type": "Question", "name": "What time is kickoff for {m['fixture']}?", "acceptedAnswer": {{ "@type": "Answer", "text": "Kickoff is at {time_str} on {date_str} at {venue}." }} }}
      ]
    }}
    </script>
    '''

    # Build Page
    page = match_temp.replace("{{FIXTURE}}", m['fixture']).replace("{{LEAGUE}}", league) \
                     .replace("{{TIME}}", time_str).replace("{{DATE}}", date_str) \
                     .replace("{{VENUE}}", venue).replace("{{BROADCAST_ROWS}}", rows) \
                     .replace("{{TOP_CHANNELS}}", ", ".join(top_ch[:3])) \
                     .replace("{{SCHEMA}}", schema)
    
    with open(f"{slug}/index.html", "w") as f: f.write(page)
    sitemap_urls.append(f"{DOMAIN}/{slug}/")
    leagues.setdefault(league, []).append({"time": time_str, "date": date_str, "venue": venue, "fixture": m['fixture'], "url": f"/{slug}/"})

# Finalize Home and Channel pages... (Omitted for brevity, use previous logic)

# AUTO SITEMAP GENERATION
sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
for url in sitemap_urls: sitemap += f'<url><loc>{url}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>'
sitemap += '</urlset>'
with open("sitemap.xml", "w") as f: f.write(sitemap)
