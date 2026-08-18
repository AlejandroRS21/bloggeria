import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Providers from "./providers";
import { resolveLocale } from "@/lib/i18n-server";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Blogger Agent | Multi-agent AI system",
    template: "%s | Blogger Agent",
  },
  description:
    "Multi-agent AI system for stylistic blog emulation. Generates blog content in the style of your favorite writer.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await resolveLocale();

  return (
    <html lang={locale} suppressHydrationWarning className={inter.variable}>
      <body className="flex min-h-screen flex-col bg-white font-sans text-gray-900 antialiased dark:bg-slate-950 dark:text-gray-100">
        <Providers locale={locale}>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}