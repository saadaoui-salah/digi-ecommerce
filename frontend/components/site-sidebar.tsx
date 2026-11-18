"use client";

import Link from "next/link";
import { useEffect } from "react";
import {
  ArrowLeftRight,
  ArrowRight,
  ChartNoAxesColumn,
  HandCoins,
  House,
  Loader2,
  LayoutList,
  Receipt,
  Settings,
  Triangle,
  Users,
  Wallet,
  X,
} from "lucide-react";

import { LanguageSwitcher } from "@/components/language-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { useSession } from "@/components/use-session";
import type { User } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

/** Unchecks the CSS-driven drawer toggle. */
function closeSidebar() {
  const toggle = document.getElementById("sidebar-open") as HTMLInputElement | null;
  if (toggle) toggle.checked = false;
}

/**
 * Side drawer rendered as a sibling of the header (never inside it — the
 * header's backdrop-blur would otherwise become the containing block for
 * these fixed elements and confine them to the header bar).
 *
 * Showing, hiding and the slide animation are pure CSS: the hidden
 * #sidebar-open checkbox toggled by the header's <label> drives the state
 * through :has(). JavaScript is only used to uncheck that box when the
 * drawer has to close itself (Escape key, navigation, sign out).
 */
export function SiteSidebar({
  user,
  onSignOut,
}: {
  user: User | null;
  onSignOut?: () => void;
}) {
  const { t } = useI18n();
  const { signingOut } = useSession();

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") closeSidebar();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      {/* Backdrop — clicking it unchecks #sidebar-open, so it closes the drawer */}
      <label
        htmlFor="sidebar-open"
        aria-hidden="true"
        className="sidebar-backdrop fixed inset-0 z-50 bg-black/50"
      />

      {/* Drawer — slides from the start side (left in LTR, right in RTL) */}
      <aside
        data-sidebar-panel
        className="sidebar-drawer fixed inset-y-0 start-0 z-50 flex w-72 max-w-[85vw] flex-col border-e border-border bg-background shadow-2xl shadow-black/20"
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <span className="flex items-center gap-2 text-sm font-semibold tracking-tight text-foreground">
            <Triangle className="size-4 text-sky-600 dark:text-sky-300" />
            {t("sidebar.title")}
          </span>
          <label
            htmlFor="sidebar-open"
            role="button"
            aria-label={t("common.close")}
            title={t("common.close")}
            className="btn-animate grid size-8 cursor-pointer place-items-center rounded-lg border border-border bg-card/60 text-muted-foreground hover:border-foreground/20 hover:text-foreground"
          >
            <X className="sidebar-close-icon size-4" />
            <span className="sr-only">{t("common.close")}</span>
          </label>
        </div>

        <div className="border-b border-border px-5 py-3">
          <LanguageSwitcher />
        </div>

        {user && (
          <div className="border-b border-border px-5 py-4">
            <p className="truncate text-sm font-medium text-foreground">
              {`${user.first_name} ${user.last_name}`.trim() || user.username}
            </p>
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {user.email}
            </p>
            <div className="mt-3 flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2.5 text-sm">
              <Wallet className="size-4 shrink-0 text-sky-600 dark:text-sky-300" />
              <span className="font-semibold text-foreground">
                {user.free_spend && Number(user.credit) === 0
                  ? t("credits.unlimited")
                  : `${Number(user.credit).toFixed(2)} DA`}
              </span>
              <span className="text-xs text-muted-foreground">
                {t("common.credit")}
              </span>
            </div>
          </div>
        )}

        <nav className="space-y-1 px-3 py-4">
          <Link
            href="/"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <House className="size-4 shrink-0" />
            {t("common.home")}
          </Link>
          <Link
            href="/catalog"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <LayoutList className="size-4 shrink-0" />
            {t("nav.catalog")}
          </Link>
          <Link
            href="/orders"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <Receipt className="size-4 shrink-0" />
            {t("orders.eyebrow")}
          </Link>
          <Link
            href="/transactions"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <ArrowLeftRight className="size-4 shrink-0" />
            {t("transactions.eyebrow")}
          </Link>
          <Link
            href="/credits"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <HandCoins className="size-4 shrink-0" />
            {t("credits.eyebrow")}
          </Link>
          <Link
            href="/referrals"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <Users className="size-4 shrink-0" />
            {t("referrals.eyebrow")}
          </Link>
          <Link
            href="/analytics"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <ChartNoAxesColumn className="size-4 shrink-0" />
            {t("analytics.eyebrow")}
          </Link>
          <Link
            href="/settings"
            onClick={closeSidebar}
            className="btn-animate flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground"
          >
            <Settings className="size-4 shrink-0" />
            {t("settings.eyebrow")}
          </Link>
        </nav>

        <div className="mt-auto space-y-3 border-t border-border px-5 py-4">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm text-muted-foreground">
              {t("common.themeToggle")}
            </span>
            <ThemeToggle />
          </div>

          {user ? (
            <button
              type="button"
              onClick={() => {
                closeSidebar();
                onSignOut?.();
              }}
              disabled={signingOut}
              className="btn-animate group/btn flex h-10 w-full cursor-pointer items-center justify-center gap-2 rounded-lg border border-border text-sm font-medium text-foreground hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive disabled:opacity-60"
            >
              {signingOut ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  {t("common.signingOut")}
                </>
              ) : (
                <>
                  {t("common.signOut")}
                  <ArrowRight className="size-3.5 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                </>
              )}
            </button>
          ) : (
            <Link
              href="/auth"
              onClick={closeSidebar}
              className="btn-animate inline-flex h-10 w-full items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              {t("nav.signIn")}
            </Link>
          )}
        </div>
      </aside>
    </>
  );
}
