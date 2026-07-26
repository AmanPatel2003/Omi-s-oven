import type { ApiEnvelope, RewardTier } from "@/types/api";

export async function serverFetchRewardTiers(): Promise<RewardTier[]> {
  const res = await fetch(`${process.env.API_URL}/rewards/tiers`, {
    next: { revalidate: 3600 },
  });
  if (!res.ok) return [];
  const envelope: ApiEnvelope<RewardTier[]> = await res.json();
  return envelope.data;
}
