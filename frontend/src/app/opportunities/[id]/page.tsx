import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { formatEur, formatPct, recColor } from "@/lib/utils";
import { ScoreBar } from "@/components/score-bar";

export default async function OpportunityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let opp;
  try {
    opp = await api.getOpportunity(id);
  } catch {
    notFound();
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <Link href="/" className="text-sm text-muted hover:text-foreground">← Back to dashboard</Link>

      <header className="flex flex-col md:flex-row gap-6">
        <div className="relative w-full md:w-80 h-80 rounded-xl overflow-hidden bg-white/5 shrink-0">
          {opp.purchase_listing.image_urls[0] && (
            <Image src={opp.purchase_listing.image_urls[0]} alt={opp.purchase_listing.title} fill className="object-cover" />
          )}
        </div>
        <div className="flex-1 space-y-4">
          <div className="flex items-start gap-3">
            <span className={`text-sm font-semibold px-3 py-1 rounded border ${recColor(opp.recommendation)}`}>
              {opp.recommendation}
            </span>
            <span className="text-sm font-mono text-muted">Score {opp.opportunity_score.toFixed(1)}</span>
          </div>
          <div>
            <p className="text-sm text-muted">{opp.brand.name} · {opp.purchase_listing.category}</p>
            <h1 className="text-2xl font-bold mt-1">{opp.purchase_listing.title}</h1>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Metric label="Purchase Cost" value={formatEur(opp.purchase_cost_eur)} />
            <Metric label="Expected Sale" value={formatEur(opp.expected_sale_price_eur)} />
            <Metric label="Gross Profit" value={formatEur(opp.gross_profit_eur)} highlight />
            <Metric label="ROI" value={formatPct(opp.roi)} highlight />
          </div>
          <div className="flex gap-3">
            <a href={opp.purchase_listing.url} target="_blank" rel="noopener" className="text-sm text-accent hover:underline">
              View on Vinted →
            </a>
            <a href={opp.sale_listing.url} target="_blank" rel="noopener" className="text-sm text-accent hover:underline">
              View on Oskelly →
            </a>
          </div>
        </div>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        <section className="card-glow rounded-xl p-6 space-y-4">
          <h2 className="font-semibold">Score Breakdown</h2>
          <ScoreBar label="ROI Score" value={opp.roi_score} />
          <ScoreBar label="Demand Score" value={opp.demand_score} />
          <ScoreBar label="Liquidity Score" value={opp.liquidity_score} />
          <ScoreBar label="Price Gap Score" value={opp.price_gap_score} />
          <ScoreBar label="Risk Score" value={opp.risk_score} danger />
          <p className="text-xs text-muted pt-2">Match confidence: {opp.match_confidence.toFixed(1)}%</p>
        </section>

        <section className="card-glow rounded-xl p-6 space-y-4">
          <h2 className="font-semibold">Purchase Cost Breakdown</h2>
          {Object.entries(opp.cost_breakdown).map(([key, val]) => (
            <div key={key} className="flex justify-between text-sm">
              <span className="text-muted capitalize">{key.replace(/_/g, " ")}</span>
              <span className="font-mono">{formatEur(val)}</span>
            </div>
          ))}
          <div className="border-t border-border pt-3 flex justify-between font-semibold">
            <span>Net Profit (after seller fees)</span>
            <span className="text-buy">{formatEur(opp.net_profit_eur)}</span>
          </div>
        </section>
      </div>

      <section className="card-glow rounded-xl p-6">
        <h2 className="font-semibold mb-4">Matching Oskelly Listing</h2>
        <div className="flex gap-4 items-center">
          <div className="relative w-20 h-20 rounded-lg overflow-hidden bg-white/5">
            {opp.sale_listing.image_urls[0] && (
              <Image src={opp.sale_listing.image_urls[0]} alt="" fill className="object-cover" />
            )}
          </div>
          <div>
            <p className="font-medium">{opp.sale_listing.title}</p>
            <p className="text-sm text-muted">
              {formatEur(opp.sale_listing.price_eur)} · {opp.sale_listing.condition} · Size {opp.sale_listing.size_normalized || "N/A"}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg bg-white/5 p-3">
      <p className="text-xs text-muted">{label}</p>
      <p className={`text-lg font-semibold font-mono ${highlight ? "text-buy" : ""}`}>{value}</p>
    </div>
  );
}
