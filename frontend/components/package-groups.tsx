"use client";

import { ArrowRight, LockKeyhole } from "lucide-react";
import Link from "next/link";

import { money } from "@/components/product-card";
import {
  SearchSelect,
  type SearchSelectOption,
} from "@/components/ui/search-select";
import type { Package, PackageGroup } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

/**
 * The package picker: two searchable dropdowns — one for the group (the
 * region) and one for the package itself (the duration). Both lists come from
 * the product detail response, so the whole page needs a single request.
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

  const groupOptions: SearchSelectOption[] = groups.map((group) => ({
    value: String(group.id),
    label: group.name,
    // The price belongs to the duration, so the region only says how many
    // durations it holds.
    hint: t("product.durationsCount", { count: group.packages.length }),
  }));

  // The durations of the chosen region — the search looks through them too,
  // so the list never shows a duration of another country.
  const scopedPackages: SearchSelectOption[] = packages
    .filter(
      (pkg) => selectedGroup === null || pkg.group === selectedGroup,
    )
    .map((pkg) => {
      const group = groups.find((item) => item.id === pkg.group);
      return {
        value: String(pkg.id),
        label: pkg.name,
        hint: group ? group.name : undefined,
        meta: money(pkg.price_current ?? pkg.price),
        disabled: !pkg.is_available,
      };
    });

  return (
    <div className="space-y-3">
      {groups.length > 0 && (
        <SearchSelect
          label={t("product.chooseRegion")}
          placeholder={t("product.selectRegion")}
          searchPlaceholder={t("product.searchRegion")}
          emptyText={t("product.noRegionFound")}
          value={selectedGroup === null ? null : String(selectedGroup)}
          options={groupOptions}
          onChange={(value) => onSelectGroup(Number(value))}
        />
      )}

      <SearchSelect
        label={t("product.chooseDuration")}
        placeholder={t("product.selectDuration")}
        searchPlaceholder={t("product.searchDuration")}
        emptyText={t("product.noPackageFound")}
        value={selectedPackage ? String(selectedPackage.id) : null}
        options={scopedPackages}
        onChange={(value) => {
          const pkg = packages.find((item) => item.id === Number(value));
          if (pkg) onSelectPackage(pkg);
        }}
      />
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
            className="btn-animate group/btn inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
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
