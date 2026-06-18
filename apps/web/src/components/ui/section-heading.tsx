export function SectionHeading({ title, className }: { title: string; className?: string }) {
  return (
    <div className={`mb-2.5 flex items-center gap-2 px-0.5 ${className ?? ""}`}>
      <h2 className="font-display text-sm font-semibold text-primary">{title}</h2>
      <div className="h-px flex-1 bg-border" />
    </div>
  );
}
