import { redirect } from "next/navigation";

export default async function ShareAliasPage({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const { token } = await params;
  const sp = await searchParams;
  const q = sp.view ? `?view=${sp.view}` : "";
  redirect(`/brief/${token}${q}`);
}
