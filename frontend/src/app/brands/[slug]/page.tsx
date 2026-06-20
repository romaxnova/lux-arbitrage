import { api } from "@/lib/api";
import { formatEur, formatPct, recColor } from "@/lib/utils";

export default async function BrandDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const data = await api.getBrand(slug);

  return (
    <div className="p-8 max-w-4xl space-y-8">
      <header>
        <p className="text-sm text-muted capitalize">{data.brand.tier}</p>
        <h1 className="text-3xl font-bold">{data.brand.name}</h1>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Stat label="Avg Vinted Price" value={formatEur(data.avg_vinted_price_eur)} />
        <Stat label="Avg Oskelly Price" value={formatEur(data.avg_oskelly_price_eur)} />
        <Stat label="Median Spread" value={formatEur(data.median_spread_eur)} />
        <Stat label="Median ROI" value={formatPct(data.median_roi)} />
        <Stat label="Active Opportunities" value={String(data.active_opportunities)} />
        <Stat label="Demand Trend" value={data.demand_trend} />
      </div>

      <section className="card-glow rounded-xl p-6">
        <h2 className="font-semibold mb-4">Most Profitable Categories</h2>
        <div className="space-y-3">
          {data.top_categories.map((cat) => (
            <div key={cat.category} className="flex justify-between text-sm">
              <span className="capitalize">{cat.category}</span>
              <span className="font-mono">{formatPct(cat.median_roi)} · {cat.opportunity_count} opps</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="card-glow rounded-xl p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-xl font-semibold font-mono mt-1">{value}</p>
    </div>
  );
}
