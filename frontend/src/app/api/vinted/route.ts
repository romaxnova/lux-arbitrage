/**
 * Vinted proxy API route — runs on Vercel's fra1 (Frankfurt) edge.
 * Vinted blocks US IPs (where Render is hosted) but European Vercel
 * servers can access the Vinted catalog API.
 *
 * Usage: GET /api/vinted?brand=Prada&category=bags&limit=5
 * Returns: { items: VintedItem[] }
 */

export const runtime = "nodejs";
export const preferredRegion = "fra1";

const VINTED_BASE = "https://www.vinted.fr";
const DEFAULT_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
  Accept: "application/json, text/plain, */*",
  "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
  "Sec-CH-UA-Mobile": "?0",
  "Sec-CH-UA-Platform": '"macOS"',
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  Referer: `${VINTED_BASE}/catalog`,
};

interface VintedItem {
  id: string;
  title: string;
  price_eur: number;
  url: string;
  image_url: string | null;
  brand: string;
  size: string | null;
  condition: string;
}

// Brand IDs known on Vinted (avoids a separate brand lookup API call)
const BRAND_IDS: Record<string, number> = {
  prada: 3573,
  "miu miu": 4490,
  balenciaga: 1005,
  "maison margiela": 3432,
  "rick owens": 62050,
  diesel: 304,
  "acne studios": 42059,
  "chrome hearts": 27609,
  "saint laurent": 33,
  gucci: 305,
  "bottega veneta": 1071,
  "comme des garçons": 15684,
  "comme des garcons": 15684,
};

async function bootstrapCookies(): Promise<string> {
  const res = await fetch(`${VINTED_BASE}/catalog`, {
    headers: {
      ...DEFAULT_HEADERS,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
    cache: "no-store",
  });
  const setCookie = res.headers.get("set-cookie") || "";
  // Extract relevant cookies
  const cookies = setCookie
    .split(/,(?=[^ ])/)
    .map((c) => c.split(";")[0].trim())
    .filter((c) => c.includes("="))
    .join("; ");
  return cookies;
}

function parseItems(data: Record<string, unknown>): VintedItem[] {
  const items = (data.items as Record<string, unknown>[]) || [];
  return items.map((item) => {
    const priceData = (item.price as Record<string, unknown>) || {};
    const photo = (item.photo as Record<string, unknown>) || {};
    const photos = (item.photos as Record<string, unknown>[]) || [];
    const firstPhoto = photos[0] || photo;
    const imageUrl =
      (firstPhoto.url as string) ||
      (firstPhoto.full_size_url as string) ||
      (photo.url as string) ||
      null;

    return {
      id: String(item.id),
      title: (item.title as string) || "",
      price_eur: parseFloat(String(priceData.amount || 0)),
      url: (item.url as string) || `${VINTED_BASE}/items/${item.id}`,
      image_url: imageUrl,
      brand: (item.brand_title as string) || "",
      size: (item.size_title as string) || null,
      condition: (item.status as string) || "good",
    };
  });
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const brand = searchParams.get("brand") || "";
  const limit = Math.min(parseInt(searchParams.get("limit") || "10"), 20);
  const minPrice = searchParams.get("min_price") || "100";

  const brandKey = brand.toLowerCase();
  const brandId = BRAND_IDS[brandKey];

  try {
    // Bootstrap session to get cookies
    const cookies = await bootstrapCookies();

    if (!cookies) {
      return Response.json({ items: [], error: "Could not obtain Vinted session" }, { status: 502 });
    }

    const params = new URLSearchParams({
      per_page: String(limit),
      page: "1",
      order: "newest_first",
      price_from: minPrice,
    });

    if (brandId) {
      params.set("brand_ids[]", String(brandId));
    } else if (brand) {
      params.set("search_text", brand);
    }

    const apiUrl = `${VINTED_BASE}/api/v2/catalog/items?${params}`;
    const res = await fetch(apiUrl, {
      headers: {
        ...DEFAULT_HEADERS,
        Cookie: cookies,
      },
      cache: "no-store",
    });

    if (!res.ok) {
      return Response.json(
        { items: [], error: `Vinted API returned ${res.status}` },
        { status: res.status === 403 ? 503 : res.status }
      );
    }

    const data = (await res.json()) as Record<string, unknown>;
    const items = parseItems(data);

    return Response.json({ items, total: data.pagination ? (data.pagination as Record<string, unknown>).total_count : items.length });
  } catch (err) {
    return Response.json({ items: [], error: String(err) }, { status: 500 });
  }
}
