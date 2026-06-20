export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export interface ListingBrief {
  id: string;
  title: string;
  price_eur: number;
  marketplace: string;
  url: string;
  image_urls: string[];
  condition: string;
  size_normalized?: string;
  category: string;
}

export interface Opportunity {
  id: string;
  opportunity_score: number;
  recommendation: "BUY" | "WATCH" | "SKIP";
  roi: number;
  gross_profit_eur: number;
  net_profit_eur: number;
  demand_score: number;
  liquidity_score: number;
  risk_score: number;
  roi_score: number;
  price_gap_score: number;
  purchase_cost_eur: number;
  expected_sale_price_eur: number;
  purchase_listing: ListingBrief;
  sale_listing: ListingBrief;
  brand: { name: string; slug: string; tier?: string };
}

export interface OpportunityDetail extends Opportunity {
  cost_breakdown: Record<string, number>;
  match_confidence: number;
  computed_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface BrandAnalytics {
  brand: { name: string; slug: string; tier?: string };
  avg_vinted_price_eur: number;
  avg_oskelly_price_eur: number;
  median_spread_eur: number;
  median_roi: number;
  demand_trend: string;
  liquidity_trend: string;
  top_categories: { category: string; median_roi: number; opportunity_count: number }[];
  active_opportunities: number;
}

export interface MarketStats {
  active_listings: number;
  opportunities: number;
  matches: number;
  buy_recommendations: number;
}

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    next: { revalidate: 30 },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getOpportunities: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return fetchApi<Paginated<Opportunity>>(`/api/v1/opportunities${qs}`);
  },
  getOpportunity: (id: string) => fetchApi<OpportunityDetail>(`/api/v1/opportunities/${id}`),
  getRankings: (type: string) => fetchApi<Opportunity[]>(`/api/v1/opportunities/rankings/${type}?limit=5`),
  getBrands: () => fetchApi<{ name: string; slug: string; tier?: string }[]>("/api/v1/brands"),
  getBrand: (slug: string) => fetchApi<BrandAnalytics>(`/api/v1/brands/${slug}`),
  getStats: () => fetchApi<MarketStats>("/api/v1/market/stats"),
  triggerPipeline: () => fetchApi<{ status: string; stats: Record<string, number> }>("/api/v1/admin/scrape/trigger", { method: "POST" }),
};
