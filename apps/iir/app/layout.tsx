import type { Metadata } from "next";

// TODO: Figure out a way to allow for both
// Generated path
import "@/tailwind.css";
// Original path (uncomment to use pnpm directly)
// import "@/styles/globals.css";

export const metadata: Metadata = {
  title: 'Is it raining?',
  description: 'Check if it is raining in Boulder, CO',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`bg-[#222222] antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
