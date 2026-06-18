export type SaathiState = "idle" | "thinking" | "happy" | "concerned";

interface SaathiAvatarProps {
  state?: SaathiState;
  size?: number;
  className?: string;
  /** Accessible label; pass null to mark purely decorative. */
  label?: string | null;
}

/**
 * Saathi — the warm friend. Coral, chatty, knows your meds; never diagnoses.
 * Four states derived from setu-saathi-characters.svg:
 *   idle · thinking (animated dots) · happy · concerned (gentle doctor handoff).
 */
export function SaathiAvatar({
  state = "idle",
  size = 48,
  className,
  label = "Saathi",
}: SaathiAvatarProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="-84 -108 168 220"
      className={className}
      role={label ? "img" : undefined}
      aria-label={label ? `${label} (${state})` : undefined}
      aria-hidden={label ? undefined : true}
    >
      <defs>
        <radialGradient id="saathi-coral" cx="38%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#FA8E72" />
          <stop offset="100%" stopColor="#EC6A50" />
        </radialGradient>
      </defs>

      {/* shared body */}
      <ellipse cx="0" cy="92" rx="48" ry="10" fill="#1C2A2A" opacity="0.07" />
      <ellipse cx="-24" cy="74" rx="16" ry="11" fill="#E2603F" />
      <ellipse cx="24" cy="74" rx="16" ry="11" fill="#E2603F" />
      <ellipse cx="0" cy="0" rx="62" ry="70" fill="url(#saathi-coral)" />
      <ellipse cx="-16" cy="-22" rx="28" ry="21" fill="#FFFFFF" opacity="0.15" />

      {state === "idle" && <IdleFace />}
      {state === "thinking" && <ThinkingFace />}
      {state === "happy" && <HappyFace />}
      {state === "concerned" && <ConcernedFace />}
    </svg>
  );
}

function IdleFace() {
  return (
    <>
      <ellipse cx="-36" cy="16" rx="11" ry="7" fill="#FFD2A8" opacity="0.9" />
      <ellipse cx="36" cy="16" rx="11" ry="7" fill="#FFD2A8" opacity="0.9" />
      <circle cx="-21" cy="-8" r="9" fill="#20302F" />
      <circle cx="21" cy="-8" r="9" fill="#20302F" />
      <circle cx="-24" cy="-11" r="3" fill="#fff" />
      <circle cx="18" cy="-11" r="3" fill="#fff" />
      <path d="M-13 16 Q0 28 13 16" stroke="#20302F" strokeWidth="4" strokeLinecap="round" fill="none" />
    </>
  );
}

function ThinkingFace() {
  return (
    <>
      <ellipse cx="-36" cy="16" rx="11" ry="7" fill="#FFD2A8" opacity="0.9" />
      <ellipse cx="36" cy="16" rx="11" ry="7" fill="#FFD2A8" opacity="0.9" />
      {/* eyes glance up */}
      <circle cx="-19" cy="-13" r="8.5" fill="#20302F" />
      <circle cx="23" cy="-13" r="8.5" fill="#20302F" />
      <circle cx="-21" cy="-16" r="2.8" fill="#fff" />
      <circle cx="21" cy="-16" r="2.8" fill="#fff" />
      <path d="M-7 18 Q0 23 7 18" stroke="#20302F" strokeWidth="4" strokeLinecap="round" fill="none" />
      {/* animated thought dots */}
      <circle cx="40" cy="-58" r="5" fill="#F4795B" className="animate-saathi-dot" style={{ animationDelay: "0ms" }} />
      <circle cx="56" cy="-74" r="6.5" fill="#F4795B" className="animate-saathi-dot" style={{ animationDelay: "180ms" }} />
      <circle cx="72" cy="-92" r="8" fill="#F4795B" className="animate-saathi-dot" style={{ animationDelay: "360ms" }} />
    </>
  );
}

function HappyFace() {
  return (
    <>
      <ellipse cx="-36" cy="18" rx="12" ry="8" fill="#FFC79A" opacity="0.95" />
      <ellipse cx="36" cy="18" rx="12" ry="8" fill="#FFC79A" opacity="0.95" />
      {/* happy ^_^ eyes */}
      <path d="M-30 -6 Q-22 -16 -14 -6" stroke="#20302F" strokeWidth="4" strokeLinecap="round" fill="none" />
      <path d="M14 -6 Q22 -16 30 -6" stroke="#20302F" strokeWidth="4" strokeLinecap="round" fill="none" />
      {/* big smile */}
      <path d="M-19 11 Q0 35 19 11" stroke="#20302F" strokeWidth="4.5" strokeLinecap="round" fill="none" />
      {/* sparkles */}
      <path d="M46 -50 L49 -42 L57 -39 L49 -36 L46 -28 L43 -36 L35 -39 L43 -42 Z" fill="#F4A93C" />
      <path d="M-44 -34 L-42 -29 L-37 -27 L-42 -25 L-44 -20 L-46 -25 L-51 -27 L-46 -29 Z" fill="#F4A93C" opacity="0.8" />
    </>
  );
}

function ConcernedFace() {
  return (
    <>
      <ellipse cx="-36" cy="16" rx="11" ry="7" fill="#FFD2A8" opacity="0.9" />
      <ellipse cx="36" cy="16" rx="11" ry="7" fill="#FFD2A8" opacity="0.9" />
      {/* caring worried brows */}
      <path d="M-30 -20 L-13 -13" stroke="#20302F" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M30 -20 L13 -13" stroke="#20302F" strokeWidth="3.5" strokeLinecap="round" />
      <circle cx="-20" cy="-3" r="8" fill="#20302F" />
      <circle cx="20" cy="-3" r="8" fill="#20302F" />
      <circle cx="-22" cy="-6" r="2.6" fill="#fff" />
      <circle cx="18" cy="-6" r="2.6" fill="#fff" />
      <path d="M-9 20 Q0 16 9 20" stroke="#20302F" strokeWidth="4" strokeLinecap="round" fill="none" />
      {/* gentle 'let's find a doctor' badge */}
      <rect x="34" y="-50" width="28" height="28" rx="9" fill="#0F766E" />
      <rect x="46" y="-44" width="4" height="16" rx="2" fill="#fff" />
      <rect x="40" y="-38" width="16" height="4" rx="2" fill="#fff" />
    </>
  );
}
