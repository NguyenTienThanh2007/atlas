import { connection } from "next/server";
import { getI18n } from "@/i18n";

type State = "ok" | "degraded" | "error" | "offline";

async function readHealth(): Promise<State> {
  await connection(); // read API_URL and call the API per request, never at build time
  const base = process.env.API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/api/v1/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    // The health endpoint answers 200 (all good) or 503 (database down); anything else is an
    // API fault, which must not be reported as a database problem.
    if (res.status === 200) return "ok";
    if (res.status === 503) return "degraded";
    return "error";
  } catch {
    return "offline";
  }
}

const DOT: Record<State, string> = {
  ok: "bg-ok",
  degraded: "bg-brass",
  error: "bg-bad",
  offline: "bg-bad",
};

function Line({ dot, text }: { dot: string; text: string }) {
  return (
    <p role="status" className="flex items-center gap-2 text-xs text-muted">
      <span aria-hidden className={`size-1.5 rounded-full ${dot}`} />
      {text}
    </p>
  );
}

export async function ApiStatus() {
  const [state, { t }] = await Promise.all([readHealth(), getI18n()]);
  return <Line dot={DOT[state]} text={t.status[state]} />;
}

export async function ApiStatusPending() {
  const { t } = await getI18n();
  return <Line dot="bg-line" text={t.status.pending} />;
}
