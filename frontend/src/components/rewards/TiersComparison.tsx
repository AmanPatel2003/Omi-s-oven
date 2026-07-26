import type { RewardTier } from "@/types/api";

export function TiersComparison({ tiers }: { tiers: RewardTier[] }) {
  if (tiers.length === 0) return null;

  return (
    <section className="mt-8">
      <h2 className="font-display text-lg font-semibold text-crust-900">
        Tiers
      </h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            className="rounded-xl border border-crust-100 bg-white p-4"
          >
            <p className="font-medium text-crust-900">{tier.name}</p>
            <p className="text-xs text-crust-500">{tier.minPoints}+ points</p>
            <ul className="mt-2 flex flex-col gap-1 text-xs text-crust-600">
              {tier.benefits.map((benefit, i) => (
                <li key={i}>• {benefit}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
