import Link from "next/link";
import type { ReactNode } from "react";
import { getI18n } from "@/i18n";

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

export async function SampleBadge() {
  const { t } = await getI18n();
  return (
    <span
      title={t.common.sampleTitle}
      className="rounded border border-brass/50 px-1.5 py-0.5 text-[11px] font-medium text-brass"
    >
      {t.common.sampleBadge}
    </span>
  );
}

export async function LoadingRows({ rows = 5 }: { rows?: number }) {
  const { t } = await getI18n();
  return (
    <div className="mt-10 max-w-3xl space-y-3" aria-busy="true" aria-live="polite">
      <span className="sr-only">{t.common.loading}</span>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-14 animate-pulse rounded-lg bg-white/[0.04] motion-reduce:animate-none" />
      ))}
    </div>
  );
}

/** `path` is the app path ("/companies"); the link keeps the current language. */
export async function BackLink({ path, children }: { path: string; children: ReactNode }) {
  const { href } = await getI18n();
  return (
    <Link href={href(path)} className="text-sm text-muted hover:text-mist">
      ← {children}
    </Link>
  );
}
