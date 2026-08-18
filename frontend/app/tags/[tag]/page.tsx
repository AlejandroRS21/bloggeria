import { notFound } from "next/navigation";
import { getPostsByTag, getAllTags } from "@/lib/api";
import TagPosts from "./TagPosts";

interface TagPageProps {
  params: Promise<{ tag: string }>;
}

export const dynamicParams = true;
export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: TagPageProps) {
  const { tag } = await params;
  const decoded = decodeURIComponent(tag);
  return {
    title: `Posts: ${decoded}`,
    description: `All blog posts tagged "${decoded}".`,
  };
}

export default async function TagPage({ params }: TagPageProps) {
  const { tag } = await params;
  const decoded = decodeURIComponent(tag);
  const posts = await getPostsByTag(decoded);

  if (posts.length === 0 && (await getAllTags()).length > 0) {
    notFound();
  }

  return <TagPosts decoded={decoded} posts={posts} />;
}