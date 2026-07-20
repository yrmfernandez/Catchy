"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

/** Shared by /login and /register — the only difference is which action runs. */
export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (isRegister) await register(email, password);
      else await login(email, password);
      router.push("/history");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <Card>
        <CardHeader
          title={isRegister ? "Create an account" : "Sign in"}
          subtitle={
            isRegister
              ? "Accounts are optional — they save your scan history."
              : "Welcome back."
          }
        />
        <CardBody>
          <form onSubmit={submit} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className="h-10 rounded-[10px] border border-line bg-bg px-3 text-sm text-ink outline-none focus:border-accent"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              Password
              <input
                type="password"
                required
                minLength={isRegister ? 8 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={isRegister ? "new-password" : "current-password"}
                className="h-10 rounded-[10px] border border-line bg-bg px-3 text-sm text-ink outline-none focus:border-accent"
              />
              {isRegister ? (
                <span className="text-xs text-ink-muted">At least 8 characters.</span>
              ) : null}
            </label>

            {error ? (
              <p
                className="m-0 rounded-[10px] border px-3 py-2 text-sm"
                style={{
                  color: "var(--band-critical)",
                  borderColor: "var(--band-critical)",
                  background:
                    "color-mix(in srgb, var(--band-critical) 10%, transparent)",
                }}
              >
                {error}
              </p>
            ) : null}

            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 size={16} className="animate-spin" /> : null}
              {isRegister ? "Create account" : "Sign in"}
            </Button>
          </form>

          <p className="mt-4 mb-0 text-sm text-ink-muted">
            {isRegister ? (
              <>
                Already have an account?{" "}
                <Link href="/login" className="text-accent">
                  Sign in
                </Link>
              </>
            ) : (
              <>
                No account?{" "}
                <Link href="/register" className="text-accent">
                  Create one
                </Link>
              </>
            )}
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
