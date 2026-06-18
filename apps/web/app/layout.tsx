import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "SanJuan AI",
  description: "Modern Caribbean Intelligence for Puerto Rico.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="nav">
          <div className="container nav-inner">
            <Link className="brand" href="/">
              SanJuan AI
              <span>Modern Caribbean Intelligence</span>
            </Link>
            <nav className="nav-links" aria-label="Main navigation">
              <Link href="/ask">Ask</Link>
              <Link href="/sources">Sources</Link>
              <a href="https://github.com/YannDavidson/sanjuan-ai" target="_blank" rel="noreferrer">
                GitHub
              </a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
