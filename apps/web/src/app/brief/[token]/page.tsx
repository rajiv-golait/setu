import { DoctorSnapshot } from "@/components/doctor/doctor-snapshot";
import { getBriefSnapshot } from "@/lib/api";
import { ApiError } from "@/lib/api";

export default async function PublicBriefPage({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<{ view?: string }>;
}) {
  const { token } = await params;
  const { view } = await searchParams;

  try {
    const snapshot = await getBriefSnapshot(
      token,
      view === "specialist" ? "specialist" : undefined,
    );
    return <DoctorSnapshot snapshot={snapshot} />;
  } catch (e) {
    const expired =
      e instanceof ApiError && (e.status === 404 || e.message.toLowerCase().includes("expired"));
    return <DoctorSnapshot expired={expired} />;
  }
}
