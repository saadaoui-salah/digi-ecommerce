"use client";

import { use, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, ChevronRight, Loader2, Package } from "lucide-react";

import { PendingApproval } from "@/components/account-gate";
import {
  LockedPanel,
  PackagePicker,
} from "@/components/package-groups";
import { CopyButton } from "@/components/copy-button";
import { ProductMedia } from "@/components/product-media";
import { ProductDetailSkeleton } from "@/components/skeletons";import { money, ProductCard } from "@/components/product-card";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { SuccessCheck } from "@/components/success-check";
import { useToast } from "@/components/toast";
import { useSession } from "@/components/use-session";
import {
  api,
  apiOnce,
  ApiError,
  type Order,
  type PackageCode,
  type Package as PackageType,
  type Product,
  type ProductDetail,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { couponPrice } from "@/lib/coupon";
import { formatDate } from "@/lib/datetime";

type ProductState = {
  product: ProductDetail | null;
  related: Product[];
  notFound: boolean;
  error: boolean;
};

export function ProductClient({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const { t, locale } = useI18n();
  const { user, checkingSession, signOut } = useSession();
  const [state, setState] = useState<ProductState | null>(null);
  const [selected, setSelected] = useState<PackageType | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [buying, setBuying] = useState(false);
  const [buyDone, setBuyDone] = useState(false);
  const [buyError, setBuyError] = useState("");
  const [delivered, setDelivered] = useState<PackageCode | null>(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [buyerInfo, setBuyerInfo] = useState("");
  const [infoError, setInfoError] = useState("");
  const { notify } = useToast();

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    async function load() {
      try {
        // One request carries the product, its packages and the siblings.
        const product = await apiOnce<ProductDetail>(`/products/${slug}/`);
        if (!cancelled) {
          setState({
            product,
            related: product.related ?? [],
            notFound: false,
            error: false,
          });
          const firstGroup = product.package_groups[0];
          const firstAvailable =
            firstGroup?.packages.find((pkg) => pkg.is_available) ??
            product.packages.find((pkg) => pkg.is_available);
          setSelected(firstAvailable ?? null);
          setSelectedGroup(firstAvailable?.group ?? firstGroup?.id ?? null);
        }
      } catch (error) {
        if (!cancelled) {
          const notFound = error instanceof ApiError && error.status === 404;
          setState({
            product: null,
            related: [],
            notFound,
            error: !notFound,
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [user, slug]);

  const product = state?.product ?? null;
  const isInstant = product?.type === "immediate";

  // The coupon of the customer and the price they pay with it.
  const coupon = product?.coupon ?? null;
  const discounted = useMemo(() => {
    if (!selected) return 0;
    const price = Number(selected.price_current ?? selected.price);
    return couponPrice(coupon, price);
  }, [coupon, selected]);

  const handleSelect = useCallback((pkg: PackageType) => {
    setSelected(pkg);
    if (pkg.group !== null) setSelectedGroup(pkg.group);
  }, []);

  const handleSelectGroup = useCallback(
    (groupId: number | null) => {
      setSelectedGroup(groupId);
      if (groupId === null || !product) return;
      // Keep a package of the newly picked group selected.
      const group = product.package_groups.find((item) => item.id === groupId);
      const stillSelected =
        selected && selected.group === groupId ? selected : null;
      if (stillSelected) return;
      const firstAvailable = group?.packages.find((pkg) => pkg.is_available);
      if (firstAvailable) setSelected(firstAvailable);
    },
    [product, selected],
  );

  const placeOrder = useCallback(
    async (info: string) => {
      if (!product || !selected) return;

      setBuying(true);
      setBuyError("");
      try {
        const order = await api<Order>(
          "/auth/orders/",
          {
            method: "POST",
            body: JSON.stringify({
              package: selected.id,
              ...(info ? { buyer_info: info } : {}),
            }),
          },
        );
        setDelivered(
          order.code_value
            ? {
                id: order.id,
                package: order.package ?? 0,
                email: order.code_value.split("|", 1)[0] ?? "",
                password: order.code_value.split("|").slice(1).join("|"),
                claimed_at: order.created_at,
              }
            : null,
        );
        setBuyDone(true);
        notify(t("product.orderPlaced"), "success");
        setTimeout(() => setBuyDone(false), 2500);
      } catch (error) {
        if (error instanceof ApiError && error.status === 409) {
          setBuyError(t("product.noCodes"));
        } else if (
          error instanceof ApiError &&
          error.status === 400 &&
          error.data &&
          typeof error.data === "object" &&
          "buyer_info" in (error.data as Record<string, unknown>)
        ) {
          setInfoError(t("product.infoRequired"));
          setInfoOpen(true);
        } else if (error instanceof ApiError && error.status === 400) {
          setBuyError(t("product.notEnoughCredit"));
        } else {
          setBuyError(t("product.buyError"));
        }
      } finally {
        setBuying(false);
      }
    },
    [product, selected, t, notify],
  );

  const handleBuy = useCallback(async () => {
    if (!product || !selected) return;

    // On-demand products flagged by the admin ask for extra details first.
    if (product.requires_info && product.type === "demand") {
      setInfoError("");
      setInfoOpen(true);
      return;
    }

    await placeOrder("");
  }, [product, selected, placeOrder]);

  const handleInfoSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const info = buyerInfo.trim();
      if (!info) {
        setInfoError(t("product.infoRequired"));
        return;
      }
      setInfoOpen(false);
      setInfoError("");
      await placeOrder(info);
    },
    [buyerInfo, placeOrder, t],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader user={user} onSignOut={signOut} />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="bg-grid pointer-events-none absolute inset-0" />
          <div className="relative mx-auto w-full max-w-6xl px-5 py-12 sm:px-8 lg:py-16">
            <nav
              aria-label="breadcrumb"
              className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground"
            >
              <Link href="/" className="transition-colors hover:text-foreground">
                {t("common.home")}
              </Link>
              <ChevronRight className="size-3.5 rtl:rotate-180" />
              {product ? (
                <Link
                  href={`/categories/${product.category_slug}`}
                  className="transition-colors hover:text-foreground"
                >
                  {product.category_name}
                </Link>
              ) : (
                <span>{t("home.catalogEyebrow")}</span>
              )}
              <ChevronRight className="size-3.5 rtl:rotate-180" />
              <span className="text-foreground">
                {product?.name ?? slug}
              </span>
            </nav>

            {checkingSession || (user && state === null) ? (
              <div className="mt-8">
                <ProductDetailSkeleton />
              </div>
            ) : !user ? (
              <div className="mt-8">
                <LockedPanel />
              </div>
            ) : !user.is_approved ? (
              <div className="mt-8">
                <PendingApproval />
              </div>
            ) : state?.notFound ? (
              <div className="mt-8 rounded-2xl border border-dashed border-border px-5 py-14 text-center">
                <p className="text-sm font-medium text-foreground">
                  {t("product.notFoundTitle")}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("product.notFoundCopy")}
                </p>
                <Link
                  href="/#catalog"
                  className="btn-animate mt-6 inline-flex h-10 items-center rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {t("product.backToCatalog")}
                </Link>
              </div>
            ) : state?.error || !product ? (
              <div className="mt-8 rounded-xl border border-destructive/25 bg-destructive/10 px-5 py-6 text-sm text-destructive">
                {t("product.errorTitle")}
              </div>
            ) : (
              <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_380px]">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={
                        isInstant
                          ? "shrink-0 rounded-md bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-700 ring-1 ring-emerald-500/20 ring-inset dark:text-emerald-300"
                          : "shrink-0 rounded-md bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium text-amber-700 ring-1 ring-amber-500/20 ring-inset dark:text-amber-300"
                      }
                    >
                      {isInstant ? t("home.instantBadge") : t("home.demandBadge")}
                    </span>
                    <Link
                      href={`/categories/${product.category_slug}`}
                      className="truncate text-[10px] font-medium tracking-[0.18em] text-sky-700 uppercase transition-colors hover:text-sky-600 dark:text-sky-300 dark:hover:text-sky-200"
                    >
                      {product.category_name}
                    </Link>
                  </div>

                  <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                    {product.name}
                  </h1>
                  {product.short_description && (
                    <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
                      {product.short_description}
                    </p>
                  )}

                  {product.promotion && (
                    <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-3">
                      <span className="rounded-md bg-amber-500 px-2 py-1 text-[11px] font-bold text-amber-950">
                        {product.promotion.percentage
                          ? t("promotion.badge", {
                              percent: Number(
                                product.promotion.percentage,
                              ).toFixed(0),
                            })
                          : t("promotion.badgePrice")}
                      </span>
                      {product.price_from && product.price_current && (
                        <span className="flex items-baseline gap-2">
                          <span className="text-lg font-semibold text-foreground">
                            {money(product.price_current)}
                          </span>
                          <span className="text-sm text-muted-foreground line-through">
                            {money(product.price_from)}
                          </span>
                          <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
                            {t("promotion.save", {
                              amount: money(
                                (
                                  Number(product.price_from) -
                                  Number(product.price_current)
                                ).toFixed(2),
                              ),
                            })}
                          </span>
                        </span>
                      )}
                      {product.promotion.ends_at && (
                        <span className="text-xs text-muted-foreground">
                          {t("promotion.until", {
                            date: formatDate(product.promotion.ends_at, locale),
                          })}
                        </span>
                      )}
                    </div>
                  )}

                  {(product.video || product.images.length > 0 || product.image) && (
                    <ProductMedia product={product} />
                  )}

                  {product.description && (
                    <div className="mt-8">
                      <h2 className="text-[11px] font-medium tracking-[0.22em] text-muted-foreground uppercase">
                        {t("product.about")}
                      </h2>
                      <p className="mt-3 whitespace-pre-line text-sm leading-7 text-muted-foreground">
                        {product.description}
                      </p>
                    </div>
                  )}
                </div>

                <aside className="lg:sticky lg:top-24 lg:self-start">
                  <div className="rounded-2xl border border-border bg-card p-5">
                    <div className="flex items-center gap-2">
                      <span className="grid size-8 place-items-center rounded-lg bg-sky-500/10 text-sky-600 ring-1 ring-sky-500/20 ring-inset dark:text-sky-300">
                        <Package className="size-4" />
                      </span>
                      <h2 className="text-base font-medium tracking-tight text-foreground">
                        {t("product.packages")}
                      </h2>
                    </div>

                    <div className="mt-4">
                      {product.package_groups.length > 0 ||
                      product.packages.length > 0 ? (
                        <PackagePicker
                          groups={product.package_groups}
                          packages={product.packages}
                          selectedGroup={selectedGroup}
                          selectedPackage={selected}
                          onSelectGroup={handleSelectGroup}
                          onSelectPackage={handleSelect}
                        />
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          {t("category.empty")}
                        </p>
                      )}
                    </div>

                    <div className="mt-5 border-t border-border pt-4">
                      {selected ? (
                        <div className="flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-[10px] tracking-[0.16em] text-muted-foreground uppercase">
                              {t("product.selectedPackage")}
                            </p>
                            <p className="mt-0.5 truncate text-sm font-medium text-foreground">
                              {selected.name}
                              {selected.group !== null &&
                                ` · ${
                                  product.package_groups.find((g) => g.id === selected.group)?.name ?? ""
                                }`}
                            </p>
                          </div>
                          <p className="shrink-0 text-xl font-semibold tracking-tight text-foreground">
                            {money(selected.price_current ?? selected.price)}
                          </p>
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">
                          {t("product.selectPackage")}
                        </p>
                      )}

                      {/* The coupon of the customer: the code, the real price
                          and the price they pay. */}
                      {coupon && selected && (
                        <div className="mt-4 rounded-xl border border-emerald-500/25 bg-emerald-500/[0.07] p-4">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-[10px] tracking-[0.16em] text-emerald-700 uppercase dark:text-emerald-300">
                              {t("product.yourCoupon")}
                            </p>
                            <span className="inline-flex items-center gap-2">
                              <span className="font-mono text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                                {coupon.code}
                              </span>
                              <CopyButton value={coupon.code} />
                            </span>
                          </div>

                          <div className="mt-3 flex items-baseline gap-2">
                            <span className="text-sm text-muted-foreground line-through">
                              {money(selected.price_current ?? selected.price)}
                            </span>
                            <span className="text-xl font-semibold tracking-tight text-emerald-700 dark:text-emerald-300">
                              {money(discounted.toFixed(2))}
                            </span>
                          </div>

                          <p className="mt-1 text-[11px] text-muted-foreground">
                            {t("product.couponOrders", {
                              count: coupon.remaining_orders,
                            })}
                          </p>
                        </div>
                      )}

                      <button
                        type="button"
                        disabled={!selected || buying || buyDone}
                        onClick={handleBuy}
                        className="btn-animate group/btn mt-4 inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {buyDone ? (
                          <>
                            <SuccessCheck />
                            {t("product.orderPlacedShort")}
                          </>
                        ) : buying ? (
                          <>
                            <Loader2 className="size-4 animate-spin" />
                            {t("product.delivering")}
                          </>
                        ) : (
                          <>
                            {t("home.buyNow")}
                            <ArrowRight className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5 rtl:rotate-180 rtl:group-hover/btn:-translate-x-0.5" />
                          </>
                        )}
                      </button>

                      {buyError && (
                        <p
                          role="alert"
                          className="mt-3 rounded-lg border border-destructive/25 bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive"
                        >
                          {buyError}
                        </p>
                      )}

                      {delivered && (
                        <div className="mt-3 rounded-xl border border-emerald-500/25 bg-emerald-500/5 p-4">
                          <p className="text-[11px] font-medium tracking-[0.18em] text-emerald-700 uppercase dark:text-emerald-300">
                            {t("product.yourCode")}
                          </p>
                          <dl className="mt-3 space-y-2">
                            <div className="flex items-center justify-between gap-3">
                              <dt className="text-xs text-muted-foreground">
                                {t("product.codeEmail")}
                              </dt>
                              <dd className="flex items-center gap-2">
                                <span className="truncate font-mono text-xs font-medium text-foreground">
                                  {delivered.email}
                                </span>
                                <CopyButton value={delivered.email} />
                              </dd>
                            </div>
                            <div className="flex items-center justify-between gap-3">
                              <dt className="text-xs text-muted-foreground">
                                {t("product.codePassword")}
                              </dt>
                              <dd className="flex items-center gap-2">
                                <span className="truncate font-mono text-xs font-medium text-foreground">
                                  {delivered.password}
                                </span>
                                <CopyButton value={delivered.password} />
                              </dd>
                            </div>
                          </dl>
                        </div>
                      )}
                    </div>
                  </div>
                </aside>
              </div>
            )}

            {!checkingSession &&
              !state?.notFound &&
              !state?.error &&
              (state?.related ?? []).length > 0 && (
                <div className="mt-12">
                  <h2 className="text-lg font-medium tracking-tight text-foreground">
                    {t("product.related")}
                  </h2>
                  <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                    {(state?.related ?? []).map((item) => (
                      <ProductCard key={item.id} product={item} />
                    ))}
                  </div>
                </div>
              )}
          </div>
        </section>
      </main>

      {infoOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 backdrop-blur-sm sm:items-center"
          onClick={(event) => {
            if (event.target === event.currentTarget) setInfoOpen(false);
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="buyer-info-title"
            className="w-full max-w-md rounded-2xl border border-border bg-card p-5 shadow-2xl"
          >
            <h2
              id="buyer-info-title"
              className="text-base font-semibold tracking-tight text-foreground"
            >
              {t("product.infoTitle")}
            </h2>
            <p className="mt-1.5 text-sm leading-6 text-muted-foreground">
              {t("product.infoCopy")}
            </p>

            <form onSubmit={handleInfoSubmit} className="mt-4">
              <label
                htmlFor="buyer-info"
                className="text-xs font-medium text-muted-foreground"
              >
                {t("product.infoLabel")}
              </label>
              <textarea
                id="buyer-info"
                name="buyer_info"
                rows={4}
                autoFocus
                value={buyerInfo}
                onChange={(event) => {
                  setBuyerInfo(event.target.value);
                  if (infoError) setInfoError("");
                }}
                placeholder={t("product.infoPlaceholder")}
                className="mt-1.5 w-full resize-none rounded-lg border border-border bg-card px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus-visible:border-sky-500/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500/20"
              />

              {infoError && (
                <p
                  role="alert"
                  className="mt-2 text-xs text-red-600 dark:text-red-400"
                >
                  {infoError}
                </p>
              )}

              <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  onClick={() => setInfoOpen(false)}
                  className="btn-animate inline-flex h-10 items-center justify-center rounded-lg border border-border px-4 text-sm font-medium text-muted-foreground hover:text-foreground"
                >
                  {t("product.infoCancel")}
                </button>
                <button
                  type="submit"
                  disabled={buying}
                  className="btn-animate inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {buying && <Loader2 className="size-4 animate-spin" />}
                  {t("product.infoContinue")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <SiteFooter />
    </div>
  );
}
