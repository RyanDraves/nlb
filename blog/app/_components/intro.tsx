import Link from "next/link";

export function Intro() {
  return (
    <section className="flex-col md:flex-row flex items-center md:justify-between mt-16 mb-16 md:mb-12">
      <div className="flex flex-col md:flex-row items-center md:items-end gap-4 md:gap-6">
        <h1 className="text-5xl md:text-8xl font-bold tracking-tighter leading-tight">
          Blog.
        </h1>
        <Link href="/clif" className="text-lg text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-all duration-200 mb-0 md:mb-2 px-3 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-700">
          Over the Clif
        </Link>
      </div>
      <h4 className="text-center md:text-left text-lg mt-5 md:pl-8">
        Ryan's blog of miraculous wonders.
      </h4>
    </section>
  );
}
