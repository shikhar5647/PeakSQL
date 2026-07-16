/** Brand mark: a peak whose vertices are knowledge-graph nodes. */
export function LogoMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden>
      <defs>
        <linearGradient id="peak-grad" x1="0" y1="32" x2="32" y2="0">
          <stop offset="0" stopColor="#3987e5" />
          <stop offset="1" stopColor="#9085e9" />
        </linearGradient>
      </defs>
      <path
        d="M3 26 L13 8 L19 18 L24 10 L29 26"
        stroke="url(#peak-grad)"
        strokeWidth="2.2"
        strokeLinejoin="round"
        strokeLinecap="round"
        fill="none"
      />
      <circle cx="3" cy="26" r="2" fill="#199e70" />
      <circle cx="13" cy="8" r="2.6" fill="#3987e5" />
      <circle cx="19" cy="18" r="2.2" fill="#6da7ec" />
      <circle cx="24" cy="10" r="2.4" fill="#9085e9" />
      <circle cx="29" cy="26" r="2" fill="#d55181" />
    </svg>
  );
}

export function LogoWordmark() {
  return (
    <span className="logo-row">
      <LogoMark />
      <span className="logo">
        Peak<em>SQL</em>
      </span>
    </span>
  );
}
