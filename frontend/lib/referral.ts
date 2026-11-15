/**
 * The referral of the visitor.
 *
 * The code travels in the query string of the link a customer shares — it is
 * how the shop knows who brought the new account. It is kept in a cookie as
 * well, so a reload of the page does not lose it before the account is
 * opened.
 */

const COOKIE = "digi_ref";
const MAX_AGE = 60 * 60 * 24 * 30;

/** The code of the referral the visitor arrived with, if there is one. */
export function readReferralCode(): string {
  if (typeof document === "undefined") return "";

  const match = document.cookie.match(
    new RegExp(`(?:^|;\\s*)${COOKIE}=([^;]*)`),
  );

  return match ? decodeURIComponent(match[1]) : "";
}

/**
 * Keep the referral of the visitor in a cookie.
 *
 * It is called on every page: the code of the link is taken out of the
 * address and put in the cookie, where it waits for the sign-up.
 */
export function captureReferralCode(): string {
  if (typeof window === "undefined") return "";

  const fromUrl = new URLSearchParams(window.location.search).get("ref");

  if (!fromUrl) return readReferralCode();

  const code = fromUrl.trim().toUpperCase();
  if (!code) return readReferralCode();

  document.cookie = `${COOKIE}=${encodeURIComponent(code)}; path=/; max-age=${MAX_AGE}; samesite=lax`;

  // The cookie holds the code, so it does not have to stay in the address.
  const url = new URL(window.location.href);
  url.searchParams.delete("ref");
  window.history.replaceState(null, "", url.toString());

  return code;
}
