import type { Metadata } from "next";
import { Sidebar } from "@/components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlphaRadar — Alternative Data Intelligence",
  description: "Democratizing hedge fund insights with real-time alternative data",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
          try {
            const t = localStorage.getItem('alpharadar-theme');
            if (t === 'light') document.documentElement.classList.remove('dark');
          } catch(e) {}
        `}} />
      </head>
      <body className="flex h-screen overflow-hidden bg-(--color-bg-primary) text-(--color-text-primary) antialiased">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pb-16 md:pb-0">{children}</main>
      </body>
    </html>
  );
}
