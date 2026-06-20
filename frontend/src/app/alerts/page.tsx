export default function AlertsPage() {
  return (
    <div className="p-8 max-w-2xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold">Alerts</h1>
        <p className="text-muted mt-1">Get notified when opportunities match your criteria</p>
      </header>

      <div className="card-glow rounded-xl p-6 space-y-4">
        <h2 className="font-semibold">Example Alert Rules</h2>
        <ul className="space-y-3 text-sm">
          <li className="flex justify-between border-b border-border pb-3">
            <span>ROI &gt; 80%</span>
            <code className="text-xs text-muted">{`{"roi_min": 0.8}`}</code>
          </li>
          <li className="flex justify-between border-b border-border pb-3">
            <span>Maison Margiela gap &gt; €300</span>
            <code className="text-xs text-muted">{`{"brand_slug": "maison-margiela", "gap_min": 300}`}</code>
          </li>
          <li className="flex justify-between">
            <span>Prada bags below market</span>
            <code className="text-xs text-muted">{`{"brand_slug": "prada", "category": "bags"}`}</code>
          </li>
        </ul>
        <p className="text-xs text-muted pt-2">
          Create alerts via API: POST /api/v1/alerts (requires authentication). Telegram/email notifications in Phase 4.
        </p>
      </div>
    </div>
  );
}
