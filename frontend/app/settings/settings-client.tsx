"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Mail, Phone, UserRound, Wallet } from "lucide-react";

import { AccountGate } from "@/components/account-gate";
import { FormField } from "@/components/form-field";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { useSession } from "@/components/use-session";
import { Button } from "@/components/ui/button";
import { ApiError, api, type User } from "@/lib/api";
import { useI18n, type MessageKey } from "@/lib/i18n";

type ProfileErrors = {
  email?: MessageKey;
  phone?: MessageKey;
  generic?: MessageKey;
};

type PasswordErrors = {
  current_password?: MessageKey;
  new_password?: MessageKey;
  confirm_password?: MessageKey;
  generic?: MessageKey;
};

function normalizePhone(value: string) {
  return value.replace(/[\s().-]/g, "");
}

export function SettingsClient() {
  const { t } = useI18n();
  const { user, signOut, refresh } = useSession();

  const [profile, setProfile] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });
  const [profileErrors, setProfileErrors] = useState<ProfileErrors>({});
  const [profilePending, setProfilePending] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);

  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [passwordErrors, setPasswordErrors] = useState<PasswordErrors>({});
  const [passwordPending, setPasswordPending] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);

  // Fill the forms from the signed-in user once the session resolves.
  const [loadedUserId, setLoadedUserId] = useState<number | null>(null);
  if (user && user.id !== loadedUserId) {
    setLoadedUserId(user.id);
    setProfile({
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
      email: user.email ?? "",
      phone: user.phone ?? "",
    });
  }

  useEffect(() => {
    if (!profileSaved) return;
    const timer = setTimeout(() => setProfileSaved(false), 4000);
    return () => clearTimeout(timer);
  }, [profileSaved]);

  useEffect(() => {
    if (!passwordSaved) return;
    const timer = setTimeout(() => setPasswordSaved(false), 4000);
    return () => clearTimeout(timer);
  }, [passwordSaved]);

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileErrors({});

    const email = profile.email.trim();
    const phone = normalizePhone(profile.phone.trim());

    if (!email || !phone || !profile.first_name.trim() || !profile.last_name.trim()) {
      setProfileErrors({ generic: "settings.errorGeneric" });
      return;
    }

    setProfilePending(true);
    try {
      await api<User>("/auth/me/", {
        method: "PATCH",
        body: JSON.stringify({
          first_name: profile.first_name.trim(),
          last_name: profile.last_name.trim(),
          email,
          phone,
        }),
      });
      await refresh();
      setProfileSaved(true);
    } catch (error) {
      if (error instanceof ApiError && error.data && typeof error.data === "object") {
        const body = error.data as Record<string, unknown>;
        const errors: ProfileErrors = {};

        const emailErrors = Array.isArray(body.email) ? body.email : [];
        const phoneErrors = Array.isArray(body.phone) ? body.phone : [];

        if (emailErrors.length > 0) {
          errors.email = /exist/i.test(String(emailErrors[0]))
            ? "settings.errorEmailTaken"
            : "settings.errorInvalidEmail";
        }
        if (phoneErrors.length > 0) {
          errors.phone = /exist/i.test(String(phoneErrors[0]))
            ? "settings.errorPhoneTaken"
            : "settings.errorInvalidPhone";
        }
        if (Object.keys(errors).length === 0) {
          errors.generic = "settings.errorGeneric";
        }
        setProfileErrors(errors);
      } else {
        setProfileErrors({ generic: "settings.errorUnreachable" });
      }
    } finally {
      setProfilePending(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordErrors({});

    if (passwords.new_password !== passwords.confirm_password) {
      setPasswordErrors({ confirm_password: "settings.errorPasswordMismatch" });
      return;
    }

    setPasswordPending(true);
    try {
      await api("/auth/change-password/", {
        method: "POST",
        body: JSON.stringify(passwords),
      });
      setPasswords({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setPasswordSaved(true);
    } catch (error) {
      if (error instanceof ApiError && error.data && typeof error.data === "object") {
        const body = error.data as Record<string, unknown>;
        const errors: PasswordErrors = {};

        const currentErrors = Array.isArray(body.current_password)
          ? body.current_password
          : [];
        const newErrors = Array.isArray(body.new_password) ? body.new_password : [];
        const confirmErrors = Array.isArray(body.confirm_password)
          ? body.confirm_password
          : [];

        if (currentErrors.length > 0) {
          errors.current_password = "settings.errorCurrentPassword";
        }
        if (newErrors.length > 0) {
          errors.new_password = /different/i.test(String(newErrors[0]))
            ? "settings.errorPasswordMismatch"
            : "settings.errorPasswordShort";
        }
        if (confirmErrors.length > 0) {
          errors.confirm_password = "settings.errorPasswordMismatch";
        }
        if (Object.keys(errors).length === 0) {
          errors.generic = "settings.errorGeneric";
        }
        setPasswordErrors(errors);
      } else {
        setPasswordErrors({ generic: "settings.errorUnreachable" });
      }
    } finally {
      setPasswordPending(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <p className="text-[11px] font-medium tracking-[0.22em] text-sky-700 uppercase dark:text-sky-300">
              {t("settings.eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              {t("settings.title")}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
              {t("settings.copy")}
            </p>
          </div>
        </section>

        <section className="border-t border-border bg-surface-muted">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <AccountGate>
              {(account) => (
                <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
                {/* Account summary */}
                <div className="h-fit overflow-hidden rounded-2xl border border-border bg-card">
                  <div className="flex flex-wrap items-center gap-4 border-b border-border px-6 py-5">
                    <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-sky-500/10 text-base font-semibold text-sky-600 dark:text-sky-300">
                      {`${account.first_name} ${account.last_name}`
                        .trim()
                        .split(/\s+/)
                        .slice(0, 2)
                        .map((part) => part[0]?.toUpperCase() ?? "")
                        .join("") || account.username.slice(0, 2).toUpperCase()}
                    </span>
                    <div>
                      <p className="text-base font-semibold tracking-tight text-foreground">
                        {`${account.first_name} ${account.last_name}`.trim() ||
                          account.username}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {t("settings.accountBadge")}
                      </p>
                    </div>
                    <span className="ms-auto inline-flex items-center rounded-md bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-700 ring-1 ring-emerald-500/20 ring-inset dark:text-emerald-300">
                      {t("settings.active")}
                    </span>
                  </div>

                  <dl className="grid gap-px bg-border sm:grid-cols-2 lg:grid-cols-1">
                    <div className="bg-card px-6 py-5">
                      <dt className="flex items-center gap-2 text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                        <UserRound className="size-3.5" />
                        {t("settings.username")}
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-foreground">
                        {account.username}
                      </dd>
                    </div>

                    <div className="bg-card px-6 py-5">
                      <dt className="flex items-center gap-2 text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                        <Mail className="size-3.5" />
                        {t("settings.email")}
                      </dt>
                      <dd className="mt-2 text-sm font-medium break-all text-foreground">
                        {account.email}
                      </dd>
                    </div>

                    <div className="bg-card px-6 py-5">
                      <dt className="flex items-center gap-2 text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                        <Phone className="size-3.5" />
                        {t("settings.phone")}
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-foreground">
                        {account.phone || "—"}
                      </dd>
                    </div>

                    <div className="bg-card px-6 py-5">
                      <dt className="flex items-center gap-2 text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                        <Wallet className="size-3.5" />
                        {t("common.credit")}
                      </dt>
                      <dd className="mt-2 text-xl font-semibold tracking-tight text-foreground">
                        {account.free_spend && Number(account.credit) === 0
                          ? t("credits.unlimited")
                          : `${Number(account.credit).toFixed(2)} DA`}
                      </dd>
                    </div>
                  </dl>
                </div>

                {/* Forms */}
                <div className="space-y-6">
                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      handleProfileSubmit(event);
                    }}
                    noValidate
                    autoComplete="on"
                    className="rounded-2xl border border-border bg-card p-6"
                  >
                    <h2 className="text-base font-semibold tracking-tight text-foreground">
                      {t("settings.profileTitle")}
                    </h2>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {t("settings.profileCopy")}
                    </p>

                    <div className="mt-5 grid gap-4 sm:grid-cols-2">
                      <FormField
                        id="settings-first-name"
                        name="first_name"
                        label={t("auth.firstName")}
                        value={profile.first_name}
                        onChange={(event) =>
                          setProfile({
                            ...profile,
                            first_name: event.target.value,
                          })
                        }
                        required
                        autoComplete="given-name"
                        autoCapitalize="words"
                        placeholder="Jane"
                      />
                      <FormField
                        id="settings-last-name"
                        name="last_name"
                        label={t("auth.lastName")}
                        value={profile.last_name}
                        onChange={(event) =>
                          setProfile({
                            ...profile,
                            last_name: event.target.value,
                          })
                        }
                        required
                        autoComplete="family-name"
                        autoCapitalize="words"
                        placeholder="Doe"
                      />
                      <FormField
                        id="settings-email"
                        name="email"
                        label={t("settings.email")}
                        type="email"
                        value={profile.email}
                        onChange={(event) =>
                          setProfile({ ...profile, email: event.target.value })
                        }
                        pattern="[^\s@]+@[^\s@]+\.[^\s@]{2,}"
                        autoComplete="email"
                        autoCapitalize="none"
                        spellCheck={false}
                        placeholder="you@example.com"
                        errorKey="settings.errorInvalidEmail"
                        serverErrorKey={profileErrors.email}
                        showInvalid
                        required
                      />
                      <FormField
                        id="settings-phone"
                        name="phone"
                        label={t("settings.phone")}
                        type="tel"
                        value={profile.phone}
                        onChange={(event) =>
                          setProfile({ ...profile, phone: event.target.value })
                        }
                        pattern="\s*\+?\d(?:[\s\(\)\.\-]*\d){6,14}\s*"
                        autoComplete="tel"
                        placeholder="+1 555 123 4567"
                        errorKey="settings.errorInvalidPhone"
                        serverErrorKey={profileErrors.phone}
                        showInvalid
                        required
                      />
                    </div>

                    {profileErrors.generic && (
                      <p
                        role="alert"
                        className="mt-4 rounded-lg border border-destructive/25 bg-destructive/10 px-3.5 py-3 text-xs text-destructive"
                      >
                        {t(profileErrors.generic)}
                      </p>
                    )}

                    <div className="mt-6 flex items-center gap-3">
                      <Button
                        type="submit"
                        disabled={profilePending}
                        className="btn-animate h-11 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                      >
                        {profilePending ? t("settings.saving") : t("settings.save")}
                      </Button>
                      {profileSaved && (
                        <p
                          role="status"
                          className="text-xs font-medium text-emerald-600 dark:text-emerald-400"
                        >
                          {t("settings.saved")}
                        </p>
                      )}
                    </div>
                  </form>

                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      handlePasswordSubmit(event);
                    }}
                    noValidate
                    autoComplete="on"
                    className="rounded-2xl border border-border bg-card p-6"
                  >
                    <h2 className="text-base font-semibold tracking-tight text-foreground">
                      {t("settings.passwordTitle")}
                    </h2>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {t("settings.passwordCopy")}
                    </p>

                    <div className="mt-5 grid gap-4">
                      <FormField
                        id="settings-current-password"
                        name="current_password"
                        label={t("settings.currentPassword")}
                        type="password"
                        value={passwords.current_password}
                        onChange={(event) =>
                          setPasswords({
                            ...passwords,
                            current_password: event.target.value,
                          })
                        }
                        autoComplete="current-password"
                        placeholder="••••••••"
                        serverErrorKey={passwordErrors.current_password}
                        required
                      />
                      <FormField
                        id="settings-new-password"
                        name="new_password"
                        label={t("settings.newPassword")}
                        type="password"
                        value={passwords.new_password}
                        onChange={(event) =>
                          setPasswords({
                            ...passwords,
                            new_password: event.target.value,
                          })
                        }
                        autoComplete="new-password"
                        minLength={8}
                        placeholder="••••••••"
                        errorKey="settings.errorPasswordShort"
                        serverErrorKey={passwordErrors.new_password}
                        showInvalid
                        required
                      />
                      <FormField
                        id="settings-confirm-password"
                        name="confirm_password"
                        label={t("settings.confirmPassword")}
                        type="password"
                        value={passwords.confirm_password}
                        onChange={(event) =>
                          setPasswords({
                            ...passwords,
                            confirm_password: event.target.value,
                          })
                        }
                        autoComplete="new-password"
                        placeholder="••••••••"
                        serverErrorKey={passwordErrors.confirm_password}
                        required
                      />
                    </div>

                    {passwordErrors.generic && (
                      <p
                        role="alert"
                        className="mt-4 rounded-lg border border-destructive/25 bg-destructive/10 px-3.5 py-3 text-xs text-destructive"
                      >
                        {t(passwordErrors.generic)}
                      </p>
                    )}

                    <div className="mt-6 flex items-center gap-3">
                      <Button
                        type="submit"
                        disabled={passwordPending}
                        className="btn-animate h-11 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                      >
                        {passwordPending ? t("settings.saving") : t("settings.save")}
                      </Button>
                      {passwordSaved && (
                        <p
                          role="status"
                          className="text-xs font-medium text-emerald-600 dark:text-emerald-400"
                        >
                          {t("settings.passwordSaved")}
                        </p>
                      )}
                    </div>
                  </form>
                </div>
              </div>
              )}
            </AccountGate>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
