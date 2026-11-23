import type { Metadata } from "next";
import { EmptyState, PageHeader } from "@/components/empty-state";
import { getI18n } from "@/i18n";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t.meta.titles.watchlist };
}

export default async function WatchlistPage() {
  const { t } = await getI18n();
  return (
    <>
      <PageHeader title={t.watchlist.title} intro={t.watchlist.intro} />
      <EmptyState title={t.watchlist.emptyTitle}>
        <p>{t.watchlist.emptyBody}</p>
      </EmptyState>
    </>
  );
}
