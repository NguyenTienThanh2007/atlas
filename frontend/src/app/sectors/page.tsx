import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, PageHeader } from "@/components/empty-state";
import { ApiErrorState } from "@/components/states";
import { apiGet, type Page, type Sector } from "@/lib/api";

export const metadata: Metadata = { title: "Sectors" };

export default async function SectorsPage() {
  const sectors = await apiGet<Page<Sector>>("/sectors", { limit: 100 });

  return (
    <>
      <PageHeader
        title="Sectors"
        intro="Compare industries across Vietnam's exchanges, from banking to logistics."
      />
      {!sectors.ok ? (
        <ApiErrorState title="Couldn't load sectors" message={sectors.message} />
      ) : sectors.data.items.length === 0 ? (
        <EmptyState title="No sectors yet">
          <p>The sector taxonomy loads when the backend starts. Restart the backend to seed it.</p>
        </EmptyState>
      ) : (
        <>
          <ul className="mt-10 grid max-w-3xl gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2">
            {sectors.data.items.map((s) => (
              <li key={s.id} className="bg-ink">
                <Link href={`/sectors/${s.id}`} className="block h-full px-5 py-4 hover:bg-white/[0.03]">
                  <span className="flex items-baseline justify-between gap-4">
                    <span className="text-mist">{s.name}</span>
                    <span className="text-sm text-muted tabular-nums">
                      {s.company_count} {s.company_count === 1 ? "company" : "companies"}
                    </span>
                  </span>
                  <span lang="vi" className="mt-0.5 block text-sm text-muted">
                    {s.name_vi}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-6 max-w-2xl text-xs leading-relaxed text-muted">
            ATLAS taxonomy v{sectors.data.items[0].taxonomy_version}: our own grouping by primary
            business line, not an official classification by HOSE, HNX or the State Securities
            Commission.
          </p>
        </>
      )}
    </>
  );
}
