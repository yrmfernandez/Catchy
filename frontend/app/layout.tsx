import type { Metadata } from "next";
import "./globals.css";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "Catchy",
  description: "Explainable phishing detection — forensics + ML + LLM analyst.",
};

// Runs before first paint: resolves the saved theme (or the OS preference) and
// stamps data-theme on <html> so the page never flashes the wrong colours.
const themeScript = `(function(){try{var t=localStorage.getItem('theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.dataset.theme=t;}catch(e){document.documentElement.dataset.theme='dark';}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <header className="topbar">
          <Logo />
          <ThemeToggle />
        </header>
        {children}
      </body>
    </html>
  );
}
