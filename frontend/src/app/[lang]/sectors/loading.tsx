import { PageHeader } from "@/components/empty-state";
import { LoadingRows } from "@/components/states";
import { getI18n } from "@/i18n";

export default async function Loading() {
  const { t } = await getI18n();
  return (
    <>
      <PageHeader title={t.sectors.title} intro={t.sectors.intro} />
      <LoadingRows rows={4} />
    </>
  );
}
