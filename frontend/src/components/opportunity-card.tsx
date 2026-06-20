import Link from "next/link";
import Image from "next/image";
import type { Opportunity } from "@/lib/api";
import { formatEur, formatPct, recColor, firstImage } from "@/lib/utils";

export function OpportunityCard({ opportunity: opp }: { opportunity: Opportunity }) {
  // Prefer the Oskelly (sale) image since it has real photos; fall back to buy
  // side. Both are routed through the edge image proxy for stable rendering.
  const img = firstImage(opp.sale_listing.image_urls, opp.purchase_listing.image_urls);
  const buyUrl = opp.purchase_listing.url;
  const sellUrl = opp.sale_listing.url;

  return (
    <div className="card-glow rounded-xl bg-card overflow-hidden hover:border-accent/30 transition-all group flex flex-col">
      {/* Image area — links to detail page */}
      <Link href={`/opportunities/${opp.id}`} className="relative h-44 bg-white/5 block">
        {img ? (
          <Image
            src={img}
            alt={opp.sale_listing.title}
            fill
            className="object-cover opacity-80 group-hover:opacity-100 transition-opacity"
            unoptimized
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-muted text-xs">No image</div>
        )}
        <div className="absolute top-3 right-3 flex gap-2">
          <span className={`text-xs font-semibold px-2 py-1 rounded border ${recColor(opp.recommendation)}`}>
            {opp.recommendation}
          </span>
          <span className="text-xs font-mono px-2 py-1 rounded bg-black/60 border border-border">
            {opp.opportunity_score.toFixed(0)}
          </span>
        </div>
        {/* Sell side label */}
        <div className="absolute bottom-2 left-2 text-[10px] bg-black/70 text-muted px-2 py-0.5 rounded">
          Oskelly listing
        </div>
      </Link>

      <div className="p-4 space-y-3 flex-1 flex flex-col">
        <Link href={`/opportunities/${opp.id}`} className="block space-y-1">
          <p className="text-xs text-muted uppercase tracking-wide">{opp.brand.name} · {opp.purchase_listing.category}</p>
          <h3 className="font-medium leading-snug line-clamp-2 text-sm">{opp.sale_listing.title}</h3>
        </Link>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <p className="text-xs text-muted">Buy on Vinted</p>
            <p className="font-mono">{formatEur(opp.purchase_cost_eur)}</p>
          </div>
          <div>
            <p className="text-xs text-muted">Sell on Oskelly</p>
            <p className="font-mono">{formatEur(opp.expected_sale_price_eur)}</p>
          </div>
        </div>

        <div className="flex justify-between items-center pt-2 border-t border-border">
          <div>
            <p className="text-buy font-semibold text-sm">{formatEur(opp.gross_profit_eur)} profit</p>
            <p className="text-xs text-muted">{formatEur(opp.net_profit_eur)} net · {formatPct(opp.roi)} ROI</p>
          </div>
        </div>

        {/* Direct action links */}
        <div className="flex gap-2 pt-1 mt-auto">
          <a
            href={buyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-xs px-2 py-1.5 rounded bg-white/5 hover:bg-white/10 border border-border text-muted hover:text-foreground transition-colors"
          >
            🛍 Buy (Vinted)
          </a>
          <a
            href={sellUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-xs px-2 py-1.5 rounded bg-accent/10 hover:bg-accent/20 border border-accent/20 text-accent transition-colors"
          >
            💰 Sell (Oskelly)
          </a>
        </div>
      </div>
    </div>
  );
}
