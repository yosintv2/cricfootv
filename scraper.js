const fs = require('fs');
const path = require('path');

// A list of real-world browser User-Agents to rotate
const USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
];

function getHeaders() {
    return {
        "User-Agent": USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)],
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "If-None-Match": 'W/"' + Math.random().toString(36).substring(2, 12) + '"' // Randomize Cache tag
    };
}

const getTomorrowDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
};

async function fetchWithStealth(url) {
    try {
        const response = await fetch(url, { headers: getHeaders() });
        if (response.status === 403) {
            console.error(`[!] 403 Forbidden at ${url}. Bot detection is active.`);
            return null;
        }
        return response.ok ? await response.json() : null;
    } catch (e) {
        return null;
    }
}

async function run() {
    const date = getTomorrowDate();
    const fileName = `${date.replace(/-/g, '')}.json`;
    const dir = './date';

    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    console.log(`🚀 Starting Stealth Fetch for: ${date}`);

    // SofaScore often uses the 'inverse' URL for certain regions/servers
    let data = await fetchWithStealth(`https://api.sofascore.com/api/v1/sport/football/scheduled-events/${date}`);
    
    if (!data || !data.events) {
        console.log("[-] Primary feed blocked/empty. Trying Fallback...");
        data = await fetchWithStealth(`https://api.sofascore.com/api/v1/sport/football/scheduled-events/${date}/inverse`);
    }

    if (!data || !data.events || data.events.length === 0) {
        console.error("❌ Still Blocked. GitHub IP is likely blacklisted by SofaScore.");
        process.exit(1);
    }

    const results = data.events.map(ev => ({
        match_id: ev.id,
        kickoff: ev.startTimestamp,
        fixture: `${ev.homeTeam.name} vs ${ev.awayTeam.name}`,
        league: ev.tournament.name
    }));

    fs.writeFileSync(path.join(dir, fileName), JSON.stringify(results, null, 4));
    console.log(`✅ Success! Saved ${results.length} matches to date/${fileName}`);
}

run();
