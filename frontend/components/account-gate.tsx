"use client";

import type { ReactNode } from "react";
import { Clock, Loader2, RefreshCw } from "lucide-react";

import { LockedPanel } from "@/components/package-groups";
import { Button } from "@/components/ui/button";
import { useSession } from "@/components/use-session";
import type { User } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

/**
 * Shown to a customer whose account still waits for an admin approval.
 */
export function PendingApproval() {
  const { t } = useI18n();
  const { user, refresh, signOut, signingOut } = useSession();

  return (
    <div className="rounded-2xl border border-border bg-card px-5 py-12 text-center sm:px-10">
      <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-300">
        <Clock className="size-6" />
      </span>

      <h2 className="mt-6 text-xl font-semibold tracking-tight text-foreground">
        {t("approval.title")}
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        {t("approval.copy")}
      </p>

      {user?.email && (
        <p className="mt-4 text-sm font-medium text-foreground">{user.email}</p>
      )}

      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Button
          type="button"
          onClick={() => refresh()}
          className="btn-animate inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
        >
          <RefreshCw className="size-4" />
          {t("approval.checkAgain")}
        </Button>
        <Button
          type="button"
          onClick={() => signOut()}
          disabled={signingOut}
          variant="outline"
          className="btn-animate inline-flex h-10 items-center gap-2 rounded-lg px-4 text-sm font-medium text-foreground hover:border-foreground/25 hover:bg-surface-muted disabled:opacity-60"
        >
          {signingOut && <Loader2 className="size-4 animate-spin" />}
          {signingOut ? t("common.signingOut") : t("common.signOut")}
        </Button>
      </div>
    </div>
  );
}

/**
 * Wraps the signed-in area of a page: signed-out visitors get the members
 * panel, customers waiting for approval get the review notice, everyone else
 * sees the page. The child receives the signed-in user.
 */
export function AccountGate({
  children,
  loading = null,
}: {
  children: (user: User) => ReactNode;
  loading?: ReactNode;
}) {
  const { user, checkingSession } = useSession();

  if (checkingSession) return <>{loading}</>;
  if (!user) return <LockedPanel />;
  if (!user.is_approved) return <PendingApproval />;

  return <>{children(user)}</>;
}
