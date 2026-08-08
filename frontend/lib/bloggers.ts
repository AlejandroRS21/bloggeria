export type BloggerPreset = {
  id: string;
  name: string;
  url: string;
  niche: string;
};

export const PRESET_BLOGGERS: BloggerPreset[] = [
  { id: "javipas", name: "JaviPas", url: "https://javipas.com", niche: "Tecnología y cultura digital" },
  { id: "microsiervos", name: "Microsiervos", url: "https://www.microsiervos.com", niche: "Ciencia y curiosidades" },
];

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
