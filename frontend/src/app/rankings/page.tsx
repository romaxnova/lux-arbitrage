import { api } from "@/lib/api";
import { OpportunityCard } from "@/components/opportunity-card";

const RANKINGS = [
  { key: "top", title: "Top Arbitrage Opportunities" },
  { key: "undervalued", title: "Most Undervalued" },
  { key: "highest_roi", title: "Highest ROI" },
  { key: "fastest_moving", title: "Fastest Moving" },
  { key: "highest_demand", title: "Highest Demand" },
  { key: "lowest_risk", title: "Lowest Risk" },
] as const;

export default async function RankingsPage() {
  const sections = await Promise.all(
    RANKINGS.map(async (r) => {
      try {
        const items = await api.getRankings(r.key);
        return { ...r, items };
      } catch {
        return { ...r, items: [] };
      }
    })
  );

  return (
    <div className="p-8 space-y-10">
      <header>
        <h1 className="text-3xl font-bold">Analytics Rankings</h1>
        <p className="text-muted mt-1">Curated views across the arbitrage engine</p>
      </header>

      {sections.map((section) => (
        <section key={section.key}>
          <h2 className="text-xl font-semibold mb-4">{section.title}</h2>
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {section.items.map((opp) => (
              <OpportunityCard key={opp.id} opportunity={opp} />
            ))}
            {section.items.length === 0 && (
              <p className="text-muted">No data available</p>
            )}
          </div>
        </section>
      ))}
    </div>
  );
}
