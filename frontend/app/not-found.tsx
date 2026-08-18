"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useI18n();

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
      <span className="text-8xl font-extrabold text-gray-200">404</span>
      <h1 className="-mt-4 text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl dark:text-gray-100">
        {t("nf.title")}
      </h1>
      <p className="mt-3 max-w-md text-center text-base leading-relaxed text-gray-600 dark:text-gray-400">
        {t("nf.subtitle")}
      </p>
      <div className="mt-8 flex items-center gap-4">
        <Link
          href="/"
          className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
        >
          {t("nf.home")}
        </Link>
        <Link
          href="/archive"
          className="rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-slate-900 dark:text-gray-300 dark:hover:bg-slate-800"
        >
          {t("nav.archive")}
        </Link>
      </div>
    </div>
  );
}