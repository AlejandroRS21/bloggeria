"use client";

import Link from "next/link";
import PostCard from "@/components/PostCard";
import type { BlogPost } from "@/types/post";
import { useI18n } from "@/lib/i18n";

export default function TagPosts({
  decoded,
  posts,
}: {
  decoded: string;
  posts: BlogPost[];
}) {
  const { t } = useI18n();

  return (
    <>
      <section className="border-b border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
          <div className="mx-auto max-w-2xl">
            <nav className="mb-4">
              <Link
                href="/tags"
                className="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                {t("tags.allTags")}
              </Link>
            </nav>
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
              {t("tags.tagTitle", { tag: decoded })}
            </h1>
            <p className="mt-3 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
              {t(
                posts.length === 1 ? "tags.count_one" : "tags.count_other",
                { count: posts.length }
              )}
            </p>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 py-12 sm:py-16 dark:bg-zinc-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          {posts.length === 0 ? (
            <div className="py-20 text-center">
              <p className="text-gray-500 dark:text-zinc-400">
                {t("tags.tagEmpty")}
              </p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {posts.map((post) => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}