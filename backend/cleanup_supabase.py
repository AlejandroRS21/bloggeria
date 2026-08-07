#!/usr/bin/env python3
import os
import argparse
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Initialize Supabase client from environment variables."""
    # Try to load .env if running locally
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY/ROLE_KEY")
    
    return create_client(url, key)

def extract_storage_path(url: str, bucket_name: str) -> Optional[str]:
    """
    Extract the storage path from a Supabase public URL.
    Example: https://xyz.supabase.co/storage/v1/object/public/post-images/folder/image.png
    Bucket: post-images
    Path: folder/image.png
    """
    if not url or bucket_name not in url:
        return None
    
    try:
        parsed = urlparse(url)
        # The path starts with /storage/v1/object/public/{bucket}/
        prefix = f"/storage/v1/object/public/{bucket_name}/"
        if parsed.path.startswith(prefix):
            return parsed.path[len(prefix):]
    except Exception:
        pass
    return None

# Boilerplate detection (common LLM intro/outro patterns)
_BOILERPLATE_PATTERNS = [
    r"Aquí tienes (un|el) post",
    r"Espero que te guste",
    r"Como modelo de lenguaje",
    r"Lo siento, no puedo",
    r"Aquí hay una entrada de blog",
    r"I hope this helps",
    r"Sure, here's a blog post",
]

def quality_metrics(content: str) -> dict[str, Any]:
    """Return structural quality metrics for a post's content.

    These are the guard values logged before every deletion so a delete
    can be audited after the fact (REQ-1).
    """
    word_count = len(content.split())
    h2_count = len(re.findall(r"<h2", content, re.IGNORECASE))
    h3_count = len(re.findall(r"<h3", content, re.IGNORECASE))
    boilerplate = next(
        (p for p in _BOILERPLATE_PATTERNS if re.search(p, content, re.IGNORECASE)),
        None,
    )
    return {
        "word_count": word_count,
        "h2_count": h2_count,
        "h3_count": h3_count,
        "boilerplate": boilerplate,
    }

def detect_low_quality(content: str, min_words: int = 200, min_headings: int = 2) -> Tuple[bool, str]:
    """
    Detects if a post is of low quality based on word count, structure, and boilerplate.
    Returns (is_low_quality, reason)
    """
    if not content:
        return True, "Empty content"
    
    metrics = quality_metrics(content)
    
    # Word count
    if metrics["word_count"] < min_words:
        return True, f"Short content ({metrics['word_count']} words)"
    
    # Heading count (h2, h3)
    headings = metrics["h2_count"] + metrics["h3_count"]
    if headings < min_headings:
        return True, f"Poor structure ({metrics['h2_count']} H2, {metrics['h3_count']} H3)"
    
    # Boilerplate detection
    if metrics["boilerplate"]:
        return True, f"Found boilerplate: '{metrics['boilerplate']}'"
            
    return False, ""

def cleanup_posts(
    days: Optional[int] = None,
    keep_limit: Optional[int] = None,
    quality_check: bool = False,
    min_words: int = 200,
    min_headings: int = 2,
    bucket_name: str = "post-images",
    dry_run: bool = True
):
    """
    Delete old posts and their associated images.
    
    Args:
        days: Delete posts older than this many days.
        keep_limit: Keep only this many recent posts.
        bucket_name: Name of the storage bucket for images.
        dry_run: If True, only log what would be deleted.
    """
    sb = get_supabase_client()
    
    # 1. Determine which posts to delete
    query = sb.table("posts").select("id, slug, date, cover_image_url, content, title").order("date", desc=True)
    response = query.execute()
    all_posts = response.data or []
    
    posts_to_delete = []
    
    if keep_limit is not None:
        if len(all_posts) > keep_limit:
            posts_to_delete = all_posts[keep_limit:]
            print(f"Found {len(all_posts)} posts. Keeping the {keep_limit} newest. {len(posts_to_delete)} marked for deletion by limit.")
    
    elif days is not None:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        posts_to_delete = [p for p in all_posts if p.get("date", "9999") < cutoff_date]
        print(f"Deleting posts older than {cutoff_date}. Found {len(posts_to_delete)} matching posts.")
    
    # 1b. Quality-based filtering (can be combined with above or stand-alone)
    if quality_check:
        quality_deleted = []
        # We check ALL posts if no other limit was applied, or only the ones NOT already marked for deletion
        candidates = all_posts if not posts_to_delete else [p for p in all_posts if p not in posts_to_delete]
        
        for post in candidates:
            is_low, reason = detect_low_quality(post.get("content", ""), min_words, min_headings)
            if is_low:
                post["_cleanup_reason"] = reason
                quality_deleted.append(post)
        
        if quality_deleted:
            print(f"Found {len(quality_deleted)} low quality posts.")
            posts_to_delete.extend(quality_deleted)
    
    if not posts_to_delete:
        if not quality_check and days is None and keep_limit is None:
            print("No cleanup criteria provided (days, keep_limit, or quality). Aborting.")
        else:
            print("Nothing to delete.")
        return

    if not posts_to_delete:
        print("Nothing to delete.")
        return

    # 2. Perform deletion
    for post in posts_to_delete:
        post_id = post["id"]
        slug = post["slug"]
        img_url = post.get("cover_image_url")
        reason = post.get("_cleanup_reason", "Outdated or limit exceeded")
        
        print(f"\n--- Processing: {slug} (ID: {post_id}) ---")
        print(f"Reason: {reason}")
        # Log the guard values that this deletion decision is based on
        # (REQ-1: every deletion MUST be logged before execution).
        metrics = quality_metrics(post.get("content", ""))
        print(
            f"Guard values: words={metrics['word_count']} (min {min_words}), "
            f"headings={metrics['h2_count'] + metrics['h3_count']} (min {min_headings}), "
            f"boilerplate={'yes' if metrics['boilerplate'] else 'no'}"
        )
        
        # 2a. Storage Cleanup
        if img_url:
            storage_path = extract_storage_path(img_url, bucket_name)
            if storage_path:
                if dry_run:
                    print(f"[DRY RUN] Would delete storage file: {bucket_name}/{storage_path}")
                else:
                    try:
                        print(f"Deleting storage file: {bucket_name}/{storage_path}")
                        sb.storage.from_(bucket_name).remove([storage_path])
                    except Exception as e:
                        print(f"Error deleting storage file: {e}")
            else:
                print(f"Skipping storage: URL does not match bucket {bucket_name} or is not a public Supabase URL.")

        # 2b. Database Cleanup
        if dry_run:
            print(f"[DRY RUN] Would delete DB entry for post: {slug}")
        else:
            try:
                print(f"Deleting DB entry for post: {slug}")
                sb.table("posts").delete().eq("id", post_id).execute()
            except Exception as e:
                print(f"Error deleting DB entry: {e}")

    if dry_run:
        print("\nDRY RUN finished. No changes were made.")
    else:
        print(f"\nCleanup finished. Deleted {len(posts_to_delete)} posts.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup old or low quality blog posts from Supabase.")
    parser.add_argument("--days", type=int, help="Delete posts older than X days")
    parser.add_argument("--keep", type=int, help="Keep only the X newest posts")
    parser.add_argument("--quality", action="store_true", help="Enable quality-based filtering")
    parser.add_argument("--min-words", type=int, default=200, help="Min words for quality check (default: 200)")
    parser.add_argument("--min-headings", type=int, default=2, help="Min headings (H2+H3) for quality check (default: 2)")
    parser.add_argument("--bucket", default="post-images", help="Supabase Storage bucket name (default: post-images)")
    parser.add_argument("--run", action="store_true", help="Actually perform deletions (default is dry run)")
    
    args = parser.parse_args()
    
    # Ensure at least one cleanup method is specified
    if not (args.days or args.keep or args.quality):
        parser.error("At least one of --days, --keep, or --quality is required.")
    
    try:
        cleanup_posts(
            days=args.days,
            keep_limit=args.keep,
            quality_check=args.quality,
            min_words=args.min_words,
            min_headings=args.min_headings,
            bucket_name=args.bucket,
            dry_run=not args.run
        )
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
