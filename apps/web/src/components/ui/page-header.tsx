import { ScreenHeader } from "@/components/ui/screen-header";

/** Title + subtitle header (sentence case). */
export function PageHeader({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <header className="mb-5">
      {eyebrow && <p className="mb-1 text-label text-primary-light">{eyebrow}</p>}
      <ScreenHeader mode="title" title={title} subtitle={subtitle} />
    </header>
  );
}
