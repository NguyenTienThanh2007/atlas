import { EmptyState } from "@/components/empty-state";
import { Graticule } from "@/components/graticule";

export default function DiscoverPage() {
  return (
    <div className="relative">
      <Graticule className="pointer-events-none absolute -top-12 right-0 -z-10 hidden h-[34rem] w-[24rem] text-muted/35 xl:block" />

      <header className="max-w-xl">
        <h1 className="font-display text-4xl leading-[1.1] font-light text-mist sm:text-5xl">
          Explore Vietnam&rsquo;s listed economy
        </h1>
        <p className="mt-4 max-w-lg leading-relaxed text-muted">
          Discover sectors, companies and the regions they operate in. Your workspace fills in
          as market data sources are connected.
        </p>
      </header>

      <EmptyState title="No market data connected">
        <p>
          ATLAS only shows figures that come from a verified source, so this workspace is empty
          for now. Once a data source is connected, sectors and companies will appear here.
        </p>
      </EmptyState>

      <section className="glass mt-6 max-w-2xl rounded-lg border border-line px-6 py-5">
        <h2 className="text-sm font-medium text-mist">World view</h2>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          An interactive map of where Vietnam&rsquo;s companies operate is planned for a later
          release.
        </p>
      </section>
    </div>
  );
}
