import type { Metadata } from "next";

// Generated path
import "@/tailwind.css";
// Original path (uncomment to use pnpm directly)
// import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "HYD",
  description: "Fancy progress bars",
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
