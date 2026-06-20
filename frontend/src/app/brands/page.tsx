import Link from "next/link";
import { api } from "@/lib/api";
import { formatEur, formatPct } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function BrandsPage() {
  let brands: Awaited<ReturnType<typeof api.getBrands>> = [];
  try {
    brands = await api.getBrands();
  } catch {
    /* empty */
  }

  const analytics = await Promise.all(
    brands.slice(0, 8).map(async (b) => {
      try {
        return await api.getBrand(b.slug);
      } catch {
        return null;
      }
    })
  );

  return (
    <div className="p-8 space-y-8">
      <header>
        <h1 className="text-3xl font-bold">Brand Intelligence</h1>
        <p className="text-muted mt-1">Cross-market pricing, spreads, and ROI by brand</p>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        {analytics.filter(Boolean).map((a) => a && (
          <Link
            key={a.brand.slug}
            href={`/brands/${a.brand.slug}`}
            className="card-glow rounded-xl p-6 hover:border-accent/30 transition-colors block"
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-semibold">{a.brand.name}</h2>
                <p className="text-xs text-muted uppercase">{a.brand.tier}</p>
              </div>
              <span className="text-xs px-2 py-1 rounded bg-accent/10 text-accent border border-accent/20">
                {a.active_opportunities} opps
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted text-xs">Avg Vinted</p>
                <p className="font-mono">{formatEur(a.avg_vinted_price_eur)}</p>
              </div>
              <div>
                <p className="text-muted text-xs">Avg Oskelly</p>
                <p className="font-mono">{formatEur(a.avg_oskelly_price_eur)}</p>
              </div>
              <div>
                <p className="text-muted text-xs">Median Spread</p>
                <p className="font-mono text-buy">{formatEur(a.median_spread_eur)}</p>
              </div>
              <div>
                <p className="text-muted text-xs">Median ROI</p>
                <p className="font-mono">{formatPct(a.median_roi)}</p>
              </div>
            </div>
            <p className="text-xs text-muted mt-4">
              Demand: {a.demand_trend} · Liquidity: {a.liquidity_trend}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
