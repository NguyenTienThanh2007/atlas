import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, PageHeader } from "@/components/empty-state";
import { ApiErrorState } from "@/components/states";
import { errorText, getI18n } from "@/i18n";
import { apiGet, type Page, type Sector } from "@/lib/api";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t.meta.titles.sectors };
}

export default async function SectorsPage() {
  const [sectors, { locale, t, href }] = await Promise.all([
    apiGet<Page<Sector>>("/sectors", { limit: 100 }),
    getI18n(),
  ]);

  return (
    <>
      <PageHeader title={t.sectors.title} intro={t.sectors.intro} />
      {!sectors.ok ? (
        <ApiErrorState title={t.sectors.loadError} message={errorText(t, sectors)} />
      ) : sectors.data.items.length === 0 ? (
        <EmptyState title={t.sectors.noneTitle}>
          <p>{t.sectors.noneBody}</p>
        </EmptyState>
      ) : (
        <>
          <ul className="mt-10 grid max-w-3xl gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2">
            {sectors.data.items.map((s) => (
              <li key={s.id} className="bg-ink">
                <Link href={href(`/sectors/${s.id}`)} className="block h-full px-5 py-4 hover:bg-white/[0.03]">
                  <span className="flex items-baseline justify-between gap-4">
                    <span className="text-mist">{locale === "vi" ? s.name_vi : s.name}</span>
                    <span className="whitespace-nowrap text-sm text-muted tabular-nums">{t.sectors.count(s.company_count)}</span>
                  </span>
                  {/* The other language's name helps readers who know the English term, and vice versa. */}
                  <span lang={locale === "vi" ? "en" : "vi"} className="mt-0.5 block text-sm text-muted">
                    {locale === "vi" ? s.name : s.name_vi}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-6 max-w-2xl text-xs leading-relaxed text-muted">
            {t.sectors.taxonomyNote(sectors.data.items[0].taxonomy_version)}
          </p>
        </>
      )}
    </>
  );
}
