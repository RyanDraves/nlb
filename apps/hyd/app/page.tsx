"use client";
import { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHourglassEnd, faTrash } from "@fortawesome/free-solid-svg-icons";

export default function Home() {
  const [progressData, setProgressData] = useState<any[]>([]);

  async function fetchProgress() {
    const res = await fetch("/api/progress");
    const data = await res.json();
    setProgressData(data);
  }

  useEffect(() => {
    fetchProgress();
    const intervalId = setInterval(fetchProgress, 5000);
    return () => clearInterval(intervalId);
  }, []);

  function handleDelete(id: number) {
    fetch(`/api/progress/${id}`, { method: "DELETE" })
      .then(() => fetchProgress())
      .catch(console.error);
  }

  return (
    <div className="grid w-[80vw] mx-auto grid-rows-[auto_1fr] items-start justify-items-center min-h-screen p-8 pb-20 gap-4">
      <header className="w-full flex items-center justify-start text-white text-xl">
        <FontAwesomeIcon icon={faHourglassEnd} className="mr-2" />
        HYD
      </header>
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
            <div key={bar.id} className="mb-4 p-2 bg-gray-800 rounded">
              <div className="flex items-center gap-2">
                <div className="relative flex-1 bg-gray-900 rounded h-8">
                  <div
                    className="bg-blue-600 h-full rounded"
                    style={{ width: `${fraction}%` }}
                  />
                  <div className="absolute left-2 top-1/2 -translate-y-1/2 text-white">
                    {bar.label} - {bar.value}/{bar.max_value}
                  </div>
                </div>
                <FontAwesomeIcon
                  icon={faTrash}
                  className="cursor-pointer text-white p-1 rounded hover:bg-red-600 transition-colors"
                  onClick={() => handleDelete(bar.id)}
                />
              </div>
              {bar.status && (
                <div className="text-white mt-2 px-2">
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
