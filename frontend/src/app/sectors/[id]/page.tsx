import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CompanyList } from "@/components/company-list";
import { EmptyState } from "@/components/empty-state";
import { Pagination } from "@/components/pagination";
import { ApiErrorState, BackLink } from "@/components/states";
import { apiGet, pageNumber, UUID, type CompanyListItem, type Page, type Sector } from "@/lib/api";

export const metadata: Metadata = { title: "Sector" };

const PAGE_SIZE = 20;

export default async function SectorPage({ params, searchParams }: PageProps<"/sectors/[id]">) {
  const [{ id }, sp] = await Promise.all([params, searchParams]);
  if (!UUID.test(id)) notFound();
  const page = pageNumber(sp.page);

  const sector = await apiGet<Sector>(`/sectors/${id}`);
  if (!sector.ok && sector.status === 404) notFound();
  if (!sector.ok) {
    return (
      <>
        <BackLink href="/sectors">Sectors</BackLink>
        <ApiErrorState title="Couldn't load this sector" message={sector.message} />
      </>
    );
  }
  const s = sector.data;
  const companies = await apiGet<Page<CompanyListItem>>("/companies", {
    sector: s.code,
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
  });

  return (
    <>
      <BackLink href="/sectors">Sectors</BackLink>
      <header className="mt-6 max-w-2xl">
        <h1 className="font-display text-3xl font-light text-mist sm:text-4xl">{s.name}</h1>
        <p lang="vi" className="mt-1 text-muted">
          {s.name_vi}
        </p>
        <p className="mt-4 leading-relaxed text-muted">{s.description}</p>
      </header>

      {!companies.ok ? (
        <ApiErrorState title="Couldn't load companies in this sector" message={companies.message} />
      ) : companies.data.items.length === 0 ? (
        <EmptyState title="No companies in this sector yet">
          <p>Companies appear here once they are imported with evidence for this sector.</p>
        </EmptyState>
      ) : (
        <>
          <CompanyList companies={companies.data.items} />
          <Pagination
            basePath={`/sectors/${s.id}`}
            params={{}}
            page={page}
            pageSize={PAGE_SIZE}
            total={companies.data.total}
          />
        </>
      )}
    </>
  );
}
