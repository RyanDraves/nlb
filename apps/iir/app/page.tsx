"use client";
import { useEffect, useState } from "react";

export default function Home() {
  const [raining, setRaining] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchWeather() {
    setError(null);
    try {
      const res = await fetch('/api/weather');
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        setRaining(null);
      } else {
        setRaining(data.raining);
      }
    } catch (err: any) {
      setError(err.message);
      setRaining(null);
    }
  }

  useEffect(() => {
    fetchWeather();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#222222] text-white p-4">
      <h1 className="text-4xl mb-6">Is it raining in Boulder, CO?</h1>
      {error ? (
        <p className="text-red-500 mb-4">{error}</p>
      ) : raining === null ? (
        <p className="mb-4">Loading...</p>
      ) : raining ? (
        <p className="text-blue-400 mb-4">Yes, it is raining.</p>
      ) : (
        <p className="text-yellow-400 mb-4">No, it is not raining.</p>
      )}
      <button
        onClick={fetchWeather}
        className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition-colors"
      >
        Refresh
      </button>
    </div>
  );
}
