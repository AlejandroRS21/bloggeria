"use client";

import { useReducer, useEffect } from "react";
import { useRouter } from "next/navigation";

const PHASES = [
  { id: "safety", label: "Protección de Contenido", icon: "🛡️", duration: 5000 },
  { id: "style", label: "Análisis de Estilo", icon: "🕵️", duration: 8000 },
  { id: "keywords", label: "Extracción de Keywords", icon: "🔑", duration: 4000 },
  { id: "generation", label: "Generación de Contenido", icon: "📝", duration: 25000 },
  { id: "critique", label: "Refinamiento y Crítica", icon: "🧐", duration: 15000 },
  { id: "images", label: "Selección de Imágenes", icon: "🖼️", duration: 7000 },
  { id: "publishing", label: "Guardando en Base de Datos", icon: "🚀", duration: 6000 },
];

type State = {
  topic: string;
  urls: string;
  isGenerating: boolean;
  currentPhase: number;
  progress: number;
  error: string | null;
};

type Action = 
  | { type: 'SET_TOPIC'; payload: string }
  | { type: 'SET_URLS'; payload: string }
  | { type: 'START_GENERATION' }
  | { type: 'NEXT_PHASE' }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'RESET' };

const initialState: State = {
  topic: "",
  urls: "https://javipas.com",
  isGenerating: false,
  currentPhase: 0,
  progress: 0,
  error: null,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_TOPIC':
      return { ...state, topic: action.payload };
    case 'SET_URLS':
      return { ...state, urls: action.payload };
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
  const { push, refresh } = useRouter();

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

    // Patrones de contenido explícito/denigrante (primera línea de defensa)
    // La protección real está en el backend con Gemini
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Client-side moderation first
    const moderationError = isTopicAppropriate(state.topic);
    if (moderationError) {
      dispatch({ type: 'SET_ERROR', payload: moderationError });
      return;
    }

    dispatch({ type: 'START_GENERATION' });

    try {
      const webhookUrl = process.env.NEXT_PUBLIC_MODAL_WEBHOOK_URL || "https://alejandrors21--blogger-agent-tfg-webhook.modal.run";
      
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: state.topic,
          blogger_urls: state.urls.split(",").map(u => u.trim()),
          provider: "gemini"
        }),
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || "Error desconocido en la generación");
      }

      // If successful, wait a bit for the last phase animation and redirect
      setTimeout(() => {
        push("/");
        refresh();
      }, 2000);

    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    }
  };

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
              Tema del Post
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
            <label htmlFor="urls" className="block text-sm font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
              URLs de Inspiración (Separadas por coma)
            </label>
            <input
              id="urls"
              type="text"
              required
              value={state.urls}
              onChange={(e) => dispatch({ type: 'SET_URLS', payload: e.target.value })}
              className="w-full rounded-xl border border-zinc-300 bg-transparent px-4 py-3 outline-none transition-all focus:ring-2 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
            />
          </div>

          <button
            type="submit"
            className="w-full transform rounded-xl bg-blue-600 py-4 font-bold text-white transition-all hover:bg-blue-700 hover:opacity-90 active:scale-[0.98]"
          >
            GENERAR POST AUTÓNOMO
          </button>
          
          {state.error && (
            <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-400">
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
        </div>
      )}
    </main>
  );
}
