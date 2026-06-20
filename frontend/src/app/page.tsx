import Link from "next/link";
import { api } from "@/lib/api";
import { formatEur, formatPct, recColor } from "@/lib/utils";
import { OpportunityCard } from "@/components/opportunity-card";
import { StatCard } from "@/components/stat-card";
import { RefreshButton } from "@/components/refresh-button";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let stats = { active_listings: 0, opportunities: 0, matches: 0, buy_recommendations: 0 };
  let opportunities: Awaited<ReturnType<typeof api.getOpportunities>> = { items: [], total: 0, page: 1, page_size: 20 };
  let topRoi: Awaited<ReturnType<typeof api.getRankings>> = [];
  let error: string | null = null;

  try {
    [stats, opportunities, topRoi] = await Promise.all([
      api.getStats(),
      api.getOpportunities({ sort: "score", page_size: "12", min_profit: "250" }),
      api.getRankings("highest_roi"),
    ]);
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to connect to API";
  }

  return (
    <div className="p-8 space-y-8">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted mb-1">What should I buy today?</p>
          <h1 className="text-3xl font-bold tracking-tight">Opportunity Dashboard</h1>
        </div>
        <RefreshButton />
      </header>

      {error && (
        <div className="rounded-lg border border-watch/30 bg-watch/10 p-4 text-sm">
          API unavailable — run the backend locally or set <code className="text-xs">NEXT_PUBLIC_API_URL</code> on Vercel. {error}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Active Listings" value={stats.active_listings.toLocaleString()} />
        <StatCard label="Matches" value={stats.matches.toLocaleString()} />
        <StatCard label="Opportunities" value={stats.opportunities.toLocaleString()} />
        <StatCard label="BUY Signals" value={stats.buy_recommendations.toLocaleString()} accent />
      </div>

      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">Best Opportunities Right Now</h2>
            <p className="text-xs text-muted mt-0.5">Filtered: gross profit &gt; €250</p>
          </div>
          <Link href="/rankings" className="text-sm text-accent hover:underline">
            All rankings →
          </Link>
        </div>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {opportunities.items.map((opp) => (
            <OpportunityCard key={opp.id} opportunity={opp} />
          ))}
          {opportunities.items.length === 0 && !error && (
            <p className="text-muted col-span-full">No opportunities yet. Run the data pipeline.</p>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Highest ROI</h2>
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-muted">
              <tr>
                <th className="text-left p-3">Product</th>
                <th className="text-left p-3">Brand</th>
                <th className="text-right p-3">Buy</th>
                <th className="text-right p-3">Sell</th>
                <th className="text-right p-3">Profit</th>
                <th className="text-right p-3">ROI</th>
                <th className="text-right p-3">Rec</th>
              </tr>
            </thead>
            <tbody>
              {topRoi.map((opp) => (
                <tr key={opp.id} className="border-t border-border hover:bg-white/5">
                  <td className="p-3">
                    <Link href={`/opportunities/${opp.id}`} className="hover:text-accent">
                      {opp.purchase_listing.title.slice(0, 40)}…
                    </Link>
                  </td>
                  <td className="p-3 text-muted">{opp.brand.name}</td>
                  <td className="p-3 text-right">{formatEur(opp.purchase_cost_eur)}</td>
                  <td className="p-3 text-right">{formatEur(opp.expected_sale_price_eur)}</td>
                  <td className="p-3 text-right text-buy">{formatEur(opp.gross_profit_eur)}</td>
                  <td className="p-3 text-right font-mono">{formatPct(opp.roi)}</td>
                  <td className="p-3 text-right">
                    <span className={`text-xs px-2 py-0.5 rounded border ${recColor(opp.recommendation)}`}>
                      {opp.recommendation}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
