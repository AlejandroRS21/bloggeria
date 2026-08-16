export type Niche = "tecnologia" | "noticias" | "literatura" | "comida" | "salsa_rosa";
export type BloggerLang = "es" | "en";

export const NICHE_LABELS: Record<Niche, { label: string; emoji: string }> = {
  tecnologia: { label: "Tecnología", emoji: "💻" },
  noticias: { label: "Noticias y Actualidad", emoji: "📰" },
  literatura: { label: "Literatura y Libros", emoji: "📚" },
  comida: { label: "Gastronomía y Comida", emoji: "🍳" },
  salsa_rosa: { label: "Salsa Rosa y Cotilleos", emoji: "🍷" },
};

export type BloggerPreset = {
  id: string;
  name: string;
  url: string;
  niche: Niche;
  lang: BloggerLang;
};

export const PRESET_BLOGGERS: BloggerPreset[] = [
  // ── Tecnología ──
  { id: "javipas", name: "JaviPas", url: "https://javipas.com", niche: "tecnologia", lang: "es" },
  { id: "microsiervos", name: "Microsiervos", url: "https://www.microsiervos.com", niche: "tecnologia", lang: "es" },
  { id: "simonwillison", name: "Simon Willison", url: "https://simonwillison.net", niche: "tecnologia", lang: "en" },
  { id: "jvns", name: "Julia Evans", url: "https://jvns.ca", niche: "tecnologia", lang: "en" },
  { id: "danluu", name: "Dan Luu", url: "https://danluu.com", niche: "tecnologia", lang: "en" },
  { id: "overreacted", name: "Dan Abramov", url: "https://overreacted.io", niche: "tecnologia", lang: "en" },
  // ── Noticias y Actualidad ──
  { id: "kiko-llaneras", name: "Kiko Llaneras", url: "https://elpais.com/opinion/analytics/", niche: "noticias", lang: "es" },
  { id: "ezra-klein", name: "Ezra Klein", url: "https://www.nytimes.com/column/ezra-klein", niche: "noticias", lang: "en" },
  // ── Literatura y Libros ──
  { id: "zenda-libros", name: "Zenda", url: "https://www.zendalibros.com", niche: "literatura", lang: "es" },
  { id: "marginalian", name: "The Marginalian", url: "https://www.themarginalian.org", niche: "literatura", lang: "en" },
  // ── Gastronomía y Comida ──
  { id: "el-comidista", name: "El Comidista", url: "https://elcomidista.elpais.com", niche: "comida", lang: "es" },
  { id: "serious-eats", name: "Serious Eats", url: "https://www.seriouseats.com", niche: "comida", lang: "en" },
  // ── Salsa Rosa y Cotilleos ──
  { id: "lecturas-cotilleos", name: "Lecturas", url: "https://www.lecturas.com", niche: "salsa_rosa", lang: "es" },
];

export function getBloggersByLanguage(lang: BloggerLang): BloggerPreset[] {
  return PRESET_BLOGGERS.filter((b) => b.lang === lang);
}

export function getBloggerBySlug(slug: string): BloggerPreset | undefined {
  return PRESET_BLOGGERS.find((b) => b.id === slug);
}

export function getBloggersByNiche(niche: Niche): BloggerPreset[] {
  return PRESET_BLOGGERS.filter((b) => b.niche === niche);
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