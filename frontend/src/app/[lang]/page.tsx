import { EmptyState } from "@/components/empty-state";
import { Graticule } from "@/components/graticule";
import { getI18n } from "@/i18n";

export default async function DiscoverPage() {
  const { t } = await getI18n();
  return (
    <div className="relative">
      <Graticule className="pointer-events-none absolute -top-12 right-0 -z-10 hidden h-[34rem] w-[24rem] text-muted/35 xl:block" />

      <header className="max-w-xl">
        <h1 className="font-display text-4xl leading-[1.1] font-light text-mist sm:text-5xl">
          {t.discover.title}
        </h1>
        <p className="mt-4 max-w-lg leading-relaxed text-muted">{t.discover.intro}</p>
      </header>

      <EmptyState title={t.discover.emptyTitle}>
        <p>{t.discover.emptyBody}</p>
      </EmptyState>

      <section className="glass mt-6 max-w-2xl rounded-lg border border-line px-6 py-5">
        <h2 className="text-sm font-medium text-mist">{t.discover.worldTitle}</h2>
        <p className="mt-1 text-sm leading-relaxed text-muted">{t.discover.worldBody}</p>
      </section>
    </div>
  );
}
