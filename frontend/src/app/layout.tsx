import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, Gem, LayoutDashboard, TrendingUp } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lux Arbitrage Intelligence",
  description: "Luxury fashion arbitrage between Vinted and Oskelly",
};

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/brands", label: "Brands", icon: Gem },
  { href: "/rankings", label: "Rankings", icon: TrendingUp },
  { href: "/alerts", label: "Alerts", icon: BarChart3 },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex">
          <aside className="w-64 border-r border-border bg-card/50 p-6 hidden md:flex flex-col gap-8">
            <div>
              <p className="text-xs uppercase tracking-widest text-muted mb-1">Lux Arbitrage</p>
              <h1 className="text-lg font-semibold gradient-text">Intelligence Platform</h1>
            </div>
            <nav className="flex flex-col gap-1">
              {nav.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted hover:text-foreground hover:bg-white/5 transition-colors"
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              ))}
            </nav>
            <div className="mt-auto text-xs text-muted">
              Vinted ↔ Oskelly
              <br />
              MVP · Phase 1
            </div>
          </aside>
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
