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
    url.searchParams.set('lat', '40.01003');
    url.searchParams.set('lon', '-105.24389');
    url.searchParams.set('units', 'metric');

    // Log the URL before the API key is added
    console.log(`Fetching weather data from: ${url.toString()}`);

    url.searchParams.set('appid', apiKey);

    try {
        const res = await fetch(url.toString(), { next: { revalidate: 300 } });
        if (!res.ok) {
            return NextResponse.json({ error: 'Failed to fetch weather' }, { status: res.status });
        }
        const data = await res.json();
        // Log the response data for debugging
        console.log('Weather data received:', data);
        const raining = Array.isArray(data.weather) && data.weather.some((w: any) =>
            w.main.toLowerCase().includes('rain') || w.description.toLowerCase().includes('rain')
        );
        return NextResponse.json({ raining });
    } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 500 });
    }
}
