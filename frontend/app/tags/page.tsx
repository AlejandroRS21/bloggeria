import { getAllTags } from "@/lib/api";
import TagCloud from "./TagCloud";

export const dynamic = "force-dynamic";

export default async function TagsPage() {
  const tags = await getAllTags();
  return <TagCloud tags={tags} />;
}