import { NextResponse } from "next/server";
import { getBloggerBySlug, normalizeUrl } from "@/lib/bloggers";

export const runtime = "nodejs";
export const maxDuration = 300;

interface GenerateRequestBody {
  topic: string;
  bloggerSlug: string;
  language: "es" | "en";
  customUrl?: string;
}

// Same endpoint the browser used to call directly (CORS/timeout issues).
// Production overrides it via MODAL_WEBHOOK_URL (SSR only — never NEXT_PUBLIC).
const DEFAULT_WEBHOOK_URL = "https://alejandrors21--blogger-agent-tfg-webhook.modal.run";

export async function POST(request: Request) {
  let body: GenerateRequestBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ success: false, error: "Validation failed" }, { status: 400 });
  }

  const { topic, bloggerSlug, language, customUrl } = body ?? {};

  if (
    typeof topic !== "string" ||
    topic.trim() === "" ||
    typeof bloggerSlug !== "string" ||
    (language !== "es" && language !== "en") ||
    (customUrl !== undefined && typeof customUrl !== "string")
  ) {
    return NextResponse.json({ success: false, error: "Validation failed" }, { status: 400 });
  }

  const preset = getBloggerBySlug(bloggerSlug);
  if (!preset) {
    return NextResponse.json({ success: false, error: "Blogger no encontrado" }, { status: 400 });
  }

  const webhookUrl =
    process.env.MODAL_WEBHOOK_URL ||
    process.env.NEXT_PUBLIC_MODAL_WEBHOOK_URL ||
    DEFAULT_WEBHOOK_URL;

  const bloggerUrls = [preset.url];
  const custom = customUrl?.trim();
  if (custom) {
    try {
      bloggerUrls.push(normalizeUrl(custom));
    } catch {
      return NextResponse.json({ success: false, error: "Custom URL inválida" }, { status: 400 });
    }
  }

  try {
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: topic.trim(),
        blogger_urls: bloggerUrls,
        blogger_name: preset.name,
        provider: "gemini",
        language,
      }),
      // Route budget is 300s; abort before the platform kills the request
      // so we can map to a clean 504 instead of a raw 500.
      signal: AbortSignal.timeout(280_000),
    });

    let result: { success?: boolean; error?: string; data?: { slug?: string } } | null = null;
    try {
      result = await response.json();
    } catch {
      // Backend returned a non-JSON body; fall through to status-based mapping.
    }

    if (!response.ok || !result?.success) {
      const message =
        result?.error ||
        `El backend respondió con un error (HTTP ${response.status}). Inténtalo de nuevo.`;
      return NextResponse.json({ success: false, error: message }, { status: 500 });
    }

    return NextResponse.json({
      success: true,
      postSlug: result?.data?.slug || (result as { post_slug?: string })?.post_slug || null,
    });
  } catch (err) {
    const aborted =
      err instanceof DOMException && (err.name === "TimeoutError" || err.name === "AbortError");
    return NextResponse.json(
      { success: false, error: aborted ? "El backend tardó demasiado en responder" : "Error de red al contactar el backend" },
      { status: aborted ? 504 : 500 }
    );
  }
}