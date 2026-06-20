"use client";

import { useState } from "react";
import { API_URL } from "@/lib/api";

interface RussianListing {
  title: string;
  description: string;
  brand: string;
  item_type_ru: string;
  condition_ru: string;
  size: string | null;
  price_rub: number;
  category: string;
  images: string[];
}

interface PostResult {
  status: string;
  message?: string;
  publish_enabled?: boolean;
  credentials_configured?: boolean;
}

interface PostResponse {
  listing: RussianListing;
  result: PostResult;
}

/**
 * Generates an adapted Russian Oskelly listing for this opportunity and shows
 * it for review. Publishing is gated server-side (preview by default), so this
 * never posts to the live account unless posting is explicitly enabled.
 */
export function PostToOskelly({ opportunityId }: { opportunityId: string }) {
  const [data, setData] = useState<PostResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  async function run(publish: boolean) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/opportunities/${opportunityId}/post-to-oskelly?publish=${publish}`,
        { method: "POST", cache: "no-store" }
      );
      if (!res.ok) throw new Error(`API ${res.status}`);
      setData(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function copy(text: string, key: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  const listing = data?.listing;
  const result = data?.result;
  const canPublish = result?.publish_enabled && result?.credentials_configured;

  return (
    <section className="card-glow rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold">Post to Oskelly</h2>
          <p className="text-xs text-muted mt-0.5">
            Auto-generates an original Russian listing — adapted, not copied.
          </p>
        </div>
        <button
          onClick={() => run(false)}
          disabled={loading}
          className="text-sm px-4 py-2 rounded bg-accent/10 hover:bg-accent/20 border border-accent/20 text-accent transition-colors disabled:opacity-50"
        >
          {loading ? "Generating…" : data ? "Regenerate" : "Generate listing"}
        </button>
      </div>

      {error && (
        <p className="text-sm text-skip">Could not generate: {error}</p>
      )}

      {listing && (
        <div className="space-y-4">
          <Field label="Заголовок (title)" value={listing.title} onCopy={() => copy(listing.title, "title")} copied={copied === "title"} />
          <Field
            label="Описание (description)"
            value={listing.description}
            multiline
            onCopy={() => copy(listing.description, "desc")}
            copied={copied === "desc"}
          />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <Meta label="Бренд" value={listing.brand} />
            <Meta label="Категория" value={listing.item_type_ru} />
            <Meta label="Состояние" value={listing.condition_ru} />
            <Meta label="Цена" value={`${listing.price_rub.toLocaleString("ru-RU")} ₽`} />
          </div>

          {listing.images.length > 0 && (
            <div className="flex gap-2 overflow-x-auto">
              {listing.images.slice(0, 5).map((src) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={src}
                  src={`/api/img?url=${encodeURIComponent(src)}`}
                  alt=""
                  className="w-20 h-20 object-cover rounded-lg bg-white/5 shrink-0"
                />
              ))}
            </div>
          )}

          <div className="flex items-center gap-3 pt-1">
            <button
              onClick={() => run(true)}
              disabled={loading || !canPublish}
              title={canPublish ? "Publish draft to Oskelly" : "Publishing disabled — enable OSKELLY_PUBLISH_ENABLED and credentials"}
              className="text-sm px-4 py-2 rounded bg-buy/10 hover:bg-buy/20 border border-buy/30 text-buy transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Publish to Oskelly →
            </button>
            {result?.message && (
              <span className="text-xs text-muted">{result.message}</span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function Field({
  label,
  value,
  multiline,
  onCopy,
  copied,
}: {
  label: string;
  value: string;
  multiline?: boolean;
  onCopy: () => void;
  copied: boolean;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-xs text-muted uppercase tracking-wide">{label}</label>
        <button onClick={onCopy} className="text-xs text-accent hover:underline">
          {copied ? "Copied ✓" : "Copy"}
        </button>
      </div>
      {multiline ? (
        <pre className="text-sm whitespace-pre-wrap font-sans bg-white/5 rounded-lg p-3 border border-border">{value}</pre>
      ) : (
        <p className="text-sm bg-white/5 rounded-lg p-3 border border-border">{value}</p>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/5 p-2">
      <p className="text-[10px] text-muted uppercase">{label}</p>
      <p className="text-sm">{value}</p>
    </div>
  );
}
