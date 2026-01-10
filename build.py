import json
import os
from datetime import datetime

# Load your bulk JSON data
with open('matches.json', 'r') as f:
    matches = json.load(f)

# The HTML template for the Match Detail pages 
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="Watch {fixture} live. Full list of official TV channels and broadcast details for {league} on {date}.">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">
    <nav class="bg-[#001529] p-4 text-white"><div class="max-w-4xl mx-auto"><a href="/" class="font-bold">YOSINTV</a></div></nav>
    <main class="max-w-4xl mx-auto p-6">
        <div class="bg-white p-8 rounded-2xl shadow-sm border mb-6">
            <h1 class="text-3xl font-extrabold text-gray-900">{fixture}</h1>
            <p class="text-blue-600 font-bold mt-2">How to Watch Live | TV Channels & Broadcast Details</p>
            <p class="text-gray-500 text-sm">{league} | {date} | {venue}</p>
        </div>
        <div class="bg-white rounded-2xl shadow-sm overflow-hidden border">
            <div class="bg-gray-800 text-white px-6 py-2 text-xs font-bold uppercase">Official Broadcasters</div>
            {tv_list}
        </div>
    </main>
</body>
</html>
"""

def slugify(text):
    return text.lower().replace(" ", "-").replace(".", "").replace("vs", "vs")

# --- GENERATE MATCH PAGES ---
match_links = []
for m in matches:
    dt = datetime.fromtimestamp(m['kickoff'])
    date_path = dt.strftime('%d-%b-%Y').lower()
    date_display = dt.strftime('%d %b %Y')
    
    # Create the folder path: match/team-vs-team/11-jan-2026/
    slug = slugify(m['fixture'])
    folder_path = f"match/{slug}/{date_path}"
    os.makedirs(folder_path, exist_ok=True)

    # Create TV list HTML
    tv_html = ""
    for country in m.get('tv_channels', []):
        pills = "".join([f'<span class="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100 font-semibold">{c}</span>' for c in country['channels']])
        tv_html += f'<div class="p-4 border-b flex flex-col md:flex-row justify-between gap-2"><span class="font-bold text-sm text-gray-700">{country["country"]}</span><div class="flex flex-wrap gap-2">{pills}</div></div>'

    # Fill template and save
    full_html = TEMPLATE.format(
        title=f"{m['fixture']} - How to Watch Live | TV Channels | {date_display}",
        fixture=m['fixture'],
        league=m['league'],
        date=date_display,
        venue=m.get('venue', 'TBA'),
        tv_list=tv_html
    )
    
    with open(f"{folder_path}/index.html", "w") as f:
        f.write(full_html)
    
    # Save link for the home page listing
    match_links.append({
        "fixture": m['fixture'],
        "league": m['league'],
        "url": f"/{folder_path}/",
        "time": dt.strftime('%H:%M'),
        "date": dt.strftime('%Y-%m-%d')
    })

# --- GENERATE HOME PAGE (index.html) ---
home_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Live Football TV Guide - YosinTV</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 font-sans">
    <header class="bg-[#001529] p-6 text-white text-center"><h1 class="text-2xl font-bold">YOSINTV LIVE GUIDE</h1></header>
    <main class="max-w-4xl mx-auto p-6">
        <div class="space-y-4">
"""

# Group match_links by league for the homepage
leagues = {}
for ml in match_links:
    leagues.setdefault(ml['league'], []).append(ml)

for league, m_list in leagues.items():
    home_html += f'<div class="bg-white rounded-xl shadow-sm border overflow-hidden"><div class="bg-gray-100 px-4 py-2 font-bold text-xs uppercase text-gray-600">{league}</div>'
    for match in m_list:
        home_html += f'<a href="{match["url"]}" class="flex justify-between items-center p-4 border-b hover:bg-blue-50 transition"><span class="text-sm font-bold text-blue-900">{match["fixture"]}</span><span class="text-xs font-bold text-gray-400">{match["time"]}</span></a>'
    home_html += '</div>'

home_html += "</main></body></html>"

with open("index.html", "w") as f:
    f.write(home_html)

print("Build Complete!")
