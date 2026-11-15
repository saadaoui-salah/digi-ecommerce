import type { Metadata } from "next";
import { Geist, Geist_Mono, Noto_Sans_Arabic } from "next/font/google";

import { ReferralCapture } from "@/components/referral-capture";
import { ToastProvider } from "@/components/toast";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const arabic = Noto_Sans_Arabic({
  variable: "--font-arabic",
  subsets: ["arabic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Digi — Digital products, delivered instantly",
  description:
    "A curated marketplace for digital products. Buy instantly or request custom work, all from one account.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} ${arabic.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        {/*
          Theme bootstrap: runs while the HTML is still parsing (before first
          paint) so there is no flash. A saved choice wins; otherwise the
          system preference decides, and keeps deciding until the visitor
          toggles the switch themselves.
        */}
        <input id="theme-dark" type="checkbox" className="sr-only" />
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var box=document.getElementById("theme-dark");if(!box)return;var saved=null;try{saved=localStorage.getItem("theme")}catch(e){}function apply(value){saved=value;try{saved?localStorage.setItem("theme",value):localStorage.removeItem("theme")}catch(e){}}if(saved==="dark"){box.checked=true}else if(saved==="light"){box.checked=false}else{box.checked=window.matchMedia("(prefers-color-scheme: dark)").matches}box.addEventListener("change",function(){apply(box.checked?"dark":"light")});var query=window.matchMedia("(prefers-color-scheme: dark)");query.addEventListener("change",function(event){if(!saved)box.checked=event.matches})})();`,
          }}
        />
        <I18nProvider>
          <ToastProvider>
            <ReferralCapture />
            {children}
          </ToastProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
