import { serverFetchRewardTiers } from "@/lib/server-rewards";
import { TiersComparison } from "@/components/rewards/TiersComparison";
import { RewardsSummaryClient } from "@/components/rewards/RewardsSummaryClient";

export default async function RewardsPage() {
  const tiers = await serverFetchRewardTiers();

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Rewards
      </h1>

      <div className="mt-6">
        <RewardsSummaryClient />
      </div>

      <TiersComparison tiers={tiers} />
    </div>
  );
}
