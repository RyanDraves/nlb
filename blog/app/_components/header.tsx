import Link from "next/link";

const Header = () => {
  return (
    <header className="mb-20 mt-8">
      <h2 className="text-2xl md:text-4xl font-bold tracking-tight md:tracking-tighter leading-tight flex items-center gap-6">
        <div className="flex items-center">
          <Link href="/" className="hover:underline">
            Blog
          </Link>
          .
        </div>
        <Link href="/clif" className="text-lg text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-all duration-200 px-3 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-700">
          Over the Clif
        </Link>
      </h2>
    </header>
  );
};

export default Header;
