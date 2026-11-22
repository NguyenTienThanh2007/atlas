import { connection } from "next/server";
import { buildUrl, fetchJson, type ApiResult } from "./api-core";

export * from "./api-core";

/** Server-side GET against the ATLAS API, evaluated per request (never at build time). */
export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
): Promise<ApiResult<T>> {
  await connection();
  return fetchJson<T>(buildUrl(process.env.API_URL ?? "http://localhost:8000", path, params));
}
