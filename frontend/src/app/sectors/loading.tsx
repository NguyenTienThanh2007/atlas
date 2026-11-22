import { PageHeader } from "@/components/empty-state";
import { LoadingRows } from "@/components/states";

export default function Loading() {
  return (
    <>
      <PageHeader
        title="Sectors"
        intro="Compare industries across Vietnam's exchanges, from banking to logistics."
      />
      <LoadingRows rows={4} />
    </>
  );
}
