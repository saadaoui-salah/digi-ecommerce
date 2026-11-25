"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

import { FormField } from "@/components/form-field";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Logo } from "@/components/logo";
import { SuccessCheck } from "@/components/success-check";
import { ThemeToggle } from "@/components/theme-toggle";
import { useToast } from "@/components/toast";
import { useSession } from "@/components/use-session";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiError, api, type Daira, type Wilaya } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { captureReferralCode, readReferralCode } from "@/lib/referral";

type Mode = "signin" | "signup";
type FormStatus = "idle" | "pending" | "done";

type AuthError =
  | "missingFields"
  | "invalidEmail"
  | "invalidPhone"
  | "passwordLength"
  | "passwordMismatch"
  | "invalid"
  | "emailTaken"
  | "phoneTaken"
  | "generic"
  | "unreachable";

const benefits = [
  {
    icon: Zap,
    title: "auth.benefit1Title",
    copy: "auth.benefit1Copy",
  },
  {
    icon: Sparkles,
    title: "auth.benefit2Title",
    copy: "auth.benefit2Copy",
  },
  {
    icon: ShieldCheck,
    title: "auth.benefit3Title",
    copy: "auth.benefit3Copy",
  },
] as const;

const errorKeys = {
  missingFields: "auth.errorMissingFields",
  invalidEmail: "auth.errorInvalidEmail",
  invalidPhone: "auth.errorInvalidPhone",
  passwordLength: "auth.errorPasswordLength",
  passwordMismatch: "auth.errorPasswordMismatch",
  invalid: "auth.errorInvalid",
  emailTaken: "auth.errorEmailTaken",
  phoneTaken: "auth.errorPhoneTaken",
  generic: "auth.errorGeneric",
  unreachable: "auth.errorUnreachable",
} as const;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function normalizePhone(value: string) {
  return value.trim().replace(/[\s().-]/g, "");
}

function isValidEmail(value: string) {
  return EMAIL_PATTERN.test(value.trim());
}

function isValidPhone(value: string) {
  return /^\+?\d{7,15}$/.test(normalizePhone(value));
}

function mapError(error: unknown): AuthError {
  if (error instanceof ApiError) {
    if (error.status === 401) return "invalid";

    const data = error.data;
    if (data && typeof data === "object") {
      const body = data as Record<string, unknown>;
      const emailErrors = Array.isArray(body.email) ? body.email : [];
      if (emailErrors.length > 0) {
        return emailErrors.some((message) => /exist/i.test(String(message)))
          ? "emailTaken"
          : "invalidEmail";
      }

      const phoneErrors = Array.isArray(body.phone) ? body.phone : [];
      if (phoneErrors.length > 0) {
        return phoneErrors.some((message) => /exist/i.test(String(message)))
          ? "phoneTaken"
          : "invalidPhone";
      }
    }

    return "generic";
  }

  return "unreachable";
}

/** Shared field with CSS-only validation (see components/form-field). */
const Field = FormField;

export default function AuthPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [mode, setMode] = useState<Mode>("signin");
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState<FormStatus>("idle");
  const [error, setError] = useState<AuthError | null>(null);
  const { notify } = useToast();
  const { user, checkingSession, refresh } = useSession();

  const [login, setLogin] = useState({ email: "", password: "" });
  const [signup, setSignup] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
    wilaya: "",
    daira: "",
  });
  const [wilayas, setWilayas] = useState<Wilaya[]>([]);
  const [dairas, setDairas] = useState<Daira[]>([]);
  const [loadingDairas, setLoadingDairas] = useState(false);

  // The wilayas are public; regions are admin-only and never fetched here.
  useEffect(() => {
    let cancelled = false;

    api<Wilaya[]>("/auth/wilayas/")
      .then((data) => {
        if (!cancelled) setWilayas(data);
      })
      .catch(() => {
        // The form still works without the list.
      });

    // The referral is kept in a cookie, so a reload does not lose it.
    captureReferralCode();

    return () => {
      cancelled = true;
    };
  }, []);

  // Fetch the dairas only after a wilaya has been picked.
  useEffect(() => {
    let cancelled = false;

    if (!signup.wilaya) return;

    api<Daira[]>(`/auth/dairas/?wilaya=${signup.wilaya}`)
      .then((data) => {
        if (!cancelled) setDairas(data);
      })
      .catch(() => {
        if (!cancelled) setDairas([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingDairas(false);
      });

    return () => {
      cancelled = true;
    };
  }, [signup.wilaya]);

  // The shared session already fetched /me/ once on page load. While the form
  // is showing its success state, let its own timer choose the destination.
  useEffect(() => {
    if (user && !checkingSession && status !== "done") router.replace("/");
  }, [user, checkingSession, router, status]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const email = login.email.trim();
    if (!email || !login.password) {
      setError("missingFields");
      return;
    }
    if (!isValidEmail(email)) {
      setError("invalidEmail");
      return;
    }

    setPending(true);
    setStatus("pending");

    try {
      await api("/auth/token/", {
        method: "POST",
        body: JSON.stringify({ email, password: login.password }),
      });
      await refresh();
      setStatus("done");
      notify(t("auth.signedInToast"));
      setTimeout(() => router.replace("/"), 700);
    } catch (loginError) {
      setStatus("idle");
      setPending(false);
      setError(mapError(loginError));
    }
  }

  async function handleSignup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const firstName = signup.first_name.trim();
    const lastName = signup.last_name.trim();
    const email = signup.email.trim();
    const phone = normalizePhone(signup.phone);

    if (
      !firstName ||
      !lastName ||
      !email ||
      !phone ||
      !signup.password ||
      !signup.confirm
    ) {
      setError("missingFields");
      return;
    }

    if (!isValidEmail(email)) {
      setError("invalidEmail");
      return;
    }

    if (!isValidPhone(phone)) {
      setError("invalidPhone");
      return;
    }

    if (signup.password.length < 8) {
      setError("passwordLength");
      return;
    }

    if (signup.password !== signup.confirm) {
      setError("passwordMismatch");
      return;
    }

    setPending(true);
    setStatus("pending");

    try {
      const referral = readReferralCode();

      await api("/auth/register/", {
        method: "POST",
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
          phone,
          password: signup.password,
          ...(signup.wilaya ? { wilaya: Number(signup.wilaya) } : {}),
          ...(signup.daira ? { daira: Number(signup.daira) } : {}),
          ...(referral ? { referral_code: referral } : {}),
        }),
      });
      await refresh();
      setStatus("done");
      notify(t("auth.accountCreatedToast"));
      setTimeout(() => router.replace("/catalog"), 700);
    } catch (signupError) {
      setStatus("idle");
      setPending(false);
      setError(mapError(signupError));
    }
  }

  const errorMessage = error ? t(errorKeys[error]) : "";

  return (
    <div className="flex min-h-screen flex-col lg:grid lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-gradient-to-br from-blue-700 via-sky-800 to-[#021018] p-12 lg:flex lg:flex-col">
        <div className="pointer-events-none absolute -top-24 -right-20 size-72 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 size-80 rounded-full bg-cyan-300/20 blur-3xl" />
        <div className="bg-grid pointer-events-none absolute inset-0 opacity-60" />

        <div className="relative">
          <Logo inverse />
        </div>

        <div className="relative my-auto max-w-md py-12">
          <p className="text-[11px] font-medium tracking-[0.22em] text-white/70 uppercase">
            {t("auth.eyebrow")}
          </p>
          <h1 className="mt-4 text-4xl leading-tight font-semibold tracking-tight text-white">
            {t("auth.sideTitle1")}
            <br />
            {t("auth.sideTitle2")}
          </h1>
          <p className="mt-4 text-sm leading-6 text-white/70">
            {t("auth.sideCopy")}
          </p>

          <ul className="mt-9 space-y-5">
            {benefits.map(({ icon: Icon, title, copy }) => (
              <li key={title} className="flex items-start gap-3.5">
                <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-white/10 text-white ring-1 ring-white/15 ring-inset">
                  <Icon className="size-4" />
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{t(title)}</p>
                  <p className="mt-0.5 text-xs leading-5 text-white/60">
                    {t(copy)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-white/50">{t("footer.rights")}</p>
      </aside>

      <main className="flex flex-1 flex-col bg-background px-5 py-7 sm:px-10">
        <div className="flex items-center justify-between gap-3">
          <div className="lg:hidden">
            <Logo />
          </div>

          <div className="ms-auto flex items-center gap-1.5 sm:gap-2">
            <ThemeToggle />
            <LanguageSwitcher compact className="w-20" />
            <Link
              href="/"
              title={t("auth.backHome")}
              className="btn-animate inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card/60 px-3 text-xs text-muted-foreground hover:border-foreground/20 hover:text-foreground"
            >
              <ArrowLeft className="size-3.5 rtl:rotate-180" />
              <span className="hidden sm:inline">{t("auth.backHome")}</span>
            </Link>
          </div>
        </div>

        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
          <Tabs
            value={mode}
            onValueChange={(value) => {
              setMode(value as Mode);
              setError(null);
            }}
          >
            <TabsList className="!h-auto grid w-full grid-cols-2 rounded-lg border border-border bg-surface-muted p-1">
              <TabsTrigger
                value="signin"
                className="!h-9 rounded-md text-sm font-medium text-muted-foreground transition-colors hover:text-foreground data-active:!bg-primary data-active:!text-primary-foreground data-active:shadow-none dark:text-muted-foreground dark:data-active:!bg-primary dark:data-active:!text-primary-foreground"
              >
                {t("auth.signInTab")}
              </TabsTrigger>
              <TabsTrigger
                value="signup"
                className="!h-9 rounded-md text-sm font-medium text-muted-foreground transition-colors hover:text-foreground data-active:!bg-primary data-active:!text-primary-foreground data-active:shadow-none dark:text-muted-foreground dark:data-active:!bg-primary dark:data-active:!text-primary-foreground"
              >
                {t("auth.signUpTab")}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="signin" className="animate-auth-panel mt-8">
              <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                {t("auth.signInTitle")}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("auth.signInCopy")}
              </p>

              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  handleLogin(event);
                }}
                noValidate
                autoComplete="on"
                className="mt-7 space-y-4"
              >
                <Field
                  id="login-email"
                  name="email"
                  label={t("auth.email")}
                  type="email"
                  autoComplete="email"
                  autoCapitalize="none"
                  spellCheck={false}
                  placeholder="you@example.com"
                  pattern="[^\s@]+@[^\s@]+\.[^\s@]{2,}"
                  errorKey="auth.errorInvalidEmail"
                  showInvalid
                  required
                  value={login.email}
                  onChange={(event) =>
                    setLogin({ ...login, email: event.target.value })
                  }
                />

                <Field
                  id="login-password"
                  name="password"
                  label={t("auth.password")}
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  required
                  value={login.password}
                  onChange={(event) =>
                    setLogin({ ...login, password: event.target.value })
                  }
                />

                {errorMessage && (
                  <div
                    role="alert"
                    className="flex items-start gap-2 rounded-lg border border-destructive/25 bg-destructive/10 px-3.5 py-3 text-xs leading-5 text-destructive"
                  >
                    <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
                    {errorMessage}
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={pending || status === "done"}
                  className="btn-animate group/btn h-11 w-full rounded-lg bg-primary text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {status === "done" ? (
                    <>
                      <SuccessCheck />
                      {t("auth.done")}
                    </>
                  ) : pending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      {t("auth.signingIn")}
                    </>
                  ) : (
                    <>
                      {t("auth.signInButton")}
                      <ArrowRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                    </>
                  )}
                </Button>
              </form>

              <p className="mt-6 text-center text-xs text-muted-foreground">
                {t("auth.newHere")}{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("signup");
                    setError(null);
                  }}
                  className="font-medium text-sky-700 transition-colors hover:text-sky-600 dark:text-sky-300 dark:hover:text-sky-200"
                >
                  {t("auth.createAccountLink")}
                </button>
              </p>
            </TabsContent>

            <TabsContent value="signup" className="animate-auth-panel mt-8">
              <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                {t("auth.signUpTitle")}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("auth.signUpCopy")}
              </p>

              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  handleSignup(event);
                }}
                noValidate
                autoComplete="on"
                className="mt-7 space-y-4"
              >
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field
                    id="first-name"
                    name="first_name"
                    label={t("auth.firstName")}
                    autoComplete="given-name"
                    autoCapitalize="words"
                    placeholder="Jane"
                    required
                    value={signup.first_name}
                    onChange={(event) =>
                      setSignup({ ...signup, first_name: event.target.value })
                    }
                  />
                  <Field
                    id="last-name"
                    name="last_name"
                    label={t("auth.lastName")}
                    autoComplete="family-name"
                    autoCapitalize="words"
                    placeholder="Doe"
                    required
                    value={signup.last_name}
                    onChange={(event) =>
                      setSignup({ ...signup, last_name: event.target.value })
                    }
                  />
                </div>

                <Field
                  id="signup-email"
                  name="email"
                  label={t("auth.email")}
                  type="email"
                  autoComplete="email"
                  autoCapitalize="none"
                  spellCheck={false}
                  placeholder="you@example.com"
                  pattern="[^\s@]+@[^\s@]+\.[^\s@]{2,}"
                  errorKey="auth.errorInvalidEmail"
                  showInvalid
                  required
                  value={signup.email}
                  onChange={(event) =>
                    setSignup({ ...signup, email: event.target.value })
                  }
                />

                <Field
                  id="phone"
                  name="phone"
                  label={t("auth.phone")}
                  type="tel"
                  autoComplete="tel"
                  placeholder="+1 555 123 4567"
                  pattern="\s*\+?\d(?:[\s\(\)\.\-]*\d){6,14}\s*"
                  errorKey="auth.errorInvalidPhone"
                  showInvalid
                  required
                  value={signup.phone}
                  onChange={(event) =>
                    setSignup({ ...signup, phone: event.target.value })
                  }
                />

                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-1.5 block text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                      {t("auth.wilaya")}
                    </span>
                    <select
                      id="wilaya"
                      name="wilaya"
                      autoComplete="address-level1"
                      value={signup.wilaya}
                      onChange={(event) => {
                        const wilaya = event.target.value;
                        setSignup({ ...signup, wilaya, daira: "" });
                        setDairas([]);
                        setLoadingDairas(Boolean(wilaya));
                      }}
                      className="h-11 w-full rounded-lg border border-border bg-card px-3 text-sm text-foreground outline-none focus:border-sky-500"
                    >
                      <option value="">{t("auth.chooseWilaya")}</option>
                      {wilayas.map((wilaya) => (
                        <option key={wilaya.id} value={String(wilaya.id)}>
                          {wilaya.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-1.5 block text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                      {t("auth.daira")}
                    </span>
                    <select
                      id="daira"
                      name="daira"
                      autoComplete="address-level2"
                      value={signup.daira}
                      onChange={(event) =>
                        setSignup({ ...signup, daira: event.target.value })
                      }
                      disabled={!signup.wilaya || loadingDairas}
                      className="h-11 w-full rounded-lg border border-border bg-card px-3 text-sm text-foreground outline-none focus:border-sky-500 disabled:opacity-55"
                    >
                      <option value="">
                        {loadingDairas ? t("common.loading") : t("auth.chooseDaira")}
                      </option>
                      {dairas.map((daira) => (
                        <option key={daira.id} value={String(daira.id)}>
                          {daira.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <Field
                    id="signup-password"
                    name="password"
                    label={t("auth.password")}
                    type="password"
                    autoComplete="new-password"
                    placeholder={t("auth.passwordPlaceholder")}
                    minLength={8}
                    required
                    value={signup.password}
                    onChange={(event) =>
                      setSignup({ ...signup, password: event.target.value })
                    }
                  />
                  <Field
                    id="confirm-password"
                    name="confirm_password"
                    label={t("auth.confirmPassword")}
                    type="password"
                    autoComplete="new-password"
                    placeholder={t("auth.confirmPlaceholder")}
                    minLength={8}
                    required
                    value={signup.confirm}
                    onChange={(event) =>
                      setSignup({ ...signup, confirm: event.target.value })
                    }
                  />
                </div>

                {errorMessage && (
                  <div
                    role="alert"
                    className="flex items-start gap-2 rounded-lg border border-destructive/25 bg-destructive/10 px-3.5 py-3 text-xs leading-5 text-destructive"
                  >
                    <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
                    {errorMessage}
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={pending || status === "done"}
                  className="btn-animate group/btn h-11 w-full rounded-lg bg-primary text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {status === "done" ? (
                    <>
                      <SuccessCheck />
                      {t("auth.done")}
                    </>
                  ) : pending ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      {t("auth.creatingAccount")}
                    </>
                  ) : (
                    <>
                      {t("auth.createAccountButton")}
                      <ArrowRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                    </>
                  )}
                </Button>
              </form>

              <p className="mt-6 text-center text-xs text-muted-foreground">
                {t("auth.alreadyHave")}{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("signin");
                    setError(null);
                  }}
                  className="font-medium text-sky-700 transition-colors hover:text-sky-600 dark:text-sky-300 dark:hover:text-sky-200"
                >
                  {t("auth.signInLink")}
                </button>
              </p>
            </TabsContent>
          </Tabs>

          <div className="mt-10 flex flex-col items-center gap-2 border-t border-border pt-6 text-center">
            <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <LockKeyhole className="size-3" />
              {t("auth.securityNote")}
            </p>
            <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground/80">
              <Check className="size-3 text-emerald-600 dark:text-emerald-400" />
              {t("auth.noSubsNote")}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
