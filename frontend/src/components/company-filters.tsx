import Link from "next/link";
import { getI18n } from "@/i18n";
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
export async function CompanyFilters({ q, sector, exchange, sectors, exchanges }: Props) {
  const { locale, t, href } = await getI18n();
  const action = href("/companies");
  return (
    <form
      role="search"
      action={action}
      className="mt-8 flex max-w-3xl flex-col gap-3 sm:flex-row sm:items-end"
    >
      <label className="flex flex-1 flex-col gap-1 text-xs text-muted">
        {t.companies.query}
        <input name="q" type="search" defaultValue={q} maxLength={100} className={field} />
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted">
        {t.companies.sector}
        <select name="sector" defaultValue={sector ?? ""} className={field}>
          <option value="">{t.companies.allSectors}</option>
          {sectors.map((s) => (
            <option key={s.code} value={s.code}>
              {locale === "vi" ? s.name_vi : s.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted">
        {t.companies.exchange}
        <select name="exchange" defaultValue={exchange ?? ""} className={field}>
          <option value="">{t.companies.allExchanges}</option>
          {exchanges.map((e) => (
            <option key={e.code} value={e.code}>
              {e.code}
            </option>
          ))}
        </select>
      </label>
      <button
        type="submit"
        className="whitespace-nowrap rounded-md border border-brass/60 px-4 py-2 text-sm text-mist hover:bg-brass/10"
      >
        {t.companies.search}
      </button>
      {(q || sector || exchange) && (
        <Link href={action} className="whitespace-nowrap py-2 text-sm text-muted hover:text-mist">
          {t.companies.clear}
        </Link>
      )}
    </form>
  );
}
