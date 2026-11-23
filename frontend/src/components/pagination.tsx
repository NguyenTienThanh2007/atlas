import Link from "next/link";
import { getI18n } from "@/i18n";

type Props = {
  basePath: string; // app path, without the language prefix
  params: Record<string, string | undefined>;
  page: number;
  pageSize: number;
  total: number;
};

export async function Pagination({ basePath, params, page, pageSize, total }: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  const { t, href: localHref } = await getI18n();
  const base = localHref(basePath);
  const href = (p: number) => {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v) sp.set(k, v);
    if (p > 1) sp.set("page", String(p));
    const qs = sp.toString();
    return qs ? `${base}?${qs}` : base;
  };
  const link = "rounded-md border border-line px-3 py-1.5 text-sm text-mist hover:bg-white/[0.04]";
  return (
    <nav aria-label={t.pagination.label} className="mt-6 flex max-w-3xl items-center justify-between">
      {page > 1 ? <Link className={link} href={href(page - 1)}>{t.pagination.previous}</Link> : <span />}
      <span className="text-sm text-muted">{t.pagination.pageOf(page, pages)}</span>
      {page < pages ? <Link className={link} href={href(page + 1)}>{t.pagination.next}</Link> : <span />}
    </nav>
  );
}
