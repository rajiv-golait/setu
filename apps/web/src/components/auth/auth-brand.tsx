import Link from "next/link";

export function AuthBrand({
  badge,
  title,
  subtitle,
  welcomeHref,
}: {
  badge: string;
  title: string;
  subtitle: string;
  welcomeHref?: string;
}) {
  const mark = (
    // Plain img: brand mark is served directly (no next/image optimizer dependency).
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/setu-logo.webp"
      alt="Setu"
      width={76}
      height={76}
      className="h-[76px] w-[76px] object-contain"
    />
  );
  return (
    <div className="mb-8 text-center">
      <div className="mx-auto flex h-[76px] w-[76px] items-center justify-center">
        {welcomeHref ? (
          <Link href={welcomeHref} aria-label="Setu home">
            {mark}
          </Link>
        ) : (
          mark
        )}
      </div>
      <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-primary-light">{badge}</p>
      <h1 className="mt-1 font-display text-[26px] font-semibold tracking-tight">{title}</h1>
      <p className="mx-auto mt-2 max-w-sm text-sm text-text-muted">{subtitle}</p>
    </div>
  );
}
