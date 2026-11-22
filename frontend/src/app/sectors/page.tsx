import type { Metadata } from "next";
import { EmptyState, PageHeader } from "@/components/empty-state";

export const metadata: Metadata = { title: "Sectors" };

export default function SectorsPage() {
  return (
    <>
      <PageHeader
        title="Sectors"
        intro="Compare industries across Vietnam's exchanges, from banking to logistics."
      />
      <EmptyState title="No sectors to show yet">
        <p>Sector classifications will appear here once a data source is connected.</p>
      </EmptyState>
    </>
  );
}
