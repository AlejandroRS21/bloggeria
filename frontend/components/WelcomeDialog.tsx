"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n";

const STORAGE_KEY = "bloggeria:welcome-dismissed";

/**
 * One-time welcome dialog that nudges first-time visitors toward generating
 * a post. Dismissed state persists in localStorage (never reappears).
 */
export default function WelcomeDialog() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) {
        setOpen(true);
      }
    } catch {
      /* localStorage blocked — show once per mount, no persistence */
      setOpen(true);
    }
  }, []);

  function dismiss() {
    setOpen(false);
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-zinc-900 dark:ring-1 dark:ring-zinc-800">
        <h2
          id="welcome-title"
          className="text-xl font-bold text-gray-900 dark:text-zinc-100"
        >
          {t("welcome.title")}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
          {t("welcome.body")}
        </p>
        <div className="mt-6 flex items-center gap-3">
          <Link
            href="/posts/new"
            onClick={dismiss}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
          >
            {t("welcome.start")}
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
              />
            </svg>
          </Link>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg px-4 py-2.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            {t("welcome.later")}
          </button>
        </div>
      </div>
    </div>
  );
}
