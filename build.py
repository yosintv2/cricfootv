import json, os, re
from datetime import datetime

# CONFIG
DOMAIN = "https://tv.cricfoot.net" # Change this!

with open('matches.json', 'r') as f:
    matches = json.load(f)
with open('match_template.html', 'r') as f:
    match_temp = f.read()

def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

channel_map = {} # To track which matches are on which channel

# 1. PROCESS MATCHES
for m in matches:
    dt = datetime.fromtimestamp(m['kickoff'])
    d_display = dt.strftime('%d %b %Y')
    d_path = dt.strftime('%d-%b-%Y').lower()
    slug = slugify(m['fixture'])
    rel_path = f"match/{slug}/{d_path}"
    os.makedirs(rel_path, exist_ok=True)

    rows_html = ""
    top_channels = []
    
    for country in m.get('tv_channels', []):
        c_links = ""
        for ch in country['channels']:
            ch_slug = slugify(ch)
            c_links += f'<a href="/channel/{ch_slug}/" class="channel-link">{ch}</a>'
            # Update channel map for SEO cross-linking
            channel_map.setdefault(ch, []).append(m)
            if len(top_channels) < 3: top_channels.append(ch)

        rows_html += f'<div class="country-col">{country["country"]}</div><div class="channel-col">{c_links}</div>'

    # Build FAQ Schema
    faq_schema = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{ "@type": "Question", "name": "Where to watch {m['fixture']} live?", "acceptedAnswer": {{ "@type": "Answer", "text": "Official broadcasters include {', '.join(top_channels)}." }} }}
      ]
    }}
    </script>
    """

    # Inject into template
    page = match_temp.replace("{{TITLE}}", f"{m['fixture']} - TV Channels & Live Stream | {d_display}") \
                     .replace("{{FIXTURE}}", m['fixture']) \
                     .replace("{{LEAGUE}}", m['league']) \
                     .replace("{{DATE}}", d_display) \
                     .replace("{{TIME}}", dt.strftime('%H:%M')) \
                     .replace("{{ISO_DATE}}", dt.isoformat()) \
                     .replace("{{VENUE}}", m.get('venue', 'TBA')) \
                     .replace("{{BROADCAST_ROWS}}", rows_html) \
                     .replace("{{TOP_CHANNELS}}", ", ".join(top_channels)) \
                     .replace("{{FAQ_SCHEMA}}", faq_schema)

    with open(f"{rel_path}/index.html", "w") as f:
        f.write(page)

# 2. GENERATE CHANNEL PAGES (Crucial for SEO)
for ch_name, m_list in channel_map.items():
    ch_slug = slugify(ch_name)
    path = f"channel/{ch_slug}"
    os.makedirs(path, exist_ok=True)
    
    ch_html = f"<html><head><title>Matches on {ch_name} - Live Guide</title><script src='https://cdn.tailwindcss.com'></script></head><body class='bg-gray-100 p-8'>"
    ch_html += f"<h1 class='text-2xl font-bold mb-6'>Upcoming Matches on {ch_name}</h1><div class='grid gap-4'>"
    for match in m_list:
        ch_html += f"<div class='p-4 bg-white border rounded shadow-sm'><p class='font-bold'>{match['fixture']}</p><p class='text-xs text-gray-500'>{match['league']}</p></div>"
    ch_html += "</div><a href='/' class='mt-6 block text-blue-600'>Back to Home</a></body></html>"
    
    with open(f"{path}/index.html", "w") as f:
        f.write(ch_html)
