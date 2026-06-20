export function StatCard({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`card-glow rounded-xl p-5 ${accent ? "border-accent/20" : ""}`}>
      <p className="text-xs text-muted uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-2xl font-bold font-mono ${accent ? "text-accent" : ""}`}>{value}</p>
    </div>
  );
}
