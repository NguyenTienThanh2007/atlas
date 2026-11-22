import Link from "next/link";

type Props = {
  basePath: string;
  params: Record<string, string | undefined>;
  page: number;
  pageSize: number;
  total: number;
};

export function Pagination({ basePath, params, page, pageSize, total }: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  const href = (p: number) => {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v) sp.set(k, v);
    if (p > 1) sp.set("page", String(p));
    const qs = sp.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };
  const link = "rounded-md border border-line px-3 py-1.5 text-sm text-mist hover:bg-white/[0.04]";
  return (
    <nav aria-label="Pagination" className="mt-6 flex max-w-3xl items-center justify-between">
      {page > 1 ? <Link className={link} href={href(page - 1)}>Previous</Link> : <span />}
      <span className="text-sm text-muted">
        Page {page} of {pages}
      </span>
      {page < pages ? <Link className={link} href={href(page + 1)}>Next</Link> : <span />}
    </nav>
  );
}
