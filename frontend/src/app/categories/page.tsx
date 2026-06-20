import { api, type CategoryAnalysisRow } from "@/lib/api";
import { formatEur } from "@/lib/utils";
import Link from "next/link";

export const dynamic = "force-dynamic";

const CATEGORY_EMOJI: Record<string, string> = {
  bags: "👜",
  shoes: "👟",
  outerwear: "🧥",
  knitwear: "🧶",
  denim: "👖",
  accessories: "💍",
  jewelry: "💎",
  eyewear: "🕶️",
};

function SpreadBar({ spread, max }: { spread: number; max: number }) {
  const pct = Math.min(100, (spread / max) * 100);
  return (
    <div className="w-full bg-white/5 rounded-full h-1.5 mt-1">
      <div
        className="bg-buy rounded-full h-1.5 transition-all"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export default async function CategoriesPage() {
  let rows: CategoryAnalysisRow[] = [];
  let error: string | null = null;

  try {
    rows = await api.getCategoryAnalysis();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load";
  }

  const maxSpread = rows.reduce((m, r) => Math.max(m, r.spread_eur), 1);

  // Group by category for the summary cards
  const byCategory: Record<string, CategoryAnalysisRow[]> = {};
  for (const row of rows) {
    if (!byCategory[row.category]) byCategory[row.category] = [];
    byCategory[row.category].push(row);
  }

  const categorySummary = Object.entries(byCategory)
    .map(([cat, items]) => ({
      category: cat,
      avgSpread: items.reduce((s, r) => s + r.spread_eur, 0) / items.length,
      maxSpread: Math.max(...items.map((r) => r.spread_eur)),
      count: items.length,
    }))
    .sort((a, b) => b.avgSpread - a.avgSpread);

  return (
    <div className="p-8 space-y-10">
      <header>
        <h1 className="text-3xl font-bold">Category Intelligence</h1>
        <p className="text-muted mt-1">
          Average prices per brand &amp; category on Vinted vs Oskelly — ranked by price spread
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-watch/30 bg-watch/10 p-4 text-sm">{error}</div>
      )}

      {/* Category summary cards */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Most Profitable Categories</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categorySummary.map(({ category, avgSpread, maxSpread: ms, count }) => (
            <div key={category} className="card-glow rounded-xl p-4 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xl">{CATEGORY_EMOJI[category] ?? "📦"}</span>
                <p className="font-semibold capitalize">{category}</p>
              </div>
              <p className="text-xs text-muted">{count} brand{count !== 1 ? "s" : ""}</p>
              <p className="text-buy font-mono font-semibold">{formatEur(avgSpread)} avg spread</p>
              <p className="text-xs text-muted">Best: {formatEur(ms)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Full ranking table */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Brand × Category Spread Ranking</h2>
        <div className="card-glow rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-muted">
              <tr>
                <th className="text-left p-3">#</th>
                <th className="text-left p-3">Brand</th>
                <th className="text-left p-3">Category</th>
                <th className="text-right p-3">Vinted avg</th>
                <th className="text-right p-3">Oskelly avg</th>
                <th className="text-right p-3">Spread</th>
                <th className="text-right p-3 hidden md:table-cell">%</th>
                <th className="text-right p-3 hidden lg:table-cell">Bar</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={`${row.brand_slug}-${row.category}`} className="border-t border-border hover:bg-white/5">
                  <td className="p-3 text-muted font-mono">{i + 1}</td>
                  <td className="p-3">
                    <Link href={`/brands/${row.brand_slug}`} className="hover:text-accent">
                      {row.brand}
                    </Link>
                  </td>
                  <td className="p-3 text-muted capitalize">
                    {CATEGORY_EMOJI[row.category] ?? ""} {row.category}
                  </td>
                  <td className="p-3 text-right font-mono text-muted">{formatEur(row.vinted_avg_eur)}</td>
                  <td className="p-3 text-right font-mono">{formatEur(row.oskelly_avg_eur)}</td>
                  <td className="p-3 text-right font-mono text-buy font-semibold">
                    {formatEur(row.spread_eur)}
                  </td>
                  <td className="p-3 text-right text-muted hidden md:table-cell">
                    +{row.spread_pct.toFixed(0)}%
                  </td>
                  <td className="p-3 hidden lg:table-cell w-32">
                    <SpreadBar spread={row.spread_eur} max={maxSpread} />
                  </td>
                </tr>
              ))}
              {rows.length === 0 && !error && (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-muted">
                    No data yet — run the data pipeline first.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
