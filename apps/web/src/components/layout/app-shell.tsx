import { BottomNav } from "./bottom-nav";

export function AppShell({
  children,
  hideNav = false,
}: {
  children: React.ReactNode;
  hideNav?: boolean;
}) {
  return (
    <div className="mx-auto min-h-screen max-w-lg bg-surface">
      <main className={hideNav ? "pb-6" : "pb-24"}>{children}</main>
      {!hideNav && <BottomNav />}
    </div>
  );
}
