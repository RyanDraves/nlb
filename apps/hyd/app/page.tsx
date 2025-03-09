"use client";
import { useEffect, useState } from "react";

export default function Home() {
  const [progressData, setProgressData] = useState<any[]>([]);

  useEffect(() => {
    async function fetchProgress() {
      const res = await fetch("/api/progress");
      const data = await res.json();
      setProgressData(data);
    }
    fetchProgress();
    const intervalId = setInterval(fetchProgress, 5000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="grid w-[80vw] mx-auto grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)] text-xl">
      <section className="w-full">
        {progressData.map((bar: {
          id: number;
          label: string;
          value: number;
          max_value: number;
          status?: string;
        }) => {
          const fraction =
            bar.max_value && bar.max_value > 0 ? (bar.value / bar.max_value) * 100 : 0;
          return (
            <div key={bar.id} className="my-2">
              <div className="relative w-full bg-gray-900 rounded h-8">
                <div
                  className="bg-blue-600 h-full rounded"
                  style={{ width: `${fraction}%` }}
                />
                <div className="absolute left-2 top-1/2 -translate-y-1/2 text-white">
                  {bar.label} - {bar.value}/{bar.max_value}
                </div>
              </div>
              {bar.status && (
                <div className="text-white mt-1 pl-5">
                  {bar.status}
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
