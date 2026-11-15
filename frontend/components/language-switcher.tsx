"use client";

import { useId } from "react";
import { Check, ChevronDown } from "lucide-react";

import { Flag } from "@/components/flags";
import { localeNames, locales, useI18n, type Locale } from "@/lib/i18n";

const shortNames: Record<Locale, string> = {
  en: "EN",
  fr: "FR",
  ar: "AR",
};

/**
 * Language dropdown driven entirely by CSS: the hidden `.lang-peer` checkbox is
 * toggled by its <label>, and sibling selectors (see globals.css) open and
 * close the list. JavaScript only performs the actual language change.
 */
export function LanguageSwitcher({
  className = "",
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  const { locale, setLocale, t } = useI18n();
  const id = useId();

  function choose(next: Locale) {
    setLocale(next);

    const url = new URL(window.location.href);
    if (url.searchParams.has("lang")) {
      url.searchParams.set("lang", next);
      window.history.replaceState(null, "", url);
    }
  }

  return (
    <div className={`relative shrink-0 ${className}`}>
      <input id={id} type="checkbox" className="dropdown-peer sr-only" />

      <label
        htmlFor={id}
        className="dropdown-trigger btn-animate flex h-9 w-full cursor-pointer items-center justify-center gap-1.5 rounded-lg border border-border bg-card/60 px-2 text-xs font-medium text-foreground outline-none hover:border-foreground/20 focus-visible:ring-2 focus-visible:ring-ring/40"
        aria-haspopup="listbox"
        aria-label={t("common.language")}
        title={t("common.language")}
      >
        <Flag locale={locale} className="h-3.5 w-5" />
        <span>{compact ? shortNames[locale] : localeNames[locale]}</span>
        <ChevronDown className="dropdown-chevron size-3.5 text-muted-foreground" />
        <span className="sr-only">{t("common.language")}</span>
      </label>

      <div
        role="listbox"
        aria-label={t("common.language")}
        className="dropdown-menu absolute end-0 top-full z-50 mt-2 w-48 space-y-1 rounded-xl border border-border bg-popover p-2 text-popover-foreground shadow-2xl shadow-foreground/10"
      >
        {locales.map((code) => (
          <label
            key={code}
            htmlFor={id}
            role="option"
            aria-selected={locale === code}
            onClick={() => choose(code)}
            className={`flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-colors ${
              locale === code
                ? "bg-surface-muted text-foreground"
                : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
            }`}
          >
            <Flag locale={code} className="h-3.5 w-5" />
            <span className="flex-1 text-start">{localeNames[code]}</span>
            {locale === code && (
              <Check className="size-3.5 text-sky-600 dark:text-sky-300" />
            )}
          </label>
        ))}
      </div>
    </div>
  );
}
