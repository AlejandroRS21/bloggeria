import { getAllPosts } from "@/lib/api";
import type { BlogPost } from "@/types/post";
import PostGrid from "./PostGrid";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const posts = await getAllPosts();
  const featuredPost: BlogPost | undefined = posts[0];
  const remainingPosts = posts.slice(1);

  return <PostGrid featuredPost={featuredPost} posts={remainingPosts} />;
}