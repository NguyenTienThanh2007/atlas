import type { Metadata } from "next";
import { CompanyFilters } from "@/components/company-filters";
import { CompanyList } from "@/components/company-list";
import { EmptyState, PageHeader } from "@/components/empty-state";
import { Pagination } from "@/components/pagination";
import { ApiErrorState } from "@/components/states";
import {
  apiGet,
  cleanParam,
  EXCHANGE_CODE,
  pageNumber,
  SECTOR_CODE,
  type CompanyListItem,
  type Exchange,
  type Page,
  type Sector,
} from "@/lib/api";

export const metadata: Metadata = { title: "Companies" };

const PAGE_SIZE = 20;

export default async function CompaniesPage({ searchParams }: PageProps<"/companies">) {
  const sp = await searchParams;
  const q = cleanParam(sp.q);
  const sector = cleanParam(sp.sector, SECTOR_CODE);
  const exchange = cleanParam(sp.exchange, EXCHANGE_CODE);
  const page = pageNumber(sp.page);

  const [companies, sectors, exchanges] = await Promise.all([
    apiGet<Page<CompanyListItem>>("/companies", {
      q,
      sector,
      exchange,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
    apiGet<Page<Sector>>("/sectors", { limit: 100 }),
    apiGet<Page<Exchange>>("/exchanges", { limit: 100 }),
  ]);
  const filtered = Boolean(q || sector || exchange);

  return (
    <>
      <PageHeader
        title="Companies"
        intro="Browse listed companies on HOSE, HNX and UPCoM and see what they do."
      />
      {sectors.ok && exchanges.ok && (
        <CompanyFilters
          q={q}
          sector={sector}
          exchange={exchange}
          sectors={sectors.data.items}
          exchanges={exchanges.data.items}
        />
      )}

      {!companies.ok ? (
        <ApiErrorState title="Couldn't load companies" message={companies.message} />
      ) : companies.data.items.length === 0 ? (
        filtered ? (
          <EmptyState title="No companies match">
            <p>Try a different ticker or name, or clear the sector and exchange filters.</p>
          </EmptyState>
        ) : (
          <EmptyState title="No companies yet">
            <p>
              Company profiles appear here once they are imported from a verified source. See
              the data import guide in docs/DEVELOPMENT.md.
            </p>
          </EmptyState>
        )
      ) : (
        <>
          <p className="mt-6 text-sm text-muted" aria-live="polite">
            {companies.data.total} {companies.data.total === 1 ? "company" : "companies"}
          </p>
          <CompanyList companies={companies.data.items} />
          <Pagination
            basePath="/companies"
            params={{ q, sector, exchange }}
            page={page}
            pageSize={PAGE_SIZE}
            total={companies.data.total}
          />
        </>
      )}
    </>
  );
}
