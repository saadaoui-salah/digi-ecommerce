"use client";

import { Moon, Sun } from "lucide-react";

import { useI18n } from "@/lib/i18n";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { t } = useI18n();

  return (
    <label
      htmlFor="theme-dark"
      title={t("common.themeToggle")}
      className={`theme-toggle-label btn-animate grid size-9 shrink-0 cursor-pointer place-items-center rounded-lg border border-border bg-card/60 text-muted-foreground outline-none hover:border-foreground/20 hover:text-foreground ${className}`}
    >
      <Sun className="hidden size-4 dark:block" />
      <Moon className="size-4 dark:hidden" />
      <span className="sr-only">{t("common.themeToggle")}</span>
    </label>
  );
}
