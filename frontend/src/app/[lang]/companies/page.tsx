import type { Metadata } from "next";
import { CompanyFilters } from "@/components/company-filters";
import { CompanyList } from "@/components/company-list";
import { EmptyState, PageHeader } from "@/components/empty-state";
import { Pagination } from "@/components/pagination";
import { ApiErrorState } from "@/components/states";
import { errorText, getI18n } from "@/i18n";
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

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t.meta.titles.companies };
}

const PAGE_SIZE = 20;

export default async function CompaniesPage({ searchParams }: PageProps<"/[lang]/companies">) {
  const [sp, { t }] = await Promise.all([searchParams, getI18n()]);
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
      <PageHeader title={t.companies.title} intro={t.companies.intro} />
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
        <ApiErrorState title={t.companies.loadError} message={errorText(t, companies)} />
      ) : companies.data.items.length === 0 ? (
        filtered ? (
          <EmptyState title={t.companies.noMatchTitle}>
            <p>{t.companies.noMatchBody}</p>
          </EmptyState>
        ) : (
          <EmptyState title={t.companies.noneTitle}>
            <p>{t.companies.noneBody}</p>
          </EmptyState>
        )
      ) : (
        <>
          <p className="mt-6 text-sm text-muted" aria-live="polite">
            {t.companies.count(companies.data.total)}
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
