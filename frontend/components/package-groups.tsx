"use client";

import { ArrowRight, LockKeyhole } from "lucide-react";
import Link from "next/link";

import { money } from "@/components/product-card";
import type { Package, PackageGroup } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

/**
 * The package picker: the group stays on its own line, and the durations are
 * small clickable boxes instead of a dropdown. Both lists come from the
 * product detail response, so the whole page needs a single request.
 */
export function PackagePicker({
  groups,
  packages,
  selectedGroup,
  selectedPackage,
  onSelectGroup,
  onSelectPackage,
}: {
  groups: PackageGroup[];
  packages: Package[];
  selectedGroup: number | null;
  selectedPackage: Package | null;
  onSelectGroup: (groupId: number | null) => void;
  onSelectPackage: (pkg: Package) => void;
}) {
  const { t } = useI18n();

  // The durations of the chosen region only — never another country's.
  const scopedPackages = packages.filter(
    (pkg) => selectedGroup === null || pkg.group === selectedGroup,
  );

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {scopedPackages.map((pkg) => {
          const selected = selectedPackage?.id === pkg.id;
          return (
            <button
              key={pkg.id}
              type="button"
              disabled={!pkg.is_available}
              onClick={() => onSelectPackage(pkg)}
              className={cn(
                "btn-animate inline-flex min-w-20 flex-col items-start gap-0.5 rounded-lg border px-3 py-2 text-start text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50",
                selected
                  ? "border-primary bg-primary/10 font-medium text-foreground"
                  : "border-border bg-card text-muted-foreground hover:border-foreground/25 hover:text-foreground",
              )}
            >
              <span className="truncate">{pkg.name}</span>
              <span className="text-xs opacity-70">
                {money(pkg.price_current ?? pkg.price)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function LockedPanel({ compact = false }: { compact?: boolean }) {
  const { t } = useI18n();

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border bg-card px-6 sm:px-12 py-14">
      <div className="pointer-events-none absolute -top-24 left-1/2 size-72 -translate-x-1/2 rounded-full bg-sky-500/10 blur-3xl dark:bg-sky-600/20" />
      <div className="relative mx-auto max-w-lg text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-xl border border-border bg-surface-muted text-sky-600 dark:text-sky-300">
          <LockKeyhole className="size-5" />
        </div>
        <h3 className="mt-6 text-2xl font-semibold tracking-tight text-foreground">
          {t("home.lockedTitle")}
        </h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {t("home.lockedCopy")}
        </p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Link
            href="/auth"
            className="btn-animate group/btn inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            {t("home.signInCta")}
            <ArrowRight className="size-3.5 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
          </Link>
          {!compact && (
            <Link
              href="/auth"
              className="btn-animate inline-flex h-10 items-center justify-center rounded-lg border border-border px-5 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-surface-muted"
            >
              {t("home.createAccountCta")}
            </Link>
          )}
        </div>
        <p className="mt-5 text-xs text-muted-foreground">
          {t("home.freeJoinNoCard")}
        </p>
      </div>
    </div>
  );
}
