import type { Metadata } from "next";
import { EmptyState, PageHeader } from "@/components/empty-state";

export const metadata: Metadata = { title: "Watchlist" };

export default function WatchlistPage() {
  return (
    <>
      <PageHeader title="Watchlist" intro="Keep the companies you're researching in one place." />
      <EmptyState title="Your watchlist is empty">
        <p>Saving companies becomes available once company profiles are live.</p>
      </EmptyState>
    </>
  );
}
