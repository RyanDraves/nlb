import Container from "@/app/_components/container";
import Header from "@/app/_components/header";
import { PostTitle } from "@/app/_components/post-title";
import Globe from "@/app/satellites/globe";
import { missions, splitBlurb } from "@/app/satellites/data/missions";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Satellites | Ryan's Bizarre Blog",
  description:
    "An interactive 3D view of the Earth and the orbits of the satellites I've worked on.",
  openGraph: {
    title: "Satellites | Ryan's Bizarre Blog",
    description:
      "An interactive 3D view of the Earth and the orbits of the satellites I've worked on.",
  },
};

export default function SatellitesPage() {
  const missionList = Object.values(missions);

  return (
    <main>
      <Container>
        <Header />
        <article>
          <PostTitle>Satellites</PostTitle>

          <div className="prose prose-lg dark:prose-invert max-w-none mb-10">
            <p className="text-xl leading-relaxed text-gray-700 dark:text-gray-300">
              The satellites I've worked on, traced around an interactive Earth.
              Drag to rotate, scroll to zoom, and hover or tap a marker to read
              about each mission.
            </p>
          </div>

          {/* 3D view */}
          <div className="mb-8 h-[70vh] w-full overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700">
            <Globe />
          </div>

          {/* Legend */}
          <section className="mb-20">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {missionList.map((m) => {
                const blurb = splitBlurb(m.blurb);
                return (
                  <div
                    key={m.noradId}
                    className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="font-bold text-gray-900 dark:text-white">
                        {m.name || `NORAD ${m.noradId}`}
                      </h3>
                      <span
                        className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                          m.status === "deorbited"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                            : "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200"
                        }`}
                      >
                        {m.orbit} · {m.status}
                      </span>
                    </div>
                    {m.role && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {m.role}
                      </p>
                    )}
                    {blurb.text && (
                      <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                        {blurb.text}
                      </p>
                    )}
                    {blurb.url && (
                      <a
                        href={blurb.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-block text-sm text-teal-600 hover:underline dark:text-teal-400"
                      >
                        Learn more →
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </article>
      </Container>
    </main>
  );
}
