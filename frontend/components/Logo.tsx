// Catchy brand mark: a shield (security) enclosing a fishhook (phishing —
// the thing we "catch"). All colours come from CSS custom properties so the
// same component renders correctly in both light and dark themes.

type LogoMarkProps = { size?: number };

export function LogoMark({ size = 28 }: LogoMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="Catchy logo"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="catchy-shield" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--accent-2)" />
          <stop offset="1" stopColor="var(--accent)" />
        </linearGradient>
      </defs>
      {/* shield */}
      <path
        d="M16 3 L26 6.5 C26.6 6.7 27 7.2 27 8 V15 C27 22 22.4 26.8 16 29 C9.6 26.8 5 22 5 15 V8 C5 7.2 5.4 6.7 6 6.5 Z"
        fill="url(#catchy-shield)"
      />
      {/* fishhook, knocked out of the shield */}
      <circle cx="17.5" cy="9" r="1.05" fill="var(--logo-knockout)" />
      <path
        d="M17.5 10 V16 A2.3 2.3 0 1 1 12.9 16 M12.9 16 L11.9 14.9"
        fill="none"
        stroke="var(--logo-knockout)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

type LogoProps = { size?: number; withWordmark?: boolean };

export function Logo({ size = 28, withWordmark = true }: LogoProps) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 9 }}>
      <LogoMark size={size} />
      {withWordmark && (
        <span
          style={{
            fontSize: 18,
            fontWeight: 650,
            letterSpacing: "-0.02em",
            color: "var(--ink)",
          }}
        >
          Catchy
        </span>
      )}
    </span>
  );
}
