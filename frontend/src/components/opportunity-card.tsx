import Link from "next/link";
import Image from "next/image";
import type { Opportunity } from "@/lib/api";
import { formatEur, formatPct, recColor } from "@/lib/utils";

export function OpportunityCard({ opportunity: opp }: { opportunity: Opportunity }) {
  const img = opp.purchase_listing.image_urls[0];

  return (
    <Link
      href={`/opportunities/${opp.id}`}
      className="card-glow rounded-xl bg-card overflow-hidden hover:border-accent/30 transition-all group"
    >
      <div className="relative h-44 bg-white/5">
        {img && (
          <Image src={img} alt={opp.purchase_listing.title} fill className="object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
        )}
        <div className="absolute top-3 right-3 flex gap-2">
          <span className={`text-xs font-semibold px-2 py-1 rounded border ${recColor(opp.recommendation)}`}>
            {opp.recommendation}
          </span>
          <span className="text-xs font-mono px-2 py-1 rounded bg-black/60 border border-border">
            {opp.opportunity_score.toFixed(0)}
          </span>
        </div>
      </div>
      <div className="p-4 space-y-3">
        <div>
          <p className="text-xs text-muted uppercase tracking-wide">{opp.brand.name}</p>
          <h3 className="font-medium leading-snug line-clamp-2">{opp.purchase_listing.title}</h3>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <p className="text-xs text-muted">Vinted</p>
            <p>{formatEur(opp.purchase_cost_eur)}</p>
          </div>
          <div>
            <p className="text-xs text-muted">Oskelly est.</p>
            <p>{formatEur(opp.expected_sale_price_eur)}</p>
          </div>
        </div>
        <div className="flex justify-between items-center pt-2 border-t border-border">
          <span className="text-buy font-semibold">{formatEur(opp.gross_profit_eur)} profit</span>
          <span className="font-mono text-sm">{formatPct(opp.roi)} ROI</span>
        </div>
      </div>
    </Link>
  );
}
