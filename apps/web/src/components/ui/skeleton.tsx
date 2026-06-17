/** Loading skeletons — design ref: SetuSkeleton.dc.html (shimmer, no spinners). */

function Skel({ className }: { className?: string }) {
  return <div className={`animate-setu-shimmer rounded-lg bg-[#E8E8E2] ${className ?? ""}`} />;
}

export function BriefSkeleton() {
  return (
    <div className="px-[18px] py-[18px]">
      <Skel className="h-[13px] w-[120px]" />
      <Skel className="mt-2 h-6 w-[200px]" />
      <Skel className="mt-[18px] h-24 w-full rounded-hero" />
      <Skel className="mt-3.5 h-16 w-full rounded-card" />
      <Skel className="mt-5 h-[13px] w-[140px]" />
      <div className="mt-3 flex flex-col gap-2.5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-card border border-[#EFEFE9] bg-surface-raised p-4">
            <div className="flex justify-between">
              <Skel className="h-4 w-[90px]" />
              <Skel className="h-5 w-[54px]" />
            </div>
            <Skel className="mt-2.5 h-[11px] w-[130px]" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function MemorySkeleton() {
  return (
    <div className="px-5 py-5">
      <Skel className="h-7 w-[180px]" />
      <Skel className="mt-2 h-4 w-[240px]" />
      <div className="mt-[18px] grid grid-cols-2 gap-2.5">
        <Skel className="h-[86px] rounded-card" />
        <Skel className="h-[86px] rounded-card" />
      </div>
      <Skel className="mt-3 h-[170px] w-full rounded-card" />
      <Skel className="mt-5 h-[13px] w-[100px]" />
      <div className="mt-3.5 flex flex-col gap-3.5">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <Skel className="mt-1 h-3 w-3 shrink-0 rounded-full" />
            <div className="flex-1">
              <Skel className="h-2.5 w-20" />
              <Skel className="mt-2 h-4 w-[170px]" />
              <Skel className="mt-2 h-[11px] w-[120px]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
