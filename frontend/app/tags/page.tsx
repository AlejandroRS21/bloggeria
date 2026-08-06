import Link from "next/link";
import { getAllTags } from "@/lib/api";

export const revalidate = 0;

function getTagColor(tag: string): string {
  const colors = [
    "bg-blue-100 text-blue-700 ring-blue-200 dark:bg-blue-950/80 dark:text-blue-300 dark:ring-blue-900",
    "bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:ring-emerald-900",
    "bg-violet-100 text-violet-700 ring-violet-200 dark:bg-violet-950/80 dark:text-violet-300 dark:ring-violet-900",
    "bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:ring-amber-900",
    "bg-rose-100 text-rose-700 ring-rose-200 dark:bg-rose-950/80 dark:text-rose-300 dark:ring-rose-900",
    "bg-cyan-100 text-cyan-700 ring-cyan-200 dark:bg-cyan-950/80 dark:text-cyan-300 dark:ring-cyan-900",
    "bg-orange-100 text-orange-700 ring-orange-200 dark:bg-orange-950/80 dark:text-orange-300 dark:ring-orange-900",
    "bg-teal-100 text-teal-700 ring-teal-200 dark:bg-teal-950/80 dark:text-teal-300 dark:ring-teal-900",
    "bg-pink-100 text-pink-700 ring-pink-200 dark:bg-pink-950/80 dark:text-pink-300 dark:ring-pink-900",
    "bg-indigo-100 text-indigo-700 ring-indigo-200 dark:bg-indigo-950/80 dark:text-indigo-300 dark:ring-indigo-900",
  ];
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

export default async function TagsPage() {
  const tags = await getAllTags();

  return (
    <>
      <section className="border-b border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
          <div className="mx-auto max-w-2xl">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
              Tags
            </h1>
            <p className="mt-3 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
              Navegá por todos los temas cubiertos en el blog.
            </p>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 py-12 sm:py-16 dark:bg-zinc-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          {tags.length === 0 ? (
            <div className="py-20 text-center">
              <p className="text-gray-500 dark:text-zinc-400">Todavía no hay tags.</p>
              <Link
                href="/posts/new"
                className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Generar el primer post →
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap justify-center gap-4">
              {tags.map(({ tag, count }) => {
                const size =
                  count <= 1
                    ? "text-sm"
                    : count <= 3
                      ? "text-base"
                      : count <= 5
                        ? "text-lg"
                        : "text-xl";
                return (
                  <Link
                    key={tag}
                    href={`/tags/${encodeURIComponent(tag.toLowerCase())}`}
                    className={`inline-flex items-center gap-2 rounded-full px-4 py-2 font-medium shadow-sm ring-1 transition-all hover:scale-105 hover:shadow-md ${getTagColor(tag)} ${size}`}
                  >
                    {tag}
                    <span className="rounded-full bg-white/60 px-2 py-0.5 text-xs font-semibold dark:bg-black/40">
                      {count}
                    </span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
