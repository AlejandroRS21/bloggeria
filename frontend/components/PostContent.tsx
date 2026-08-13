"use client";

import Link from "next/link";
import type { BlogPost } from "@/types/post";

interface PostContentProps {
  post: BlogPost;
  crossLinkedContent?: string;
}

export default function PostContent({ post, crossLinkedContent }: PostContentProps) {
  const hasHeadings =
    post.html_structure?.headings &&
    post.html_structure.headings.length > 0;

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header info */}
      <div className="mb-8 border-b border-gray-200 pb-6 dark:border-zinc-800">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
          {post.title}
        </h1>

        <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-zinc-400">
          <span className="font-medium text-gray-700 dark:text-zinc-300">{post.author}</span>
          <span className="text-gray-300 dark:text-zinc-700">|</span>
          <span>{post.date}</span>
          <span className="text-gray-300 dark:text-zinc-700">|</span>
          <span>{post.reading_time} min de lectura</span>
          <span className="text-gray-300 dark:text-zinc-700">|</span>
          <span>{post.word_count} palabras</span>
          {post.style_source && post.style_source_url && (
            <a
              href={post.style_source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:hover:bg-blue-900/60"
            >
              Estilo de {post.style_source}
            </a>
          )}
        </div>

        {post.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <Link
                key={tag}
                href={`/tags/${encodeURIComponent(tag.toLowerCase())}`}
                className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:hover:bg-blue-900/60"
              >
                {tag}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Table of contents */}
      {hasHeadings && (
        <div className="mb-8 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-zinc-800 dark:bg-zinc-900/60">
          <h3 className="mb-2 text-sm font-semibold text-gray-900 dark:text-zinc-100">
            Tabla de contenidos
          </h3>
          <nav>
            <ul className="space-y-1">
              {post.html_structure!.headings.map((heading, index) => (
                <li key={index}>
                  <a
                    href={`#heading-${index}`}
                    className="text-sm text-blue-600 underline decoration-blue-200 underline-offset-2 hover:text-blue-800 dark:text-blue-400 dark:decoration-blue-800 dark:hover:text-blue-300"
                  >
                    {heading}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      )}

      {/* Blog content with prose styles */}
      <div
        className="prose prose-lg max-w-none prose-img:rounded-2xl prose-img:shadow-md prose-img:mx-auto prose-figure:my-8 prose-figcaption:text-center prose-figcaption:text-sm prose-figcaption:text-gray-500 dark:prose-figcaption:text-zinc-400"
        dangerouslySetInnerHTML={{ __html: crossLinkedContent ?? post.content }}
      />

      {/* Meta keywords */}
      {post.keywords.length > 0 && (
        <div className="mt-10 border-t border-gray-200 pt-6 dark:border-zinc-800">
          <p className="text-xs text-gray-500 dark:text-zinc-400">
            Palabras clave:{" "}
            <span className="text-gray-700 dark:text-zinc-300">{post.keywords.join(", ")}</span>
          </p>
        </div>
      )}
    </div>
  );
}
