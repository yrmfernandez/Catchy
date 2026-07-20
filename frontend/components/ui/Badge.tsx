import { cn } from "@/lib/cn";

export function Badge({
  color,
  children,
  className,
}: {
  /** Any CSS colour (usually a band/severity var). */
  color?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        className,
      )}
      style={
        color
          ? { color, backgroundColor: `color-mix(in srgb, ${color} 14%, transparent)` }
          : undefined
      }
    >
      {children}
    </span>
  );
}
