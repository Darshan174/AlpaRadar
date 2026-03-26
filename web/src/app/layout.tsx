import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlphaRadar — Alternative Data Intelligence",
  description: "Alternative data intelligence workspace",
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
      <body className="bg-(--color-bg-primary) text-(--color-text-primary) antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
