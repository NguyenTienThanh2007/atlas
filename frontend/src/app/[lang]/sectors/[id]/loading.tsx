import { BackLink, LoadingRows } from "@/components/states";
import { getI18n } from "@/i18n";

export default async function Loading() {
  const { t } = await getI18n();
  return (
    <>
      <BackLink path="/sectors">{t.sector.back}</BackLink>
      <div className="mt-6 h-10 w-64 animate-pulse rounded bg-white/[0.04] motion-reduce:animate-none" />
      <LoadingRows rows={3} />
    </>
  );
}
