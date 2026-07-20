"use client";

import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";

/** Client-side guard for the history surfaces (the API enforces this too). */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <p className="text-sm text-ink-muted">Loading…</p>;
  }

  if (!user) {
    return (
      <Card className="mx-auto max-w-md">
        <CardBody className="flex flex-col items-start gap-3">
          <h2 className="m-0 text-base font-semibold">Sign in required</h2>
          <p className="m-0 text-sm text-ink-muted">
            Scan history is tied to your account. Scanning itself works without
            one — sign in to keep a record.
          </p>
          <div className="flex gap-2">
            <Link href="/login" className="no-underline">
              <Button size="sm">Sign in</Button>
            </Link>
            <Link href="/register" className="no-underline">
              <Button size="sm" variant="secondary">
                Create account
              </Button>
            </Link>
          </div>
        </CardBody>
      </Card>
    );
  }

  return <>{children}</>;
}
