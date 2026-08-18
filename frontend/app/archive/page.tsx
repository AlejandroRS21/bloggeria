"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import PostCard from "@/components/PostCard";
import type { BlogPost } from "@/types/post";
import { useI18n } from "@/lib/i18n";

const PER_PAGE = 12;

export default function ArchivePage() {
  const { t } = useI18n();
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const loadPage = useCallback(async (p: number, q: string) => {
    setLoading(true);
    try {
      const mod = await import("@/lib/api");
      const result = await mod.getPaginatedPosts(p, PER_PAGE, q || undefined);
      setPosts(result.posts);
      setTotalPages(result.totalPages);
      setTotal(result.total);
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPage(page, search);
  }, [page, search, loadPage]);

  // Debounce search — reset to page 1 when search changes
  const [searchInput, setSearchInput] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  return (
    <>
      <section className="border-b border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
          <div className="mx-auto max-w-2xl">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
              {t("archive.title")}
            </h1>
            <p className="mt-3 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
              {t("archive.subtitle")}
            </p>
          </div>

          {/* Search */}
          <div className="mx-auto mt-8 max-w-xl">
            <div className="relative">
              <svg
                className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400 dark:text-zinc-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                />
              </svg>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder={t("archive.searchPh")}
                className="w-full rounded-xl border border-gray-300 bg-white py-3 pl-12 pr-4 text-sm shadow-sm placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-blue-500 dark:focus:ring-blue-950"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 py-12 sm:py-16 dark:bg-zinc-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          {loading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="animate-pulse rounded-xl border border-gray-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div className="mb-3 h-6 w-3/4 rounded bg-gray-200 dark:bg-zinc-800" />
                  <div className="mb-4 h-4 w-full rounded bg-gray-100 dark:bg-zinc-800/60" />
                  <div className="flex gap-2">
                    <div className="h-5 w-16 rounded-full bg-gray-100 dark:bg-zinc-800/60" />
                    <div className="h-5 w-20 rounded-full bg-gray-100 dark:bg-zinc-800/60" />
                  </div>
                </div>
              ))}
            </div>
          ) : posts.length === 0 ? (
            <div className="py-20 text-center">
              <p className="text-gray-500 dark:text-zinc-400">
                {search
                  ? t("archive.noResults", { q: search })
                  : t("archive.empty")}
              </p>
              {search && (
                <button
                  onClick={() => {
                    setSearchInput("");
                    setSearch("");
                  }}
                  className="mt-4 text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {t("archive.clear")}
                </button>
              )}
            </div>
          ) : (
            <>
              <p className="mb-6 text-sm text-gray-500 dark:text-zinc-400">
                {t(
                  total === 1 ? "archive.found_one" : "archive.found_other",
                  { count: total }
                )}
              </p>

              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {posts.map((post) => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <nav className="mt-12 flex items-center justify-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                  >
                    {t("archive.prev")}
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter(
                      (p) =>
                        p === 1 ||
                        p === totalPages ||
                        Math.abs(p - page) <= 2
                    )
                    .map((p, idx, arr) => (
                      <span key={p} className="contents">
                        {idx > 0 && arr[idx - 1] !== p - 1 && (
                          <span className="px-1 text-gray-400 dark:text-zinc-600">...</span>
                        )}
                        <button
                          onClick={() => setPage(p)}
                          className={`min-w-[2.5rem] rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                            p === page
                              ? "border-blue-600 bg-blue-600 text-white dark:border-blue-500 dark:bg-blue-600"
                              : "border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                          }`}
                        >
                          {p}
                        </button>
                      </span>
                    ))}

                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                  >
                    {t("archive.next")}
                  </button>
                </nav>
              )}
            </>
          )}
        </div>
      </section>
    </>
  );
}
