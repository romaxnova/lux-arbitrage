export function ScoreBar({ label, value, danger }: { label: string; value: number; danger?: boolean }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-muted">{label}</span>
        <span className="font-mono">{value.toFixed(0)}</span>
      </div>
      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${danger ? "bg-skip" : "bg-accent"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
