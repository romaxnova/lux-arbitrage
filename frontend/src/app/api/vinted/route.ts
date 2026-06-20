/**
 * Vinted proxy API route — runs on Vercel's fra1 (Frankfurt) edge.
 * Vinted blocks US IPs (Render) but European Vercel servers can access it.
 *
 * Usage: GET /api/vinted?brand=Prada&limit=5&min_price=200
 * Returns: { items: VintedItem[], total?: number }
 */

export const runtime = "nodejs";
export const preferredRegion = "fra1";

const VINTED_BASE = "https://www.vinted.fr";

const BROWSER_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
  "Accept-Encoding": "gzip, deflate, br",
  "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
  "Sec-CH-UA-Mobile": "?0",
  "Sec-CH-UA-Platform": '"macOS"',
};

// Brand IDs on Vinted — verified via /api/v2/brands?keyword=NAME
const BRAND_IDS: Record<string, number> = {
  prada: 3573,
  "miu miu": 1745,
  balenciaga: 2369,
  "maison margiela": 639289,
  "rick owens": 145654,
  diesel: 161,
  "acne studios": 180798,
  "chrome hearts": 95106,
  "saint laurent": 83122,
  gucci: 567,
  "bottega veneta": 86972,
  "comme des garçons": 56974,
  "comme des garcons": 56974,
};

/** Extract all Set-Cookie values from a response and deduplicate by name.
 *  Vinted sends access_token_web twice; keeping the last value is correct. */
function extractCookies(headers: Headers): string {
  const raw = (headers as unknown as { getSetCookie?: () => string[] }).getSetCookie?.() ?? [];
  if (raw.length === 0) {
    // Fallback for environments without getSetCookie
    raw.push(...(headers.get("set-cookie") || "").split(/,(?=\s*\w+=)/));
  }
  // Deduplicate: last Set-Cookie wins for each name
  const map = new Map<string, string>();
  for (const cookie of raw) {
    const nameVal = cookie.split(";")[0].trim();
    const name = nameVal.split("=")[0].trim();
    map.set(name, nameVal);
  }
  return [...map.values()].join("; ");
}

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

// Reject obviously non-fashion items (cosmetics, electronics, food, etc.)
const NON_FASHION_PATTERNS =
  /\b(parfum|perfume|essence|eau de|fragrance|ml\b|hdmi|cable|câble|supra\b|lacoste\b|pull lacoste|nike\b|adidas\b|new balance|vans\b|converse\b)\b/i;

function parseItems(items: unknown[]): VintedItem[] {
  const results: VintedItem[] = [];

  for (const raw of items) {
    const item = raw as Record<string, unknown>;
    const title = String(item.title ?? "");

    // Skip non-fashion items
    if (NON_FASHION_PATTERNS.test(title)) continue;

    const priceData = (item.price as Record<string, unknown>) || {};
    const photos = (item.photos as Record<string, unknown>[]) || [];
    const photo = (item.photo as Record<string, unknown>) || {};
    const firstPhoto = photos[0] ?? photo;
    const imageUrl =
      (firstPhoto.url as string | undefined) ??
      (firstPhoto.full_size_url as string | undefined) ??
      null;

    results.push({
      id: String(item.id),
      title,
      price_eur: parseFloat(String(priceData.amount ?? 0)),
      url: String(item.url ?? `${VINTED_BASE}/items/${item.id}`),
      image_url: imageUrl,
      brand: String(item.brand_title ?? ""),
      size: (item.size_title as string | null) ?? null,
      condition: String(item.status ?? "good"),
    });
  }

  return results;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const brand = searchParams.get("brand") ?? "";
  // item_type_en: English type phrase to narrow the search (e.g. "sneakers", "tote bag")
  const itemTypeEn = searchParams.get("item_type") ?? "";
  const limit = Math.min(parseInt(searchParams.get("limit") ?? "10"), 20);
  const minPrice = searchParams.get("min_price") ?? "80";

  try {
    const bootstrapRes = await fetch(`${VINTED_BASE}/catalog`, {
      headers: {
        ...BROWSER_HEADERS,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
      },
      cache: "no-store",
      redirect: "follow",
    });

    const cookieHeader = extractCookies(bootstrapRes.headers);
    if (!cookieHeader) {
      return Response.json({ items: [], error: "No cookies from Vinted bootstrap" }, { status: 502 });
    }

    const brandKey = brand.toLowerCase();
    const brandId = BRAND_IDS[brandKey];

    const params = new URLSearchParams({
      per_page: String(limit),
      page: "1",
      order: "newest_first",
      price_from: minPrice,
    });

    // Use brand_id filter when available + item_type_en as search_text.
    // Combining both narrows results to the correct brand AND item type
    // (e.g. Gucci brand_id + search_text="tote bag" → real Gucci tote bags).
    if (brandId) {
      params.set("brand_ids[]", String(brandId));
    }
    if (itemTypeEn) {
      params.set("search_text", itemTypeEn);
    } else if (!brandId && brand) {
      params.set("search_text", brand);
    }

    const apiRes = await fetch(`${VINTED_BASE}/api/v2/catalog/items?${params}`, {
      headers: {
        ...BROWSER_HEADERS,
        Accept: "application/json, text/plain, */*",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        Referer: `${VINTED_BASE}/catalog`,
        Cookie: cookieHeader,
      },
      cache: "no-store",
    });

    if (!apiRes.ok) {
      const body = await apiRes.text().catch(() => "");
      return Response.json(
        { items: [], error: `Vinted API ${apiRes.status}`, detail: body.slice(0, 200) },
        { status: apiRes.status === 403 ? 503 : apiRes.status }
      );
    }

    const data = (await apiRes.json()) as Record<string, unknown>;
    const rawItems = (data.items as unknown[]) ?? [];
    const items = parseItems(rawItems);

    return Response.json({
      items,
      total: (data.pagination as Record<string, unknown> | undefined)?.total_count ?? items.length,
    });
  } catch (err) {
    return Response.json({ items: [], error: String(err) }, { status: 500 });
  }
}
