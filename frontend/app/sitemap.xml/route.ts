export const dynamic = "force-static";

import { getAllPosts } from "@/lib/api";

const BASE_URL = "https://bloggeria-cf0iyl2bv-alejandrors21s-projects.vercel.app";

interface SitemapEntry {
  url: string;
  priority: string;
  lastmod?: string;
}

export async function GET() {
  const staticPages: SitemapEntry[] = [
    { url: "/", priority: "1.0" },
    { url: "/project", priority: "0.8" },
    { url: "/archive", priority: "0.9" },
    { url: "/tags", priority: "0.7" },
    { url: "/posts/new", priority: "0.7" },
  ];

  const posts = await getAllPosts();
  const postPages: SitemapEntry[] = posts.map((post) => ({
    url: `/posts/${post.slug}`,
    priority: "0.6",
    lastmod: post.date,
  }));

  const tagMap = new Map<string, boolean>();
  for (const post of posts) {
    for (const tag of post.tags) {
      tagMap.set(tag.toLowerCase(), true);
    }
  }
  const tagPages: SitemapEntry[] = Array.from(tagMap.keys()).map((tag) => ({
    url: `/tags/${encodeURIComponent(tag)}`,
    priority: "0.5",
  }));

  const allPages: SitemapEntry[] = [...staticPages, ...postPages, ...tagPages];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allPages
  .map(
    (page) => `  <url>
    <loc>${BASE_URL}${page.url}</loc>
    <priority>${page.priority}</priority>
    ${page.lastmod ? `    <lastmod>${page.lastmod}</lastmod>` : ""}
  </url>`
  )
  .join("\n")}
</urlset>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
    },
  });
}
