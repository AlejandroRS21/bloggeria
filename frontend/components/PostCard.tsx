"use client";

import Link from "next/link";
import type { BlogPost } from "@/types/post";
import { useI18n } from "@/lib/i18n";

interface PostCardProps {
  post: BlogPost;
}

export default function PostCard({ post }: PostCardProps) {
  const { t } = useI18n();
  const tagColors: Record<string, string> = {
    Tecnologia: "bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300",
    Innovacion: "bg-green-100 text-green-700 dark:bg-green-950/60 dark:text-green-300",
    Analisis: "bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300",
    Ciencia: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950/60 dark:text-cyan-300",
  };

  return (
    <article className="group rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900">
      <Link href={`/posts/${post.slug}`} className="block">
        <h3 className="text-xl font-bold text-gray-900 transition-colors group-hover:text-blue-600 dark:text-zinc-100 dark:group-hover:text-blue-400">
          {post.title}
        </h3>

        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
          {post.description}
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {post.tags.map((tag) => (
            <span
              key={tag}
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                tagColors[tag] || "bg-gray-100 text-gray-600 dark:bg-zinc-800 dark:text-zinc-400"
              }`}
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-4 text-xs text-gray-500 dark:text-zinc-400">
          <span className="flex items-center gap-1">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
            {post.author}
          </span>
          <span>{post.date}</span>
          <span className="flex items-center gap-1">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            {post.reading_time} {t("posts.min")}
          </span>
          <span className="flex items-center gap-1">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {post.word_count} {t("card.words")}
          </span>
        </div>
      </Link>
      {post.style_source && post.style_source_url && (
        <a
          href={post.style_source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:hover:bg-blue-900/60"
        >
          {t("posts.styleOf", { author: post.style_source })}
        </a>
      )}
    </article>
  );
}
