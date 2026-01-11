const fs = require('fs');
const path = require('path');

const HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
};

const getTomorrowDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1); // Get tomorrow
    return d.toISOString().split('T')[0];
};

async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { headers: HEADERS });
            if (response.ok) return await response.json();
            if (response.status === 403) console.log(`[403] Blocked on: ${url}`);
        } catch (e) {
            console.log(`Error fetching ${url}: ${e.message}`);
        }
        await new Promise(r => setTimeout(r, 2000)); // Wait 2s before retry
    }
    return null;
}

async function run() {
    const date = getTomorrowDate();
    const fileName = date.replace(/-/g, '') + '.json';
    const dir = './date';
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    console.log(`Targeting Date: ${date}`);
    
    // Attempt 1: Standard endpoint
    let data = await fetchWithRetry(`https://api.sofascore.com/api/v1/sport/football/scheduled-events/${date}`);
    
    // Attempt 2: Inverse endpoint (Fallback)
    if (!data || !data.events || data.events.length === 0) {
        console.log("Standard feed empty, trying inverse...");
        data = await fetchWithRetry(`https://api.sofascore.com/api/v1/sport/football/scheduled-events/${date}/inverse`);
    }

    if (!data || !data.events || data.events.length === 0) {
        console.log("❌ CRITICAL: No events found on either endpoint. SofaScore may have blocked this IP.");
        return;
    }

    const events = data.events;
    console.log(`Found ${events.length} events. Fetching details...`);

    const results = [];
    // We only process the first 30 to stay under the radar for now
    for (const event of events.slice(0, 30)) {
        const tvData = await fetchWithRetry(`https://api.sofascore.com/api/v1/tv/event/${event.id}/country-channels`);
        
        let broadcasters = [];
        if (tvData?.countryChannels) {
            for (const code of Object.keys(tvData.countryChannels)) {
                const channels = await Promise.all(tvData.countryChannels[code].map(async (chId) => {
                    const ch = await fetchWithRetry(`https://api.sofascore.com/api/v1/tv/channel/${chId}/schedule`);
                    return ch?.channel?.name || null;
                }));
                const valid = channels.filter(c => c !== null);
                if (valid.length > 0) broadcasters.push({ country: code, channels: valid });
            }
        }

        results.push({
            match_id: event.id,
            kickoff: event.startTimestamp,
            fixture: `${event.homeTeam.name} vs ${event.awayTeam.name}`,
            league: event.tournament.name,
            tv_channels: broadcasters
        });
        
        console.log(`✓ Scraped: ${event.homeTeam.name}`);
        await new Promise(r => setTimeout(r, 1000)); // Be gentle
    }

    fs.writeFileSync(path.join(dir, fileName), JSON.stringify(results, null, 4));
    console.log(`✅ Success! Saved to date/${fileName}`);
}

run();
