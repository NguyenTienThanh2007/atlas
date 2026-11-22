import type { Metadata } from "next";
import { EmptyState, PageHeader } from "@/components/empty-state";

export const metadata: Metadata = { title: "Companies" };

export default function CompaniesPage() {
  return (
    <>
      <PageHeader
        title="Companies"
        intro="Browse listed companies on HOSE, HNX and UPCoM and see what they do."
      />
      <EmptyState title="No companies to show yet">
        <p>Company profiles will appear here once a data source is connected.</p>
      </EmptyState>
    </>
  );
}
