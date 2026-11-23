import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CompanyList } from "@/components/company-list";
import { EmptyState } from "@/components/empty-state";
import { Pagination } from "@/components/pagination";
import { ApiErrorState, BackLink } from "@/components/states";
import { errorText, getI18n } from "@/i18n";
import { apiGet, pageNumber, UUID, type CompanyListItem, type Page, type Sector } from "@/lib/api";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t.meta.titles.sector };
}

const PAGE_SIZE = 20;

export default async function SectorPage({ params, searchParams }: PageProps<"/[lang]/sectors/[id]">) {
  const [{ id }, sp, { locale, t }] = await Promise.all([params, searchParams, getI18n()]);
  if (!UUID.test(id)) notFound();
  const page = pageNumber(sp.page);

  const sector = await apiGet<Sector>(`/sectors/${id}`);
  if (!sector.ok && sector.kind === "not_found") notFound();
  if (!sector.ok) {
    return (
      <>
        <BackLink path="/sectors">{t.sector.back}</BackLink>
        <ApiErrorState title={t.sector.loadError} message={errorText(t, sector)} />
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
      <BackLink path="/sectors">{t.sector.back}</BackLink>
      <header className="mt-6 max-w-2xl">
        <h1 className="font-display text-3xl font-light text-mist sm:text-4xl">
          {locale === "vi" ? s.name_vi : s.name}
        </h1>
        <p lang={locale === "vi" ? "en" : "vi"} className="mt-1 text-muted">
          {locale === "vi" ? s.name : s.name_vi}
        </p>
        {/* Taxonomy descriptions exist in English only (taxonomy v1.0.0). */}
        <p lang="en" className="mt-4 leading-relaxed text-muted">
          {s.description}
        </p>
      </header>

      {!companies.ok ? (
        <ApiErrorState title={t.sector.companiesLoadError} message={errorText(t, companies)} />
      ) : companies.data.items.length === 0 ? (
        <EmptyState title={t.sector.noneTitle}>
          <p>{t.sector.noneBody}</p>
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
