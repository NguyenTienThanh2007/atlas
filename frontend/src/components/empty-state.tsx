import type { ReactNode } from "react";

export function PageHeader({ title, intro }: { title: string; intro: string }) {
  return (
    <header className="max-w-2xl">
      <h1 className="font-display text-3xl font-light text-mist sm:text-4xl">{title}</h1>
      <p className="mt-3 leading-relaxed text-muted">{intro}</p>
    </header>
  );
}

export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-10 max-w-2xl rounded-lg border border-dashed border-line px-6 py-10">
      <h2 className="text-base font-medium text-mist">{title}</h2>
      <div className="mt-2 text-sm leading-relaxed text-muted">{children}</div>
    </section>
  );
}
