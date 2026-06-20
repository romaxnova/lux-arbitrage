import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { formatEur, formatPct, recColor, firstImage } from "@/lib/utils";
import { ScoreBar } from "@/components/score-bar";
import { PostToOskelly } from "@/components/post-to-oskelly";

export const dynamic = "force-dynamic";

export default async function OpportunityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let opp;
  try {
    opp = await api.getOpportunity(id);
  } catch {
    notFound();
  }

  const sellImg = firstImage(opp.sale_listing.image_urls);
  const buyImg = firstImage(opp.purchase_listing.image_urls);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <Link href="/" className="text-sm text-muted hover:text-foreground">← Back to dashboard</Link>

      <header className="flex flex-col md:flex-row gap-6">
        {/* Both listing images side by side */}
        <div className="flex gap-3 shrink-0">
          <div className="space-y-1 text-center">
            <div className="relative w-44 h-44 rounded-xl overflow-hidden bg-white/5">
              {buyImg ? (
                <Image src={buyImg} alt={opp.purchase_listing.title} fill className="object-cover" unoptimized />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-1">
                  <span className="text-2xl">🛍</span>
                  <span className="text-xs text-muted text-center px-2">Search on Vinted</span>
                </div>
              )}
            </div>
            <a
              href={opp.purchase_listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs px-3 py-1 rounded bg-white/5 border border-border text-muted hover:text-foreground transition-colors"
            >
              🛍 Buy on Vinted →
            </a>
          </div>

          <div className="flex items-center text-muted text-xl font-bold">→</div>

          <div className="space-y-1 text-center">
            <div className="relative w-44 h-44 rounded-xl overflow-hidden bg-white/5">
              {sellImg ? (
                <Image src={sellImg} alt={opp.sale_listing.title} fill className="object-cover" unoptimized />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-1">
                  <span className="text-2xl">💰</span>
                  <span className="text-xs text-muted">Oskelly listing</span>
                </div>
              )}
            </div>
            <a
              href={opp.sale_listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs px-3 py-1 rounded bg-accent/10 border border-accent/20 text-accent hover:bg-accent/20 transition-colors"
            >
              💰 Sell on Oskelly →
            </a>
          </div>
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
            <h1 className="text-xl font-bold mt-1">{opp.sale_listing.title}</h1>
            <p className="text-sm text-muted mt-0.5">Vinted search: {opp.purchase_listing.title}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Metric label="Purchase Cost" value={formatEur(opp.purchase_cost_eur)} />
            <Metric label="Expected Sale" value={formatEur(opp.expected_sale_price_eur)} />
            <Metric label="Gross Profit" value={formatEur(opp.gross_profit_eur)} highlight />
            <Metric label="Net Profit" value={formatEur(opp.net_profit_eur)} highlight />
          </div>
          <p className="text-sm text-muted font-mono">ROI: {formatPct(opp.roi)}</p>
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

      {/* Post-to-Oskelly: generate an adapted Russian listing for the sell side */}
      <PostToOskelly opportunityId={opp.id} />

      {/* Oskelly listing detail */}
      <section className="card-glow rounded-xl p-6">
        <h2 className="font-semibold mb-4">Oskelly Listing (sell side)</h2>
        <div className="flex gap-4 items-start">
          {sellImg && (
            <div className="relative w-24 h-24 rounded-lg overflow-hidden bg-white/5 shrink-0">
              <Image src={sellImg} alt="" fill className="object-cover" unoptimized />
            </div>
          )}
          <div className="space-y-1">
            <p className="font-medium">{opp.sale_listing.title}</p>
            <p className="text-sm text-muted">
              Listed at {formatEur(opp.sale_listing.price_eur)} · {opp.sale_listing.condition}
              {opp.sale_listing.size_normalized ? ` · Size ${opp.sale_listing.size_normalized}` : ""}
            </p>
            <a
              href={opp.sale_listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-accent hover:underline"
            >
              View on Oskelly →
            </a>
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
