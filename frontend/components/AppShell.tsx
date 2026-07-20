"use client";

import {
  BarChart3,
  FileText,
  History,
  LayoutDashboard,
  LogOut,
  ScanLine,
  Settings,
  Shield,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/cn";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scan", label: "Scan", icon: ScanLine },
  { href: "/history", label: "History", icon: History },
  { href: "/intel", label: "Threat intel", icon: Shield },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout, loading } = useAuth();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar — collapses to icons on small screens. */}
      <aside className="sticky top-0 flex h-screen w-16 shrink-0 flex-col border-r border-line bg-surface md:w-56">
        <div className="flex h-14 items-center px-3 md:px-4">
          <Link href="/" className="no-underline">
            <span className="hidden md:inline">
              <Logo size={26} />
            </span>
            <span className="md:hidden">
              <Logo size={26} withWordmark={false} />
            </span>
          </Link>
        </div>

        <nav className="flex flex-1 flex-col gap-1 p-2">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                title={label}
                className={cn(
                  "flex items-center gap-3 rounded-[10px] px-3 py-2 text-sm no-underline transition-colors",
                  active
                    ? "bg-surface-2 text-accent font-medium"
                    : "text-ink-muted hover:bg-surface-2 hover:text-ink",
                )}
              >
                <Icon size={18} className="shrink-0" />
                <span className="hidden md:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-3 border-b border-line bg-surface px-4">
          <span className="text-sm text-ink-muted">
            Explainable phishing detection
          </span>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {loading ? null : user ? (
              <div className="flex items-center gap-2">
                <span className="hidden text-sm text-ink-muted sm:inline">
                  {user.email}
                </span>
                <Button variant="ghost" size="sm" onClick={logout} title="Sign out">
                  <LogOut size={16} />
                  <span className="hidden sm:inline">Sign out</span>
                </Button>
              </div>
            ) : (
              <Link href="/login" className="no-underline">
                <Button size="sm" variant="secondary">
                  Sign in
                </Button>
              </Link>
            )}
          </div>
        </header>

        <main className="min-w-0 flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
