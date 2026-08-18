// Server-side locale resolution.
// Priority: cookie override > Vercel geo country > Accept-Language > "es".
// Vercel injects x-vercel-ip-country on every request at no cost.

import { cookies, headers } from "next/headers";
import type { Locale } from "./i18n";

const ENGLISH_COUNTRIES = new Set([
  "US", "GB", "AU", "CA", "IE", "NZ", "ZA", "SG", "IN", "PH", "NG", "GH", "KE", "JM", "TT",
]);

const SPANISH_COUNTRIES = new Set([
  "ES", "MX", "AR", "CO", "PE", "VE", "CL", "EC", "GT", "CU", "BO", "DO", "HN", "PY", "SV", "NI", "CR", "PA", "UY", "PR",
]);

export async function resolveLocale(): Promise<Locale> {
  // 1. explicit cookie choice wins
  const cookieStore = await cookies();
  const cookie = cookieStore.get("locale")?.value;
  if (cookie === "es" || cookie === "en") return cookie;

  // 2. Vercel geo header (country code)
  const h = await headers();
  const country = h.get("x-vercel-ip-country")?.toUpperCase();
  if (country && ENGLISH_COUNTRIES.has(country)) return "en";
  if (country && SPANISH_COUNTRIES.has(country)) return "es";

  // 3. Accept-Language
  const acceptLang = h.get("accept-language") ?? "";
  const first = acceptLang.split(",")[0]?.trim().toLowerCase() ?? "";
  if (first.startsWith("en")) return "en";
  if (first.startsWith("es")) return "es";

  // 4. default
  return "es";
}