"use client";

import Link from "next/link";
import { ArrowRight, Menu } from "lucide-react";

import { NotificationBell } from "@/components/notification-bell";
import { SiteSidebar } from "@/components/site-sidebar";
import { Logo } from "@/components/logo";
import type { User } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export function SiteHeader({
  user,
  onSignOut,
}: {
  user: User | null;
  onSignOut?: () => void;
}) {
  const { t } = useI18n();

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-3 px-4 sm:px-8">
          <div className="flex items-center gap-3">
            {user && (
              <>
                {/* Hidden toggle: the drawer and its animation are pure CSS. */}
                <input
                  id="sidebar-open"
                  type="checkbox"
                  className="peer sr-only"
                  aria-label={t("common.menu")}
                />
                <label
                  htmlFor="sidebar-open"
                  data-sidebar-trigger
                  title={t("common.menu")}
                  className="btn-animate grid size-9 shrink-0 cursor-pointer place-items-center rounded-lg border border-border bg-card/60 text-muted-foreground outline-none hover:border-foreground/20 hover:text-foreground peer-focus-visible:ring-2 peer-focus-visible:ring-ring/40"
                >
                  <Menu className="sidebar-menu-icon size-4" />
                  <span className="sr-only">{t("common.menu")}</span>
                </label>
              </>
            )}
            <Logo />
          </div>

          <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
            <Link href="/" className="transition-colors hover:text-foreground">
              {t("common.home")}
            </Link>
            <Link href="/catalog" className="transition-colors hover:text-foreground">
              {t("nav.catalog")}
            </Link>
          </nav>

          {user ? (
            <div className="flex items-center gap-3">
              <span className="hidden truncate text-sm text-muted-foreground sm:inline">
                {`${user.first_name} ${user.last_name}`.trim() || user.email}
              </span>
              <NotificationBell />
            </div>
          ) : (
            <Link
              href="/auth"
              className="btn-animate group/btn inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              <span className="hidden sm:inline">{t("nav.createAccount")}</span>
              <span className="sm:hidden">{t("nav.join")}</span>
              <ArrowRight className="size-3.5 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
            </Link>
          )}
        </div>
      </header>

      {/* Sibling of the header so the header's backdrop-blur never becomes the
          containing block for the fixed drawer/backdrop. Only signed-in
          visitors get the menu. */}
      {user && <SiteSidebar user={user} onSignOut={onSignOut} />}
    </>
  );
}
