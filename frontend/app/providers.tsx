"use client";

import { I18nProvider } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";
import { ThemeProvider } from "next-themes";

export default function Providers({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  return (
    <I18nProvider initialLocale={locale}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        {children}
      </ThemeProvider>
    </I18nProvider>
  );
}