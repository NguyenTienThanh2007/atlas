import type { Dictionary } from "@/i18n";
import { figureHref, type FigureSource } from "@/lib/provenance";

/** WS3: the document and page one figure comes from. Missing pages and non-linkable documents are
 * stated, never guessed; the link opens the document at the figure's page. */
export function FigureSourceLine({
  metric,
  source,
  labels,
}: {
  metric: string;
  source: FigureSource;
  labels: Dictionary["company"]["figure"];
}) {
  const title = source.document_title ?? labels.untitled;
  const href = figureHref(source);
  const page = source.page === null ? labels.noPage : labels.page(source.page);
  return (
    <span className="mt-0.5 block text-xs leading-snug break-words text-muted">
      {labels.source}:{" "}
      {href ? (
        <a
          href={href}
          rel="noopener noreferrer"
          target="_blank"
          aria-label={labels.open(metric, title, source.page)}
          className="text-mist underline decoration-line underline-offset-2 hover:decoration-mist"
        >
          {title} · {page}
        </a>
      ) : (
        <>
          {title} · {page} · <span className="text-brass">{labels.noLink}</span>
        </>
      )}
    </span>
  );
}
