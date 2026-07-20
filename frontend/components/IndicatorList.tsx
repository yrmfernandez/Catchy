import { Badge } from "@/components/ui/Badge";
import { severityVar } from "@/lib/bands";
import type { Indicator } from "@/lib/types";

/** The explainable core: every rule/intel finding that contributed points. */
export function IndicatorList({ indicators }: { indicators: Indicator[] }) {
  if (indicators.length === 0) {
    return (
      <p className="m-0 text-sm text-ink-muted">
        No suspicious indicators fired for this message.
      </p>
    );
  }

  return (
    <ul className="m-0 flex list-none flex-col gap-3 p-0">
      {indicators.map((ind, i) => (
        <li key={`${ind.id}-${i}`} className="flex gap-3">
          <span
            className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ background: severityVar[ind.severity] }}
            aria-hidden
          />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">{ind.title}</span>
              <Badge color={severityVar[ind.severity]}>{ind.severity}</Badge>
              {ind.points > 0 ? (
                <span className="mono text-xs text-ink-muted">+{ind.points}</span>
              ) : null}
            </div>
            <p className="m-0 mt-0.5 text-sm text-ink-muted">{ind.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
