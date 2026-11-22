import { connection } from "next/server";

type Health = { status: "ok" | "error"; checks: { database: { status: "ok" | "error" } } };
type State = "ok" | "degraded" | "offline";

async function readHealth(): Promise<State> {
  await connection(); // read API_URL and call the API per request, never at build time
  const base = process.env.API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/api/v1/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    // 503 still carries a body describing which dependency failed.
    const body = (await res.json()) as Health;
    return body.status === "ok" ? "ok" : "degraded";
  } catch {
    return "offline";
  }
}

const LABEL: Record<State, string> = {
  ok: "API and database online",
  degraded: "API online, database unreachable",
  offline: "API unreachable",
};

const DOT: Record<State, string> = {
  ok: "bg-ok",
  degraded: "bg-brass",
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
  const state = await readHealth();
  return <Line dot={DOT[state]} text={LABEL[state]} />;
}

export function ApiStatusPending() {
  return <Line dot="bg-line" text="Checking services…" />;
}
