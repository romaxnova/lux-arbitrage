/**
 * Image proxy — stabilises remote marketplace images.
 *
 * Vinted (vinted.net) and Oskelly (oskelly.ru) CDN images frequently fail when
 * hotlinked directly from the browser: hotlink/referer protection, occasional
 * CORS headers, and short-lived signed URLs. Proxying through this route (which
 * runs from Vercel's fra1 edge, the same region trusted by both CDNs) fetches
 * the bytes server-side with a proper Referer and re-streams them with long
 * cache headers, so every card shows a stable image regardless of source.
 *
 * Usage: /api/img?url=<encoded source image url>
 */

export const runtime = "nodejs";
export const preferredRegion = "fra1";

// Only proxy images from sources we actually ingest. Prevents the route being
// used as an open proxy for arbitrary URLs.
const ALLOWED_HOST_SUFFIXES = [
  ".vinted.net",
  ".vinted.com",
  "oskelly.ru",
  ".oskelly.ru",
  "images.unsplash.com",
];

function isAllowed(host: string): boolean {
  return ALLOWED_HOST_SUFFIXES.some(
    (suffix) => host === suffix.replace(/^\./, "") || host.endsWith(suffix)
  );
}

function refererFor(host: string): string {
  if (host.includes("oskelly")) return "https://oskelly.ru/";
  if (host.includes("vinted")) return "https://www.vinted.fr/";
  return "https://www.google.com/";
}

const TRANSPARENT_PIXEL = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64"
);

function placeholder(status = 200): Response {
  return new Response(TRANSPARENT_PIXEL, {
    status,
    headers: {
      "Content-Type": "image/png",
      // Short cache for failures so a transient CDN hiccup self-heals.
      "Cache-Control": "public, max-age=60",
    },
  });
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const raw = searchParams.get("url");
  if (!raw) return placeholder(400);

  let target: URL;
  try {
    target = new URL(raw);
  } catch {
    return placeholder(400);
  }

  if (target.protocol !== "https:" || !isAllowed(target.hostname)) {
    return placeholder(400);
  }

  try {
    const upstream = await fetch(target.toString(), {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        Accept: "image/avif,image/webp,image/png,image/*,*/*;q=0.8",
        Referer: refererFor(target.hostname),
      },
      // Cache the upstream fetch at the edge.
      next: { revalidate: 86400 },
    });

    if (!upstream.ok || !upstream.body) {
      return placeholder(upstream.status === 404 ? 404 : 502);
    }

    const contentType = upstream.headers.get("content-type") ?? "image/jpeg";
    if (!contentType.startsWith("image/")) {
      return placeholder(415);
    }

    return new Response(upstream.body, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        // Long, immutable-ish cache: marketplace photos never change per URL.
        "Cache-Control": "public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400",
      },
    });
  } catch {
    return placeholder(502);
  }
}
