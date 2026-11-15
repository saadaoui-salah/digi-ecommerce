"use client";

import { useEffect } from "react";

import { captureReferralCode } from "@/lib/referral";

/**
 * Keeps the referral of the visitor.
 *
 * The code of the link a customer shared travels in the query string. It is
 * put in a cookie right away — on every page — so a reload never loses it
 * before the account is opened.
 */
export function ReferralCapture() {
  useEffect(() => {
    captureReferralCode();
  }, []);

  return null;
}
