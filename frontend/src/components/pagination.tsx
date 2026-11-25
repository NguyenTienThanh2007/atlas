import Link from "next/link";
import { getI18n } from "@/i18n";
import { pageRange } from "@/lib/api";

type Props = {
  basePath: string; // app path, without the language prefix
  params: Record<string, string | undefined>; // other query state to keep (filters, other lists' pages)
  page: number;
  pageSize: number;
  total: number;
  param?: string; // query parameter holding this list's page; lets one page carry several lists
  anchor?: string; // fragment to return to the list after navigating
  showRange?: boolean; // always say which items are shown ("Đang hiển thị 1–20 / 85"), never truncate silently
  label?: string; // accessible name when a page has more than one paginated list
};

export async function Pagination({
  basePath,
  params,
  page,
  pageSize,
  total,
  param = "page",
  anchor,
  showRange = false,
  label,
}: Props) {
  const { from, to, pages, beyond } = pageRange(page, pageSize, total);
  if (total === 0 || (pages <= 1 && !showRange)) return null;
  const { t, href: localHref } = await getI18n();
  const base = localHref(basePath);
  const href = (p: number) => {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v && k !== param) sp.set(k, v);
    if (p > 1) sp.set(param, String(p));
    const qs = sp.toString();
    return `${qs ? `${base}?${qs}` : base}${anchor ? `#${anchor}` : ""}`;
  };
  const link = "rounded-md border border-line px-3 py-1.5 text-sm text-mist hover:bg-white/[0.04]";
  const status = !showRange
    ? t.pagination.pageOf(page, pages)
    : beyond
      ? t.pagination.beyond(page, total)
      : t.pagination.range(from, to, total);
  return (
    <nav aria-label={label ?? t.pagination.label} className="mt-6 flex max-w-3xl items-center justify-between gap-3">
      {page > 1 ? (
        <Link className={link} href={href(beyond ? pages : page - 1)}>
          {t.pagination.previous}
        </Link>
      ) : (
        <span />
      )}
      <span className="text-center text-sm text-muted" aria-live="polite">
        {status}
      </span>
      {page < pages ? (
        <Link className={link} href={href(page + 1)}>
          {t.pagination.next}
        </Link>
      ) : (
        <span />
      )}
    </nav>
  );
}
