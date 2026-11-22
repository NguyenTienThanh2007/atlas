import Link from "next/link";
import type { Exchange, Sector } from "@/lib/api";

type Props = {
  q?: string;
  sector?: string;
  exchange?: string;
  sectors: Sector[];
  exchanges: Exchange[];
};

const field =
  "rounded-md border border-line bg-charcoal px-3 py-2 text-sm text-mist placeholder:text-muted";

// A plain GET form: search and filters work without client-side JavaScript.
export function CompanyFilters({ q, sector, exchange, sectors, exchanges }: Props) {
  return (
    <form
      role="search"
      action="/companies"
      className="mt-8 flex max-w-3xl flex-col gap-3 sm:flex-row sm:items-end"
    >
      <label className="flex flex-1 flex-col gap-1 text-xs text-muted">
        Ticker or name
        <input name="q" type="search" defaultValue={q} maxLength={100} className={field} />
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted">
        Sector
        <select name="sector" defaultValue={sector ?? ""} className={field}>
          <option value="">All sectors</option>
          {sectors.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted">
        Exchange
        <select name="exchange" defaultValue={exchange ?? ""} className={field}>
          <option value="">All exchanges</option>
          {exchanges.map((e) => (
            <option key={e.code} value={e.code}>
              {e.code}
            </option>
          ))}
        </select>
      </label>
      <button
        type="submit"
        className="rounded-md border border-brass/60 px-4 py-2 text-sm text-mist hover:bg-brass/10"
      >
        Search
      </button>
      {(q || sector || exchange) && (
        <Link href="/companies" className="py-2 text-sm text-muted hover:text-mist">
          Clear
        </Link>
      )}
    </form>
  );
}
