"use client";

import Link from "next/link";
import PostCard from "@/components/PostCard";
import type { BlogPost } from "@/types/post";
import { useI18n } from "@/lib/i18n";

export default function PostGrid({
  featuredPost,
  posts,
}: {
  featuredPost: BlogPost | undefined;
  posts: BlogPost[];
}) {
  const { t } = useI18n();

  return (
    <>
      {/* ── Blog Header ── */}
      <section className="border-b border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
          <div className="mx-auto max-w-2xl">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
              {t("home.title")}
            </h1>
            <p className="mt-3 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
              {t("home.subtitle")}
            </p>
          </div>
        </div>
      </section>

      {/* ── Posts Grid ── */}
      <section className="bg-gray-50 py-12 sm:py-16 dark:bg-zinc-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          {/* Featured post */}
          {featuredPost && (
            <div className="group mb-10">
              <Link
                href={`/posts/${featuredPost.slug}`}
                className="relative block overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition-all hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="grid md:grid-cols-5">
                  <div className="flex flex-col justify-center p-8 md:col-span-3">
                    <span className="mb-3 inline-block w-fit rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                      {t("home.featured")}
                    </span>
                    <h2 className="text-2xl font-bold text-gray-900 transition-colors group-hover:text-blue-600 md:text-3xl dark:text-zinc-100 dark:group-hover:text-blue-400">
                      {featuredPost.title}
                    </h2>
                    <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
                      {featuredPost.description}
                    </p>
                    <div className="mt-5 flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-zinc-400">
                      <span className="flex items-center gap-1.5">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                        </svg>
                        {featuredPost.author}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                        </svg>
                        {featuredPost.date}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        {featuredPost.reading_time} {t("posts.minRead")}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        {featuredPost.word_count} {t("home.words")}
                      </span>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {featuredPost.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600 dark:bg-zinc-800 dark:text-zinc-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="hidden items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-8 md:col-span-2 md:flex dark:from-blue-950/40 dark:to-indigo-950/40">
                    <div className="text-center">
                      <div className="text-6xl">📝</div>
                      <p className="mt-3 text-sm font-medium text-blue-600 dark:text-blue-400">
                        {t("home.readFull")}
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
              {featuredPost.style_source && featuredPost.style_source_url && (
                <a
                  href={featuredPost.style_source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-block rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:hover:bg-blue-900/60"
                >
                  {t("home.styleOf", { author: featuredPost.style_source })}
                </a>
              )}
            </div>
          )}

          {/* Remaining posts */}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>

          {/* Generate CTA */}
          <div className="mt-14 text-center">
            <p className="text-sm text-gray-500 dark:text-zinc-400">
              {t("home.cta")}
            </p>
            <Link
              href="/posts/new"
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
            >
              {t("home.ctaButton")}
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}