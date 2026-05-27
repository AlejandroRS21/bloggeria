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
    <main className="max-w-4xl mx-auto px-6 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-semibold tracking-tight mb-4">Crear Nuevo Post</h1>
        <p className="text-secondary text-lg">
          Configura el tema y la fuente de inspiración para que la IA haga su magia.
        </p>
      </div>

      {!state.isGenerating ? (
        <form onSubmit={handleSubmit} className="space-y-8 bg-white dark:bg-zinc-900 p-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="space-y-2">
            <label htmlFor="topic" className="block text-sm font-semibold uppercase tracking-wider text-zinc-700">
              Tema del Post
            </label>
            <input
              id="topic"
              type="text"
              required
              value={state.topic}
              onChange={(e) => dispatch({ type: 'SET_TOPIC', payload: e.target.value })}
              placeholder="Ej: El futuro de la IA en el desarrollo web"
              className="w-full px-4 py-3 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-transparent focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
            <p className="text-xs text-secondary italic">El moderador con IA validará que el tema sea profesional.</p>
          </div>

          <div className="space-y-2">
            <label htmlFor="urls" className="block text-sm font-semibold uppercase tracking-wider text-zinc-700">
              URLs de Inspiración (Separadas por coma)
            </label>
            <input
              id="urls"
              type="text"
              required
              value={state.urls}
              onChange={(e) => dispatch({ type: 'SET_URLS', payload: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-transparent focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-primary text-background font-bold py-4 rounded-xl hover:opacity-90 transition-opacity active:scale-[0.98] transform"
          >
            GENERAR POST AUTÓNOMO
          </button>
          
          {state.error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl border border-red-100 dark:border-red-800 text-sm">
              <strong>Error:</strong> {state.error}
            </div>
          )}
        </form>
      ) : (
        <div className="space-y-12 py-12">
          {/* Progress Section */}
          <div className="relative pt-1">
            <div className="flex mb-4 items-center justify-between">
              <div>
                <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-accent bg-accent/10">
                  Progreso de Generación
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold inline-block text-blue-600">
                  {Math.round(state.progress)}%
                </span>
              </div>
            </div>
            <div className="overflow-hidden h-3 mb-4 text-xs flex rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div
                style={{ width: `${state.progress}%` }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-600 transition-all duration-1000 ease-out"
              ></div>
            </div>
          </div>

          {/* Phases List */}
          <div className="grid gap-4">
            {PHASES.map((phase, index) => (
              <div 
                key={phase.id}
                className={`flex items-center p-4 rounded-xl border transition-all duration-500 ${
                  index === state.currentPhase 
                    ? "bg-blue-50/50 border-blue-200 scale-[1.02] shadow-md" 
                    : index < state.currentPhase 
                    ? "bg-zinc-50 dark:bg-zinc-800/50 border-transparent opacity-60" 
                    : "bg-transparent border-zinc-200 dark:border-zinc-800 opacity-40"
                }`}
              >
                <span className="text-2xl mr-4">{phase.icon}</span>
                <div className="flex-1">
                  <h3 className={`font-bold ${index === state.currentPhase ? "text-blue-600" : "text-zinc-900"}`}>
                    {phase.label}
                  </h3>
                  <p className="text-xs text-zinc-500">
                    {index === state.currentPhase ? "En proceso..." : index < state.currentPhase ? "Completado" : "Pendiente"}
                  </p>
                </div>
                {index === state.currentPhase && (
                  <div className="size-2 bg-blue-600 rounded-full animate-ping"></div>
                )}
                {index < state.currentPhase && (
                  <span className="text-green-500 text-xl">✓</span>
                )}
              </div>
            ))}
          </div>

          <p className="text-center text-secondary italic animate-pulse">
            Por favor, no cierres esta ventana. El proceso toma unos 2-3 minutos.
          </p>
        </div>
      )}
    </main>
  );
}
