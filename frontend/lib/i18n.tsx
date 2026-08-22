"use client";

// Lightweight i18n: no dependency, no route restructuring.
// Dictionary-driven with a React context. Locale is resolved server-side
// (Vercel geo header + Accept-Language + cookie override) and hydrated here.
// ponytail: dictionary is ES-first with EN mirror; if a 3rd language appears,
// switch to next-intl (route groups) — that's the ceiling.

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

export type Locale = "es" | "en";

export const LOCALES: { code: Locale; label: string; flag: string }[] = [
  { code: "es", label: "Español", flag: "🇪🇸" },
  { code: "en", label: "English", flag: "🇬🇧" },
];

const es = {
  // nav
  "nav.blog": "Blog",
  "nav.tags": "Tags",
  "nav.archive": "Archivo",
  "nav.project": "Proyecto",
  "nav.generate": "Generar",
  "nav.lang": "Idioma",
  // header
  "theme.light": "Activar tema claro",
  "theme.dark": "Activar tema oscuro",
  // footer
  "footer.tagline": "Sistema multi-agente de IA que imita estilos de escritura.",
  "footer.rights": "Todos los derechos reservados.",
  "footer.tfg": "TFG — Especialización en IA y Big Data",
  // home
  "home.title": "Blog",
  "home.subtitle":
    "Artículos generados por el sistema multi-agente de IA. Cada post emula el estilo único de su autor de referencia.",
  "home.featured": "Destacado",
  "home.readFull": "Leer post completo →",
  "home.styleOf": "Estilo de {author}",
  "home.words": "palabras",
  "home.cta": "¿Quieres generar tu propio artículo con el estilo de tu escritor favorito?",
  "home.ctaButton": "Generar nuevo post",
  "welcome.title": "¿Qué quieres escribir hoy?",
  "welcome.body":
    "Elige un autor y un tema, y el sistema multi-agente escribirá un artículo con su estilo en unos minutos.",
  "welcome.start": "Empezar a escribir",
  "welcome.later": "Ahora no",
  // posts
  "posts.minRead": "min de lectura",
  "posts.min": "min",
  "posts.words": "palabras",
  "posts.styleOf": "Estilo de {author}",
  "posts.toc": "Tabla de contenidos",
  "posts.keywords": "Palabras clave",
  // card
  "card.words": "palabras",
  // tags
  "tags.title": "Tags",
  "tags.subtitle": "Navega por todos los temas cubiertos en el blog.",
  "tags.count_one": "{count} post",
  "tags.count_other": "{count} posts",
  "tags.empty": "Todavía no hay tags.",
  "tags.first": "Generar el primer post →",
  "tags.tagTitle": "Posts sobre {tag}",
  "tags.tagEmpty": "No hay posts con esta etiqueta.",
  "tags.allTags": "← Todos los tags",
  // archive
  "archive.title": "Archivo",
  "archive.subtitle": "Todos los posts generados, con búsqueda incluida.",
  "archive.searchPh": "Buscar posts por título, descripción o tag...",
  "archive.empty": "Todavía no hay posts.",
  "archive.noResults": "No hay resultados para \"{q}\".",
  "archive.clear": "Limpiar búsqueda",
  "archive.found_one": "{count} post encontrado",
  "archive.found_other": "{count} posts encontrados",
  "archive.prev": "← Anterior",
  "archive.next": "Siguiente →",
  // project
  "project.badge": "Arquitectura de Sistemas Multiagente",
  "project.heroTitle": "Arquitectura del Sistema",
  "project.heroSubtitle":
    "Detalle técnico y diseño de la infraestructura serverless para la mimetización y generación automatizada de blogs basada en procesamiento del lenguaje natural (NLP).",
  "project.generate": "Generar Artículo",
  "project.github": "Código en GitHub",
  "project.pipelineTitle": "Ciclo de Procesamiento del Pipeline",
  "project.pipelineDesc":
    "El proceso de orquestación asíncrono se divide en cuatro fases principales que transforman una solicitud de entrada en un artículo optimizado para la web.",
  "project.agentsTitle": "Orquestación del Pipeline (8 Agentes)",
  "project.agentsDesc":
    "El orquestador gestiona un flujo de trabajo cíclico y asíncrono en el que cada agente independiente asume una función especializada de análisis, redacción o control de calidad.",
  "project.ctaTitle": "Prueba la Generación de Artículos",
  "project.ctaDesc":
    "Define un tema, apunta a un blog de WordPress de referencia y observa cómo trabaja el pipeline multiagente.",
  "project.ctaButton": "Generar Post Ahora",
  // generate
  "gen.title": "Crear Nuevo Post",
  "gen.subtitle":
    "Configura el tema y la fuente de inspiración para que la IA haga su magia.",
  "gen.topicLabel": "Título del Artículo",
  "gen.topicPh": "Ej: El futuro de la IA en el desarrollo web",
  "gen.topicHint": "El moderador con IA validará que el tema sea profesional.",
  "gen.langLabel": "Idioma de Generación",
  "gen.langHint": "Los bloggers disponibles se filtran según el idioma elegido.",
  "gen.inspirationLabel": "Blogger de Inspiración",
  "gen.customUrlLabel": "URL de Inspiración (Opcional)",
  "gen.customUrlPh": "Ej: https://miblog.com",
  "gen.submit": "GENERAR POST AUTÓNOMO",
  "gen.errorLabel": "Error:",
  "gen.progress": "Progreso de Generación",
  "gen.running": "En proceso...",
  "gen.done": "Completado",
  "gen.pending": "Pendiente",
  "gen.wait": "Por favor, no cierres esta ventana. El proceso toma unos 2-3 minutos.",
  // not-found
  "nf.title": "Página no encontrada",
  "nf.subtitle": "La página que buscas no existe.",
  "nf.home": "Volver a inicio",
};

const en: Record<keyof typeof es, string> = {
  "nav.blog": "Blog",
  "nav.tags": "Tags",
  "nav.archive": "Archive",
  "nav.project": "Project",
  "nav.generate": "Generate",
  "nav.lang": "Language",
  "theme.light": "Switch to light theme",
  "theme.dark": "Switch to dark theme",
  "footer.tagline": "Multi-agent AI system that mimics writing styles.",
  "footer.rights": "All rights reserved.",
  "footer.tfg": "TFG — AI & Big Data specialization",
  "home.title": "Blog",
  "home.subtitle":
    "Posts generated by the multi-agent AI system. Each article emulates the unique style of its reference author.",
  "home.featured": "Featured",
  "home.readFull": "Read full post →",
  "home.styleOf": "Style of {author}",
  "home.words": "words",
  "home.cta": "Want to generate your own article in the style of your favorite writer?",
  "home.ctaButton": "Generate new post",
  "welcome.title": "What do you want to write today?",
  "welcome.body":
    "Pick an author and a topic, and the multi-agent system will write an article in their style in a few minutes.",
  "welcome.start": "Start writing",
  "welcome.later": "Not now",
  "posts.minRead": "min read",
  "posts.min": "min",
  "posts.words": "words",
  "posts.styleOf": "Style of {author}",
  "posts.toc": "Table of contents",
  "posts.keywords": "Keywords",
  "card.words": "words",
  "tags.title": "Tags",
  "tags.subtitle": "Browse every topic covered on the blog.",
  "tags.count_one": "{count} post",
  "tags.count_other": "{count} posts",
  "tags.empty": "No tags yet.",
  "tags.first": "Generate the first post →",
  "tags.tagTitle": "Posts about {tag}",
  "tags.tagEmpty": "No posts with this tag.",
  "tags.allTags": "← All tags",
  // archive
  "archive.title": "Archive",
  "archive.subtitle": "All generated posts, with search included.",
  "archive.searchPh": "Search posts by title, description or tag...",
  "archive.empty": "No posts yet.",
  "archive.noResults": "No results for \"{q}\".",
  "archive.clear": "Clear search",
  "archive.found_one": "{count} post found",
  "archive.found_other": "{count} posts found",
  "archive.prev": "← Previous",
  "archive.next": "Next →",
  "project.badge": "Multi-Agent Systems Architecture",
  "project.heroTitle": "System Architecture",
  "project.heroSubtitle":
    "Technical detail and design of the serverless infrastructure for automated blog style mimicry and generation based on natural language processing (NLP).",
  "project.generate": "Generate Article",
  "project.github": "Code on GitHub",
  "project.pipelineTitle": "Pipeline Processing Cycle",
  "project.pipelineDesc":
    "The asynchronous orchestration process is split into four main phases that transform an input request into a web-optimized article.",
  "project.agentsTitle": "Pipeline Orchestration (8 Agents)",
  "project.agentsDesc":
    "The orchestrator manages a cyclic, asynchronous workflow where each independent agent takes on a specialized analysis, writing, or quality-control role.",
  "project.ctaTitle": "Try Article Generation",
  "project.ctaDesc":
    "Define a topic, point to a reference WordPress blog, and watch the multi-agent pipeline work.",
  "project.ctaButton": "Generate Post Now",
  "gen.title": "Create New Post",
  "gen.subtitle":
    "Set the topic and inspiration source so the AI can do its magic.",
  "gen.topicLabel": "Article Title",
  "gen.topicPh": "E.g. The future of AI in web development",
  "gen.topicHint": "The AI moderator will validate that the topic is professional.",
  "gen.langLabel": "Generation Language",
  "gen.langHint": "Available bloggers are filtered by the chosen language.",
  "gen.inspirationLabel": "Inspiration Blogger",
  "gen.customUrlLabel": "Inspiration URL (Optional)",
  "gen.customUrlPh": "E.g. https://myblog.com",
  "gen.submit": "GENERATE AUTONOMOUS POST",
  "gen.errorLabel": "Error:",
  "gen.progress": "Generation Progress",
  "gen.running": "In progress...",
  "gen.done": "Completed",
  "gen.pending": "Pending",
  "gen.wait":
    "Please don't close this window. The process takes about 2-3 minutes.",
  "nf.title": "Page not found",
  "nf.subtitle": "The page you're looking for doesn't exist.",
  "nf.home": "Back to home",
};

export const dictionaries: Record<Locale, typeof es> = { es, en };

export type MessageKey = keyof typeof es;

export interface I18nContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: MessageKey, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({
  initialLocale,
  children,
}: {
  initialLocale: Locale;
  children: React.ReactNode;
}) {
  const [locale, setLocaleState] = useState<Locale>(initialLocale);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    try {
      document.cookie = `locale=${l};path=/;max-age=31536000;samesite=lax`;
    } catch {
      /* cookie blocked; locale lives for the session */
    }
  }, []);

  const t = useCallback(
    (key: MessageKey, vars?: Record<string, string | number>) => {
      let s: string = dictionaries[locale][key] ?? es[key] ?? key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          s = s.replace(`{${k}}`, String(v));
        }
      }
      return s;
    },
    [locale]
  );

  const value = useMemo(
    () => ({ locale, setLocale, t }),
    [locale, setLocale, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}