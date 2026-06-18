interface SetuAvatarProps {
  size?: number;
  className?: string;
  /** Accessible label; pass null to mark purely decorative. */
  label?: string | null;
}

/**
 * SETU — the calm keeper. Teal, steady, holds your whole health memory.
 * Derived from setu-saathi-characters.svg.
 */
export function SetuAvatar({ size = 56, className, label = "SETU" }: SetuAvatarProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="-90 -110 180 230"
      className={className}
      role={label ? "img" : undefined}
      aria-label={label ?? undefined}
      aria-hidden={label ? undefined : true}
    >
      <defs>
        <radialGradient id="setu-teal" cx="38%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#1FBEAB" />
          <stop offset="100%" stopColor="#0F766E" />
        </radialGradient>
      </defs>
      <ellipse cx="0" cy="96" rx="52" ry="11" fill="#1C2A2A" opacity="0.07" />
      <ellipse cx="-26" cy="80" rx="17" ry="12" fill="#0B5E57" />
      <ellipse cx="26" cy="80" rx="17" ry="12" fill="#0B5E57" />
      {/* sprout = life/growth */}
      <path d="M0 -78 L0 -94" stroke="#0F766E" strokeWidth="4" strokeLinecap="round" />
      <circle cx="0" cy="-99" r="6.5" fill="#F4A93C" />
      <ellipse cx="0" cy="0" rx="66" ry="74" fill="url(#setu-teal)" />
      <ellipse cx="-18" cy="-24" rx="30" ry="22" fill="#FFFFFF" opacity="0.16" />
      <ellipse cx="-38" cy="18" rx="11" ry="7" fill="#BFEFE6" opacity="0.85" />
      <ellipse cx="38" cy="18" rx="11" ry="7" fill="#BFEFE6" opacity="0.85" />
      {/* calm closed eyes */}
      <path d="M-30 -8 Q-21 0 -12 -8" stroke="#1C2A2A" strokeWidth="4" strokeLinecap="round" fill="none" />
      <path d="M12 -8 Q21 0 30 -8" stroke="#1C2A2A" strokeWidth="4" strokeLinecap="round" fill="none" />
      <path d="M-12 14 Q0 22 12 14" stroke="#1C2A2A" strokeWidth="4" strokeLinecap="round" fill="none" />
      {/* belly: health-memory heartbeat badge */}
      <rect x="-27" y="30" width="54" height="30" rx="10" fill="#FFFFFF" opacity="0.92" />
      <path
        d="M-18 45 L-8 45 L-3 36 L4 54 L9 45 L18 45"
        stroke="#0F766E"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
