import Link from "next/link";
import { getI18n } from "@/i18n";
import type { CompanyListItem } from "@/lib/api";
import { SampleBadge } from "./states";

export async function CompanyList({ companies }: { companies: CompanyListItem[] }) {
  const { locale, t, href } = await getI18n();
  return (
    <ul className="mt-8 max-w-3xl divide-y divide-line border-y border-line">
      {companies.map((c) => (
        <li key={c.id}>
          <Link
            href={href(`/companies/${c.id}`)}
            className="flex flex-col gap-1 px-1 py-4 transition-colors hover:bg-white/[0.03] sm:flex-row sm:items-center sm:gap-6"
          >
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="flex items-center gap-2 text-mist">
                {c.short_name}
                {c.is_sample && <SampleBadge />}
              </span>
              <span className="truncate text-sm text-muted">{c.legal_name}</span>
            </span>
            <span className="text-sm text-muted sm:w-44">
              {locale === "vi" ? c.sector.name_vi : c.sector.name}
            </span>
            <span className="flex flex-wrap gap-1.5 sm:w-48 sm:justify-end">
              {c.securities.map((s) => (
                <span
                  key={s.id}
                  className={`rounded border border-line px-1.5 py-0.5 text-xs ${
                    s.listing_status === "delisted" ? "text-muted line-through" : "text-mist"
                  }`}
                  title={`${s.exchange.name} · ${t.glossary.listingStatus[s.listing_status]}`}
                >
                  {s.ticker} <span className="text-muted">{s.exchange.code}</span>
                </span>
              ))}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
