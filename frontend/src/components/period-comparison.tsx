import Link from "next/link";
import { FigureSourceLine } from "@/components/figure-source";
import { Pagination } from "@/components/pagination";
import { errorText, getI18n, unitText, type Dictionary, type Locale } from "@/i18n";
import {
  COMPARISON_TYPES,
  comparisonLabel,
  formatDate,
  formatDecimal,
  formatFixed,
  percentText,
  type ApiResult,
  type ComparisonSide,
  type ComparisonType,
  type Page,
  type PeriodComparison,
} from "@/lib/api";

export const COMPARISONS_PAGE_SIZE = 20;
// Neutral shapes (W3-D5): the word next to the arrow carries the meaning; no colour does.
const ARROW = { up: "▲", down: "▼", unchanged: "=" } as const;

type Props = {
  companyId: string;
  result: ApiResult<Page<PeriodComparison>>;
  kind: ComparisonType;
  scope: "consolidated" | "separate" | undefined;
  page: number;
  kept: Record<string, string | undefined>; // every list's query state, this one's included
};

/** WS4-3: changes between periods, computed by the API from reported figures. Server-rendered;
 * the controls are plain links, so the choice survives reloads and the language switch. */
export async function PeriodComparisons({ companyId, result, kind, scope, page, kept }: Props) {
  const { locale, t, href } = await getI18n();
  const k = t.company.comparison;
  const base = `/companies/${companyId}`;
  const target = (next: Record<string, string | undefined>) => {
    const sp = new URLSearchParams();
    for (const [key, v] of Object.entries({
      ...kept,
      comparisons_page: undefined,
      ...next,
    }))
      if (v) sp.set(key, v);
    const qs = sp.toString();
    return `${href(base)}${qs ? `?${qs}` : ""}#comparisons`;
  };
  const option = (active: boolean, label: string, to: string) => (
    <Link
      key={label}
      href={to}
      aria-current={active ? "page" : undefined}
      className={`rounded-md border px-3 py-1.5 text-sm ${
        active ? "border-mist text-mist" : "border-line text-muted hover:bg-white/[0.04]"
      }`}
    >
      {label}
    </Link>
  );
  const scopes = [undefined, "consolidated", "separate"] as const;

  return (
    <section id="comparisons" className="mt-12 scroll-mt-6">
      <h2 className="mb-4 font-display text-xl font-light text-mist">{k.title}</h2>
      <p className="mb-4 max-w-prose text-xs leading-relaxed text-muted">{k.note}</p>
      <nav aria-label={k.typeLabel} className="flex flex-wrap gap-2">
        {COMPARISON_TYPES.map((c) =>
          option(c === kind, k.type[c], target({ compare: c === "annual_yoy" ? undefined : c })),
        )}
      </nav>
      <nav aria-label={k.scopeLabel} className="mt-2 flex flex-wrap gap-2">
        {scopes.map((s) => option(s === scope, s ? t.glossary.scope[s] : k.allScopes, target({ compare_scope: s })))}
      </nav>
      {kind === "quarterly_qoq" && <p className="mt-3 max-w-prose text-xs text-brass">{k.seasonality}</p>}
      <div className="mt-4">
        {!result.ok ? (
          <p className="text-sm text-bad">{errorText(t, result)}</p>
        ) : result.data.total === 0 ? (
          <p className="text-sm text-muted">{k.none}</p>
        ) : (
          <div className="sm:overflow-x-auto">
            <table className="block w-full text-left text-sm sm:table">
              <thead className="hidden text-xs text-muted sm:table-header-group">
                <tr>
                  <th className="py-2 pr-4 font-normal">{k.metric}</th>
                  <th className="py-2 pr-4 font-normal">{k.current}</th>
                  <th className="py-2 pr-4 font-normal">{k.previous}</th>
                  <th className="py-2 pr-4 font-normal">{k.change}</th>
                  <th className="py-2 font-normal">{k.percent}</th>
                </tr>
              </thead>
              {result.data.items.map((r) => (
                <ComparisonRow key={`${r.current.statement_id}-${r.metric_code}`} r={r} locale={locale} t={t} />
              ))}
            </table>
          </div>
        )}
      </div>
      {result.ok && (
        <Pagination
          basePath={base}
          params={kept}
          page={page}
          pageSize={COMPARISONS_PAGE_SIZE}
          total={result.data.total}
          param="comparisons_page"
          anchor="comparisons"
          label={k.pages}
          showRange
        />
      )}
    </section>
  );
}

const CELL = "block py-1 break-words sm:table-cell sm:py-3 sm:pr-4 sm:align-top";

function ComparisonRow({ r, locale, t }: { r: PeriodComparison; locale: Locale; t: Dictionary }) {
  const k = t.company.comparison;
  const kc = t.company.calculated;
  const vi = locale === "vi";
  const name = vi ? r.metric_name_vi : r.metric_name_en;
  const verification = comparisonLabel(r);
  const reason = r.reason ? k.reason[r.reason] : null;
  const head = (label: string) => <span className="block text-xs text-muted sm:hidden">{label}</span>;
  const change = r.absolute_change !== null && r.direction !== null && (
    <span className="tabular-nums text-mist">
      <span aria-hidden="true">{ARROW[r.direction]}</span> {k.direction[r.direction]}{" "}
      {formatDecimal(r.absolute_change, locale)} <span className="text-xs text-muted">{unitText(t, r.unit)}</span>
    </span>
  );
  return (
    <tbody className="block border-t border-line py-3 sm:table-row-group sm:py-0">
      <tr className="block sm:table-row">
        <th scope="row" className={`${CELL} font-medium text-mist`}>
          {name}
          <span className="block text-xs font-normal text-muted">
            {t.glossary.statementType[r.statement_type]} · {t.glossary.scope[r.scope]}
          </span>
          {verification && (
            <span className="block text-xs font-normal text-muted">{kc.verification[verification]}</span>
          )}
        </th>
        <td className={CELL}>
          {head(k.current)}
          <SideValue side={r.current} unit={r.unit} locale={locale} t={t} />
        </td>
        <td className={CELL}>
          {head(k.previous)}
          {r.previous ? (
            <SideValue side={r.previous} unit={r.unit} locale={locale} t={t} />
          ) : (
            <span className="text-muted">{k.noValue}</span>
          )}
        </td>
        {r.status === "not_comparable" ? (
          <td className={CELL} colSpan={2}>
            <span className="text-brass">{reason}</span>
          </td>
        ) : (
          <>
            <td className={CELL}>
              {head(k.change)}
              {change}
            </td>
            <td className={CELL}>
              {head(k.percent)}
              {r.growth_percent !== null ? (
                <span className="font-medium text-mist tabular-nums">{percentText(r.growth_percent, locale)}</span>
              ) : (
                <span className="text-brass">{reason}</span>
              )}
            </td>
          </>
        )}
      </tr>
      <tr className="block sm:table-row">
        <td colSpan={5} className="block pb-3 sm:table-cell">
          <details className="text-xs text-muted">
            <summary className="cursor-pointer text-mist underline decoration-line underline-offset-2">
              {kc.howTo}
            </summary>
            <p className="mt-2">{vi ? r.formula_text_vi : r.formula_text_en}</p>
            {r.growth_percent !== null && r.growth_value !== null && (
              <p className="mt-1 tabular-nums">
                {k.fullValue(formatFixed(r.growth_percent, locale), formatFixed(r.growth_value, locale))}
              </p>
            )}
            <ul className="mt-2 space-y-2">
              {(
                [
                  [k.current, r.current],
                  [k.previous, r.previous],
                ] as const
              ).map(
                ([label, side]) =>
                  side && (
                    <li key={label}>
                      <span className="text-mist">{label}</span>:{" "}
                      {t.company.period(side.fiscal_year, side.fiscal_quarter)} ·{" "}
                      {t.company.range(formatDate(side.period_start, locale), formatDate(side.period_end, locale))}
                      {side.revision > 1 && <span className="text-brass"> · {t.company.restated(side.revision)}</span>}
                      {side.value !== null && side.source ? (
                        <>
                          {" "}
                          ·{" "}
                          <span className="tabular-nums">
                            {formatDecimal(side.value, locale)} {unitText(t, r.unit)}
                          </span>
                          <FigureSourceLine metric={name} source={side.source} labels={t.company.figure} />
                        </>
                      ) : (
                        <> · {k.noValue}</>
                      )}
                    </li>
                  ),
              )}
            </ul>
          </details>
        </td>
      </tr>
    </tbody>
  );
}

function SideValue({ side, unit, locale, t }: { side: ComparisonSide; unit: string; locale: Locale; t: Dictionary }) {
  return (
    <>
      <span className="block text-xs text-muted">
        {t.company.period(side.fiscal_year, side.fiscal_quarter)}
        {side.revision > 1 && <span className="text-brass"> · {t.company.restated(side.revision)}</span>}
      </span>
      {side.value !== null ? (
        <span className="tabular-nums text-mist">
          {formatDecimal(side.value, locale)} <span className="text-xs text-muted">{unitText(t, unit)}</span>
        </span>
      ) : (
        <span className="text-muted">{t.company.comparison.noValue}</span>
      )}
    </>
  );
}
