import type { Band, Severity } from "./types";

/** Risk bands and severities share one visual language across the app. */
export const bandVar: Record<Band, string> = {
  low: "var(--band-low)",
  medium: "var(--band-medium)",
  high: "var(--band-high)",
  critical: "var(--band-critical)",
};

export const bandLabel: Record<Band, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
  critical: "Critical risk",
};

export const severityVar: Record<Severity, string> = {
  info: "var(--ink-muted)",
  low: "var(--band-low)",
  medium: "var(--band-medium)",
  high: "var(--band-high)",
  critical: "var(--band-critical)",
};

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
