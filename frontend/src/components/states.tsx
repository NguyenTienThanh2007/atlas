import Link from "next/link";
import type { ReactNode } from "react";

export function ApiErrorState({ title, message }: { title: string; message: string }) {
  return (
    <section
      role="alert"
      className="mt-10 max-w-2xl rounded-lg border border-bad/40 bg-bad/5 px-6 py-8"
    >
      <h2 className="text-base font-medium text-mist">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-muted">{message}</p>
    </section>
  );
}

export function SampleBadge() {
  return (
    <span
      title="Fictional record from the ATLAS sample fixture. Not a real company."
      className="rounded border border-brass/50 px-1.5 py-0.5 text-[11px] font-medium text-brass"
    >
      Sample data
    </span>
  );
}

export function LoadingRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="mt-10 max-w-3xl space-y-3" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading…</span>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-14 animate-pulse rounded-lg bg-white/[0.04] motion-reduce:animate-none" />
      ))}
    </div>
  );
}

export function BackLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="text-sm text-muted hover:text-mist">
      ← {children}
    </Link>
  );
}
