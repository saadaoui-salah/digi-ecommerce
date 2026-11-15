"use client";

import Link from "next/link";

import { LanguageSwitcher } from "@/components/language-switcher";
import { Logo } from "@/components/logo";
import { useI18n } from "@/lib/i18n";

export function SiteFooter() {
  const { t } = useI18n();

  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-10 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <div className="space-y-2">
          <Logo />
          <p className="text-xs text-muted-foreground">{t("footer.tagline")}</p>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-xs text-muted-foreground">
          <Link href="/" className="transition-colors hover:text-foreground">
            {t("common.home")}
          </Link>
          <Link href="/catalog" className="transition-colors hover:text-foreground">
            {t("nav.catalog")}
          </Link>
          <Link href="/orders" className="transition-colors hover:text-foreground">
            {t("orders.eyebrow")}
          </Link>
          <Link
            href="/transactions"
            className="transition-colors hover:text-foreground"
          >
            {t("transactions.eyebrow")}
          </Link>
          <Link href="/analytics" className="transition-colors hover:text-foreground">
            {t("analytics.eyebrow")}
          </Link>
          <Link href="/referrals" className="transition-colors hover:text-foreground">
            {t("referrals.eyebrow")}
          </Link>
          <Link href="/settings" className="transition-colors hover:text-foreground">
            {t("settings.eyebrow")}
          </Link>
          <Link href="/auth" className="transition-colors hover:text-foreground">
            {t("footer.account")}
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <LanguageSwitcher compact className="w-20" />
          <p className="text-xs text-muted-foreground/70">
            {t("footer.rights")}
          </p>
        </div>
      </div>
    </footer>
  );
}
