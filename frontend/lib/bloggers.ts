export type BloggerPreset = {
  id: string;
  name: string;
  url: string;
  niche: string;
  lang: "es" | "en";
};

export const PRESET_BLOGGERS: BloggerPreset[] = [
  // Español primero, inglés después (convención UI: nicho en español)
  { id: "javipas", name: "JaviPas", url: "https://javipas.com", niche: "Tecnología y cultura digital", lang: "es" },
  { id: "microsiervos", name: "Microsiervos", url: "https://www.microsiervos.com", niche: "Ciencia y curiosidades", lang: "es" },
  { id: "simonwillison", name: "Simon Willison", url: "https://simonwillison.net", niche: "Tecnología, IA y desarrollo web", lang: "en" },
  { id: "jvns", name: "Julia Evans", url: "https://jvns.ca", niche: "Programación y sistemas", lang: "en" },
  { id: "danluu", name: "Dan Luu", url: "https://danluu.com", niche: "Ingeniería de software y análisis técnico", lang: "en" },
  { id: "overreacted", name: "Dan Abramov", url: "https://overreacted.io", niche: "Desarrollo frontend y React", lang: "en" },
];

export function getBloggersByLanguage(lang: "es" | "en"): BloggerPreset[] {
  return PRESET_BLOGGERS.filter((b) => b.lang === lang);
}

export function getBloggerBySlug(slug: string): BloggerPreset | undefined {
  return PRESET_BLOGGERS.find((b) => b.id === slug);
}

/**
 * Normalizes a user-supplied blog URL to an absolute http(s) URL.
 * - Bare domains (e.g. "miblog.com") get "https://" prepended.
 * - Non-http(s) schemes and dot-less hostnames (e.g. "not-a-url") are rejected.
 * Throws on invalid input.
 */
export function normalizeUrl(input: string): string {
  let value = input.trim();
  if (value === "") throw new Error("URL vacía");
  if (!/^[a-z][a-z0-9+.-]*:/i.test(value)) {
    value = `https://${value}`;
  }
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("URL inválida");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("URL inválida");
  }
  if (!/^[a-z0-9-]+(\.[a-z0-9-]+)+$/i.test(parsed.hostname)) {
    throw new Error("URL inválida");
  }
  return parsed.toString();
}
