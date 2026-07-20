import { Construction } from "lucide-react";

import { Card, CardBody } from "@/components/ui/Card";

/** Honest stub: says what's missing rather than showing invented data. */
export function Placeholder({
  title,
  description,
  milestone,
}: {
  title: string;
  description: string;
  milestone: string;
}) {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <h1 className="m-0 text-xl font-semibold tracking-tight">{title}</h1>
      <Card>
        <CardBody className="flex flex-col items-start gap-2">
          <Construction size={20} className="text-ink-muted" />
          <p className="m-0 text-sm">{description}</p>
          <p className="m-0 text-xs text-ink-muted">Planned for {milestone}.</p>
        </CardBody>
      </Card>
    </div>
  );
}
