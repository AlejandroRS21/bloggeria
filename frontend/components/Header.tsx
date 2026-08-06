"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export default function Header() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isDark = mounted && resolvedTheme === "dark";

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200/80 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 dark:border-gray-800 dark:bg-slate-950/95 dark:supports-[backdrop-filter]:bg-slate-950/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2">
          <span className="text-2xl font-extrabold tracking-tight text-gray-900 transition-colors group-hover:text-blue-600 dark:text-gray-100">
            BLOGGER<span className="text-blue-600">IA</span>
          </span>
        </Link>

        <nav className="flex items-center gap-5">
          <Link
            href="/"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400"
          >
            Blog
          </Link>
          <Link
            href="/tags"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400"
          >
            Tags
          </Link>
          <Link
            href="/archive"
            className="text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400"
          >
            Archivo
          </Link>
          <Link
            href="/project"
            className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 sm:inline"
          >
            Proyecto
          </Link>

          <a
            href="https://github.com/AlejandroRS21/blogger-agent-tfg"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400 sm:inline"
          >
            GitHub
          </a>
          <button
            type="button"
            aria-label={isDark ? "Activar tema claro" : "Activar tema oscuro"}
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className="text-lg leading-none text-gray-600 transition-colors hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400"
          >
            {mounted ? (isDark ? "☀️" : "🌙") : "🌓"}
          </button>
          <Link
            href="/posts/new"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
          >
            Generar
          </Link>
        </nav>
      </div>
    </header>
  );
}