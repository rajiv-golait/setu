import { SetuAvatar } from "@/components/characters/setu-avatar";
import { BackLink } from "@/components/ui/back-link";
import { cn } from "@/lib/cn";

type GreetingProps = {
  mode: "greeting";
  dateLine: string;
  name: string;
  tagline?: string;
  showAvatar?: boolean;
};

type TitleProps = {
  mode?: "title";
  title: string;
  subtitle?: string;
};

type ToolbarProps = {
  mode: "toolbar";
  title: string;
  backHref?: string;
  backLabel?: string;
  trailing?: React.ReactNode;
};

type ImmersiveProps = {
  mode: "immersive";
  title: string;
  className?: string;
};

export function ScreenHeader(props: GreetingProps | TitleProps | ToolbarProps | ImmersiveProps) {
  if (props.mode === "greeting") {
    return (
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-label text-text-muted">{props.dateLine}</p>
          <h1 className="font-display text-2xl font-semibold tracking-tight">Namaste, {props.name}</h1>
          {props.tagline && <p className="mt-0.5 text-sm text-text-muted">{props.tagline}</p>}
        </div>
        {props.showAvatar !== false && <SetuAvatar size={56} label="SETU, your health keeper" />}
      </div>
    );
  }

  if (props.mode === "toolbar") {
    return (
      <header className="mb-4">
        <BackLink href={props.backHref} label={props.backLabel} className="mb-2" />
        <div className="flex items-center justify-between gap-2">
          <h1 className="font-display text-xl font-semibold text-text">{props.title}</h1>
          {props.trailing}
        </div>
      </header>
    );
  }

  if (props.mode === "immersive") {
    return (
      <h1
        className={cn(
          "font-display text-[22px] font-semibold tracking-tight text-text",
          props.className,
        )}
      >
        {props.title}
      </h1>
    );
  }

  return (
    <div>
      <h1 className="font-display text-[22px] font-semibold tracking-tight text-text">{props.title}</h1>
      {props.subtitle && <p className="mt-1 text-sm text-text-muted">{props.subtitle}</p>}
    </div>
  );
}
