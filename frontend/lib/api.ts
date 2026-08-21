import type { BlogPost } from "@/types/post";
import { supabase } from "./supabase";

export async function getAllPosts(): Promise<BlogPost[]> {
  try {
    const { data, error } = await supabase
      .from("posts")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) {
      console.warn("[API] Supabase error fetching posts:", error.message);
      return [];
    }

    return ((data ?? []) as BlogPost[]).filter(
      (p) => (p as any).status !== "failed"
    );
  } catch (err) {
    console.warn("[API] Failed to fetch posts:", err);
    return [];
  }
}

export async function fetchPost(slug: string): Promise<BlogPost | null> {
  try {
    const { data, error } = await supabase
      .from("posts")
      .select("*")
      .eq("slug", slug)
      .single();

    if (error) {
      console.warn(`[API] Supabase error fetching post "${slug}":`, error.message);
      return null;
    }

    return data as BlogPost;
  } catch {
    return null;
  }
}

/** Aggregate all unique tags with post counts */
export async function getAllTags(): Promise<{ tag: string; count: number }[]> {
  const posts = await getAllPosts();
  const tagMap = new Map<string, number>();
  for (const post of posts) {
    for (const tag of post.tags) {
      tagMap.set(tag, (tagMap.get(tag) || 0) + 1);
    }
  }
  return Array.from(tagMap.entries())
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count);
}

/** Fetch posts that have a specific tag */
export async function getPostsByTag(tag: string): Promise<BlogPost[]> {
  const posts = await getAllPosts();
  return posts.filter((post) =>
    post.tags.some((t) => t.toLowerCase() === tag.toLowerCase())
  );
}

/** Paginated posts with optional search filter */
export async function getPaginatedPosts(
  page: number = 1,
  perPage: number = 12,
  search?: string
): Promise<{ posts: BlogPost[]; total: number; totalPages: number }> {
  let posts = await getAllPosts();

  if (search) {
    const q = search.toLowerCase();
    posts = posts.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q)) ||
        p.keywords.some((k) => k.toLowerCase().includes(q))
    );
  }

  const total = posts.length;
  const totalPages = Math.ceil(total / perPage);
  const start = (page - 1) * perPage;
  return { posts: posts.slice(start, start + perPage), total, totalPages };
}
