import { bandLabel, bandVar } from "@/lib/bands";
import type { Band } from "@/lib/types";

/** Semicircular gauge: the headline 0-100 fused score, coloured by band. */
export function ScoreGauge({
  score,
  band,
  size = 180,
}: {
  score: number;
  band: Band;
  size?: number;
}) {
  const radius = 70;
  const length = Math.PI * radius; // semicircle arc length
  const progress = length * (1 - Math.min(Math.max(score, 0), 100) / 100);
  const colour = bandVar[band];

  return (
    <div className="flex flex-col items-center">
      <svg
        width={size}
        height={size * 0.62}
        viewBox="0 0 180 112"
        role="img"
        aria-label={`Risk score ${score} out of 100, ${bandLabel[band]}`}
      >
        <path
          d="M 20 90 A 70 70 0 0 1 160 90"
          fill="none"
          stroke="var(--line)"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d="M 20 90 A 70 70 0 0 1 160 90"
          fill="none"
          stroke={colour}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={length}
          strokeDashoffset={progress}
          style={{ transition: "stroke-dashoffset 600ms ease, stroke 300ms ease" }}
        />
        <text
          x="90"
          y="80"
          textAnchor="middle"
          fontSize="34"
          fontWeight="700"
          fill="var(--ink)"
        >
          {score}
        </text>
        <text x="90" y="100" textAnchor="middle" fontSize="11" fill="var(--ink-muted)">
          out of 100
        </text>
      </svg>
      <span
        className="mt-1 text-sm font-semibold uppercase tracking-wide"
        style={{ color: colour }}
      >
        {bandLabel[band]}
      </span>
    </div>
  );
}
