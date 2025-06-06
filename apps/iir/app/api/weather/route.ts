import { NextResponse } from 'next/server';
import fs from 'fs';


let apiKey = process.env.OPENWEATHER_API_KEY;
if (!apiKey && process.env.OPENWEATHER_API_KEY_FILE) {
    try {
        apiKey = fs.readFileSync(process.env.OPENWEATHER_API_KEY_FILE, 'utf8').trim();
        apiKey = apiKey.trim();
    } catch (err) {
        console.error(`Error reading OPENWEATHER_API_KEY_FILE: ${err}`);
    }
}

export async function GET(): Promise<NextResponse> {
    if (!apiKey) {
        return NextResponse.json({ error: 'API key not configured' }, { status: 500 });
    }
    const url = new URL('https://api.openweathermap.org/data/2.5/weather');
    url.searchParams.set('lat', '40.0150');
    url.searchParams.set('lon', '-105.2705');
    url.searchParams.set('appid', apiKey);
    url.searchParams.set('units', 'metric');

    try {
        const res = await fetch(url.toString(), { next: { revalidate: 300 } });
        if (!res.ok) {
            return NextResponse.json({ error: 'Failed to fetch weather' }, { status: res.status });
        }
        const data = await res.json();
        const raining = Array.isArray(data.weather) && data.weather.some((w: any) =>
            w.main.toLowerCase().includes('rain') || w.description.toLowerCase().includes('rain')
        );
        return NextResponse.json({ raining });
    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 });
    }
}
