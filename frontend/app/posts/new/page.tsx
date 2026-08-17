"use client";

import { useReducer, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getBloggersByLanguage, getBloggerBySlug, normalizeUrl, NICHE_LABELS } from "@/lib/bloggers";
import { supabase } from "@/lib/supabase";

const DEFAULT_WEBHOOK_URL = "https://alejandrors21--blogger-agent-tfg-webhook.modal.run";

const PHASES = [
  { id: "safety", label: "Protección de Contenido", icon: "🛡️", duration: 5000 },
  { id: "style", label: "Análisis de Estilo", icon: "🕵️", duration: 8000 },
  { id: "keywords", label: "Extracción de Keywords", icon: "🔑", duration: 4000 },
  { id: "generation", label: "Generación de Contenido", icon: "📝", duration: 25000 },
  { id: "critique", label: "Refinamiento y Crítica", icon: "🧐", duration: 15000 },
  { id: "images", label: "Selección de Imágenes", icon: "🖼️", duration: 7000 },
  { id: "publishing", label: "Guardando en Base de Datos", icon: "🚀", duration: 6000 },
];

type Language = "es" | "en";

type State = {
  topic: string;
  selectedBloggerSlug: string | null;
  customUrl: string;
  language: Language;
  isGenerating: boolean;
  currentPhase: number;
  progress: number;
  error: string | null;
};

type Action =
  | { type: 'SET_TOPIC'; payload: string }
  | { type: 'SELECT_BLOGGER'; payload: string }
  | { type: 'RESET_BLOGGER_SELECTION' }
  | { type: 'SET_CUSTOM_URL'; payload: string }
  | { type: 'SET_LANGUAGE'; payload: Language }
  | { type: 'START_GENERATION' }
  | { type: 'NEXT_PHASE' }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'RESET' };

const initialState: State = {
  topic: "",
  selectedBloggerSlug: null,
  customUrl: "",
  language: "es",
  isGenerating: false,
  currentPhase: 0,
  progress: 0,
  error: null,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_TOPIC':
      return { ...state, topic: action.payload };
    case 'SELECT_BLOGGER':
      return { ...state, selectedBloggerSlug: state.selectedBloggerSlug === action.payload ? null : action.payload };
    case 'RESET_BLOGGER_SELECTION':
      return { ...state, selectedBloggerSlug: null };
    case 'SET_CUSTOM_URL':
      return { ...state, customUrl: action.payload };
    case 'SET_LANGUAGE':
      return { ...state, language: action.payload };
    case 'START_GENERATION':
      return { ...state, isGenerating: true, currentPhase: 0, progress: 0, error: null };
    case 'NEXT_PHASE': {
      const nextPhase = state.currentPhase + 1;
      const stepProgress = 100 / PHASES.length;
      return {
        ...state,
        currentPhase: nextPhase,
        progress: Math.min(state.progress + stepProgress, 100)
      };
    }
    case 'SET_ERROR':
      return { ...state, error: action.payload, isGenerating: false };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export default function NewPostPage() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const { push, refresh } = useRouter();

  const filteredBloggers = useMemo(
    () => getBloggersByLanguage(state.language),
    [state.language]
  );

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (state.isGenerating && state.currentPhase < PHASES.length) {
      const phase = PHASES[state.currentPhase];
      timer = setTimeout(() => {
        dispatch({ type: 'NEXT_PHASE' });
      }, phase.duration);
    }
    return () => clearTimeout(timer);
  }, [state.isGenerating, state.currentPhase]);

  /** Client-side content moderation — quick pattern check before hitting the API */
  const isTopicAppropriate = (topic: string): string | null => {
    const trimmed = topic.trim().toLowerCase();
    if (trimmed.length < 2) return "El tema es demasiado corto.";

    const blockedPatterns = [
      /\b(sexo|sexual|pornograf[íi]a|xxx|porno|desnud[oa]s?|er[óo]tico)\b/i,
      /\b(violaci[óo]n|maltrato|tortura|gore|sangriento)\b/i,
      /\b(odio|discriminaci[óo]n|racista|xen[óo]fobo|nazi)\b/i,
      /\b(armas?|explosivos?|drogas?|narcotr[áa]fico)\b/i,
      /\b(autolesi[óo]n|suicidio|bullying|acoso)\b/i,
    ];

    for (const pattern of blockedPatterns) {
      if (pattern.test(trimmed)) {
        return `⛔ El tema contiene lenguaje que podría ser inapropiado. Elige un tema profesional para el blog.`;
      }
    }

    return null;
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const lang = e.target.value as Language;
    dispatch({ type: 'SET_LANGUAGE', payload: lang });
    dispatch({ type: 'RESET_BLOGGER_SELECTION' });
  };

  const pollSupabaseForPost = async (jobId: string): Promise<string | null> => {
    const startTime = Date.now();
    const timeoutMs = 300_000; // 300s
    const pollIntervalMs = 3000; // 3000ms
    const coldStartNoticeMs = 60_000; // 60s
    let coldStartNotified = false;

    while (Date.now() - startTime < timeoutMs) {
      const elapsed = Date.now() - startTime;
      if (elapsed >= coldStartNoticeMs && !coldStartNotified) {
        coldStartNotified = true;
        setInfoMessage("La GPU se está encendiendo, puede tardar unos minutos.");
      }

      const { data } = await supabase
        .from("posts")
        .select("slug, status, error_message")
        .eq("job_id", jobId)
        .maybeSingle();

      if (data) {
        if (data.status === "failed") {
          throw new Error(data.error_message || "La generación del post ha fallado en el servidor.");
        }
        if (data.slug) {
          return data.slug;
        }
      }
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setInfoMessage(null);

    const moderationError = isTopicAppropriate(state.topic);
    if (moderationError) {
      dispatch({ type: 'SET_ERROR', payload: moderationError });
      return;
    }
    if (!state.selectedBloggerSlug) {
      dispatch({ type: 'SET_ERROR', payload: 'Selecciona un blogger de inspiración' });
      return;
    }

    const preset = getBloggerBySlug(state.selectedBloggerSlug);
    if (!preset) {
      dispatch({ type: 'SET_ERROR', payload: 'Blogger no encontrado' });
      return;
    }

    const bloggerUrls = [preset.url];
    const custom = state.customUrl.trim();
    if (custom) {
      try {
        bloggerUrls.push(normalizeUrl(custom));
      } catch {
        dispatch({ type: 'SET_ERROR', payload: 'Custom URL inválida' });
        return;
      }
    }

    const jobId = crypto.randomUUID();
    dispatch({ type: 'START_GENERATION' });

    try {
      const webhookUrl = process.env.NEXT_PUBLIC_MODAL_WEBHOOK_URL || DEFAULT_WEBHOOK_URL;
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: state.topic.trim(),
          blogger_urls: bloggerUrls,
          blogger_name: preset.name,
          blogger_preset_id: preset.id,
          provider: "gemini",
          language: state.language,
          job_id: jobId,
        }),
      });

      let resData: any = null;
      try {
        resData = await response.json();
      } catch {}

      if (!response.ok || !resData?.success) {
        const rawError = resData?.error || `Error del servidor (HTTP ${response.status}). Inténtalo de nuevo.`;
        const isRateLimited =
          response.status === 429 || (typeof rawError === "string" && rawError.includes("Límite de tasa"));
        const errorMsg = isRateLimited
          ? "Has alcanzado el límite de 5 generaciones por hora. Vuelve a intentarlo más tarde."
          : rawError;
        dispatch({ type: 'SET_ERROR', payload: errorMsg });
        return;
      }

      // Webhook returned 200 with status: queued. Poll Supabase.
      setInfoMessage("Tu post está en cola de generación. Puede tardar unos minutos.");
      const slug = await pollSupabaseForPost(jobId);

      if (slug) {
        // Post found, redirect to post or homepage
        push(`/posts/${slug}`);
        refresh();
      } else {
        // Polling timed out (300s)
        setInfoMessage("El post se está generando en segundo plano y aparecerá en el inicio al terminar.");
      }
    } catch (err: any) {
      const message =
        err?.message === "Failed to fetch"
          ? "No se pudo conectar con el servidor. Comprueba tu conexión e inténtalo de nuevo."
          : (err?.message || "Error desconocido en la generación");
      dispatch({ type: 'SET_ERROR', payload: message });
    }
  };

  const canSubmit = state.topic.trim().length > 0 && state.selectedBloggerSlug !== null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-12 text-zinc-900 dark:text-zinc-100">
      <div className="mb-12">
        <h1 className="mb-4 text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">Crear Nuevo Post</h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400">
          Configura el tema y la fuente de inspiración para que la IA haga su magia.
        </p>
      </div>

      {!state.isGenerating ? (
        <form onSubmit={handleSubmit} className="space-y-8 rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <div className="space-y-2">
            <label htmlFor="topic" className="block text-sm font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Título del Artículo
            </label>
            <input
              id="topic"
              type="text"
              required
              value={state.topic}
              onChange={(e) => dispatch({ type: 'SET_TOPIC', payload: e.target.value })}
              placeholder="Ej: El futuro de la IA en el desarrollo web"
              className="w-full rounded-xl border border-zinc-300 bg-transparent px-4 py-3 outline-none transition-all focus:ring-2 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
            />
            <p className="text-xs italic text-zinc-500 dark:text-zinc-400">El moderador con IA validará que el tema sea profesional.</p>
          </div>

          <div className="space-y-2">
            <label htmlFor="language" className="block text-sm font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Idioma de Generación
            </label>
            <select
              id="language"
              value={state.language}
              onChange={handleLanguageChange}
              className="w-full rounded-xl border border-zinc-300 bg-transparent px-4 py-3 outline-none transition-all focus:ring-2 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
            <p className="text-xs italic text-zinc-500 dark:text-zinc-400">Los bloggers disponibles se filtran según el idioma elegido.</p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              Blogger de Inspiración {state.language === "en" ? "(English)" : "(Español)"}
            </label>
            <div className="space-y-4">
              {Object.entries(NICHE_LABELS)
                .filter(([niche]) => filteredBloggers.some((b) => b.niche === niche))
                .map(([niche, { label, emoji }]) => (
                  <div key={niche}>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                      {emoji} {label}
                    </h4>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {filteredBloggers
                        .filter((b) => b.niche === niche)
                        .map((blogger) => {
                          const isActive = state.selectedBloggerSlug === blogger.id;
                          return (
                            <button
                              key={blogger.id}
                              type="button"
                              aria-pressed={isActive}
                              onClick={() => dispatch({ type: 'SELECT_BLOGGER', payload: blogger.id })}
                              className={`rounded-xl border px-4 py-3 text-left transition-all ${
                                isActive
                                  ? "border-blue-500 bg-blue-50 ring-2 ring-blue-500 dark:border-blue-400 dark:bg-blue-950/40"
                                  : "border-zinc-300 bg-transparent hover:border-blue-300 dark:border-zinc-700 dark:hover:border-zinc-600"
                              }`}
                            >
                              <span className="flex items-center justify-between gap-2 font-semibold text-zinc-900 dark:text-zinc-100">
                                <span className="truncate">{blogger.name}</span>
                                <span className="shrink-0 rounded-full bg-zinc-100 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                                  {blogger.lang.toUpperCase()}
                                </span>
                              </span>
                            </button>
                          );
                        })}
                    </div>
                  </div>
                ))}
              {filteredBloggers.length === 0 && (
                <p className="text-sm italic text-zinc-500 dark:text-zinc-400">
                  No hay bloggers disponibles para este idioma.
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="custom-url" className="block text-sm font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              URL de Inspiración (Opcional)
            </label>
            <input
              id="custom-url"
              type="text"
              value={state.customUrl}
              onChange={(e) => dispatch({ type: 'SET_CUSTOM_URL', payload: e.target.value })}
              placeholder="Ej: https://miblog.com"
              className="w-full rounded-xl border border-zinc-300 bg-transparent px-4 py-3 outline-none transition-all focus:ring-2 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
            />
          </div>

          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full transform rounded-xl bg-blue-600 py-4 font-bold text-white transition-all hover:bg-blue-700 hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-blue-600"
          >
            GENERAR POST AUTÓNOMO
          </button>

          {state.error && (
            <div role="alert" className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-400">
              <strong>Error:</strong> {state.error}
            </div>
          )}
        </form>
      ) : (
        <div className="space-y-12 py-12">
          {/* Progress Section */}
          <div className="relative pt-1">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <span className="inline-block rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold uppercase text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                  Progreso de Generación
                </span>
              </div>
              <div className="text-right">
                <span className="inline-block text-xs font-semibold text-blue-600 dark:text-blue-400">
                  {Math.round(state.progress)}%
                </span>
              </div>
            </div>
            <div className="mb-4 flex h-3 overflow-hidden rounded-full bg-zinc-100 text-xs dark:bg-zinc-800">
              <div
                style={{ width: `${state.progress}%` }}
                className="flex flex-col justify-center whitespace-nowrap bg-blue-600 text-center text-white shadow-none transition-all duration-1000 ease-out dark:bg-blue-500"
              ></div>
            </div>
          </div>

          {/* Phases List */}
          <div className="grid gap-4">
            {PHASES.map((phase, index) => (
              <div
                key={phase.id}
                className={`flex items-center rounded-xl border p-4 transition-all duration-500 ${
                  index === state.currentPhase
                    ? "scale-[1.02] border-blue-300 bg-blue-50/80 shadow-md dark:border-blue-800 dark:bg-blue-950/40"
                    : index < state.currentPhase
                    ? "border-transparent bg-zinc-50 opacity-60 dark:bg-zinc-800/50"
                    : "border-zinc-200 bg-transparent opacity-40 dark:border-zinc-800"
                }`}
              >
                <span className="mr-4 text-2xl">{phase.icon}</span>
                <div className="flex-1">
                  <h3 className={`font-bold ${index === state.currentPhase ? "text-blue-600 dark:text-blue-400" : "text-zinc-900 dark:text-zinc-100"}`}>
                    {phase.label}
                  </h3>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {index === state.currentPhase ? "En proceso..." : index < state.currentPhase ? "Completado" : "Pendiente"}
                  </p>
                </div>
                {index === state.currentPhase && (
                  <div className="size-2 rounded-full bg-blue-600 animate-ping dark:bg-blue-400"></div>
                )}
                {index < state.currentPhase && (
                  <span className="text-xl text-green-500 dark:text-green-400">✓</span>
                )}
              </div>
            ))}
          </div>

          <p className="animate-pulse text-center italic text-zinc-500 dark:text-zinc-400">
            Por favor, no cierres esta ventana. El proceso toma unos 2-3 minutos.
          </p>

          {infoMessage && (
            <div role="status" className="rounded-xl border border-blue-100 bg-blue-50 p-4 text-center text-sm text-blue-700 dark:border-blue-900/50 dark:bg-blue-950/40 dark:text-blue-300">
              {infoMessage}
            </div>
          )}
        </div>
      )}
    </main>
  );
}