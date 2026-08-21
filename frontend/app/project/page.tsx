"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n";

const steps = [
  {
    number: "01",
    title: "Ingreso de Referencias",
    desc: "El usuario introduce el tema deseado y la URL del blog de referencia (ej: un blog de WordPress como javipas.com).",
    color: "bg-blue-600",
  },
  {
    number: "02",
    title: "Análisis Estilístico",
    desc: "El Scraper extrae el corpus de artículos. El Style Analyzer analiza el ADN lingüístico (sintaxis, dialecto, vocabulario y tono).",
    color: "bg-indigo-600",
  },
  {
    number: "03",
    title: "Generación y Crítica",
    desc: "El Writer genera un borrador adaptando el estilo. El Critic evalúa la calidad y solicita refinamientos si la nota es menor de 7/10.",
    color: "bg-violet-600",
  },
  {
    number: "04",
    title: "Optimización y Carga",
    desc: "El SEO Agent ajusta metadatos y el Image Selector asocia imágenes de Unsplash. El post se inserta directamente en Supabase.",
    color: "bg-purple-600",
  },
];

const agentsList = [
  {
    title: "Scraper Agent",
    desc: "Extrae de forma automatizada las publicaciones históricas del blog objetivo mediante técnicas de web scraping asíncrono y evasión de bloqueos antibot, conformando el corpus de entrenamiento estilístico.",
    icon: "🕷️",
  },
  {
    title: "Style Analyzer Agent",
    desc: "Evalúa sintácticamente el corpus para determinar la distribución de longitudes de frases, tipo de registro (formal/informal), dialecto regional (peninsular/rioplatense), uso de recursos retóricos y puntuación.",
    icon: "🧠",
  },
  {
    title: "Keyword Extractor Agent",
    desc: "Extrae semánticamente las palabras clave, entidades nombradas y temas recurrentes que definen el nicho temático del autor a partir del análisis del corpus.",
    icon: "🏷️",
  },
  {
    title: "Writer / Generator Agent",
    desc: "Redacta el borrador del artículo mimetizando el estilo analizado y aplicando directivas estrictas de dialecto, evitando spanglish, eliminando citas numéricas e incorporando negritas estratégicas.",
    icon: "✍️",
  },
  {
    title: "Critic Agent",
    desc: "Evalúa objetivamente el borrador frente a una rúbrica de calidad de escritura, legibilidad, estructura y correspondencia con el autor. Devuelve una puntuación e informe de mejoras para la fase de refinamiento.",
    icon: "🔍",
  },
  {
    title: "SEO Agent",
    desc: "Optimiza la estructura del artículo y sus etiquetas de encabezados (H1-H3), refina el título para que sea un gancho atractivo y genera los metadatos necesarios (meta-description, palabras clave).",
    icon: "📈",
  },
  {
    title: "Image Selector Agent",
    desc: "Genera descripciones semánticas (prompts) de recursos visuales idóneos para el artículo y busca recursos fotográficos reales a través de la API oficial de Unsplash.",
    icon: "🖼️",
  },
  {
    title: "HTML / JSX Builder Agent",
    desc: "Estandariza el contenido final convirtiéndolo de Markdown a código HTML semántico, estima el tiempo de lectura, calcula el recuento de palabras y añade un índice interactivo de secciones.",
    icon: "🛠️",
  },
];

export default function ProjectPage() {
  const { t } = useI18n();
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-gray-200 bg-gradient-to-b from-white to-gray-50 dark:border-zinc-800 dark:from-zinc-950 dark:to-zinc-900/60">
        <div className="mx-auto max-w-6xl px-4 pt-32 pb-20 sm:px-6 sm:pt-40 sm:pb-28 lg:pt-48 lg:pb-32">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-block rounded-full bg-blue-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-blue-700 dark:bg-blue-950/80 dark:text-blue-300">
              {t("project.badge")}
            </span>
            <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl dark:text-zinc-100">
              {t("project.heroTitle")}
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-gray-600 sm:text-xl dark:text-zinc-400">
              {t("project.heroSubtitle")}
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link
                href="/posts/new"
                className="rounded-lg bg-blue-600 px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
              >
                {t("project.generate")}
              </Link>
              <a
                href="https://github.com/AlejandroRS21/bloggeria"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-gray-300 bg-white px-8 py-3.5 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                {t("project.github")}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Flujo general de ejecución */}
      <section className="border-b border-gray-200 bg-white py-20 sm:py-28 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
              {t("project.pipelineTitle")}
            </h2>
            <p className="mt-4 text-gray-600 dark:text-zinc-400">
              {t("project.pipelineDesc")}
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {steps.map((step) => (
              <div key={step.number} className="relative">
                <div className="flex items-start gap-4 p-6 bg-gray-50/60 rounded-2xl border border-gray-100 hover:bg-gray-50 transition-all duration-300 lg:flex-col lg:items-center lg:text-center dark:border-zinc-800 dark:bg-zinc-900/60 dark:hover:bg-zinc-900">
                  <div
                    className={`flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full text-lg font-bold text-white shadow-md ${step.color}`}
                  >
                    {step.number}
                  </div>
                  <div className="min-w-0 lg:mt-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-zinc-100">
                      {step.title}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
                      {step.desc}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pipeline de Agentes */}
      <section className="border-b border-gray-200 bg-gray-50 py-20 sm:py-28 dark:border-zinc-800 dark:bg-zinc-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-zinc-100">
              {t("project.agentsTitle")}
            </h2>
            <p className="mt-4 text-gray-600 dark:text-zinc-400">
              {t("project.agentsDesc")}
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {agentsList.map((agent) => (
              <div
                key={agent.title}
                className="flex flex-col rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="text-3xl">{agent.icon}</div>
                <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-zinc-100">{agent.title}</h3>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
                  {agent.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Detalles del Stack e Infraestructura */}
      <section className="border-b border-gray-200 bg-white py-20 sm:py-28 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="text-center text-3xl font-bold tracking-tight text-gray-900 dark:text-zinc-100">
              Infraestructura y Stack Tecnológico Real
            </h2>
            <p className="mt-4 text-center text-gray-600 dark:text-zinc-400">
              Diseñado con arquitectura serverless moderna para garantizar un rendimiento óptimo y una separación limpia de responsabilidades.
            </p>

            <div className="mt-12 space-y-8">
              <div className="flex gap-4">
                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-blue-50 text-2xl text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
                  ▲
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-zinc-100">Next.js 16 & Vercel (Capa de Presentación)</h3>
                  <p className="mt-2 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
                    El frontend está desarrollado bajo Next.js 16, aprovechando las ventajas de React 19 (Server Components, enrutamiento dinámico optimizado y renderizado asíncrono). Se aloja en <strong>Vercel</strong> para descargas de página instantáneas y escalado global automatizado.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-green-50 text-2xl text-green-600 dark:bg-green-950/60 dark:text-green-400">
                  ☁️
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-zinc-100">Modal Serverless (Motor de Ejecución de IA)</h3>
                  <p className="mt-2 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
                    El backend multiagente se ejecuta en <strong>Modal</strong> en formato serverless. Al invocar un webhook seguro, Modal levanta contenedores Python aislados bajo demanda, orquestando el flujo de agentes de forma asíncrona. Los modelos LLM de producción (como Qwen 2.5 u otros de HuggingFace/Gemini) se integran directamente para tareas intensivas de análisis de texto y generación formal.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-2xl text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
                  ⚡
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-zinc-100">Supabase (Persistencia Relacional)</h3>
                  <p className="mt-2 text-base leading-relaxed text-gray-600 dark:text-zinc-400">
                    Para la base de datos se emplea <strong>Supabase (PostgreSQL)</strong>. El backend en Modal realiza un `upsert` seguro directamente sobre la tabla `posts` una vez finalizado el pipeline de agentes. Los artículos se almacenan estructurados con sus metadatos de estilo, tags, imágenes de portada e índice interactivo en campos JSONB. El frontend en Next.js consulta la base de datos en tiempo real mediante el cliente de Supabase.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="bg-gray-50 py-20 sm:py-28 dark:bg-zinc-900/40">
        <div className="mx-auto max-w-6xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl dark:text-zinc-100">
          {t("project.ctaTitle")}
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-gray-600 dark:text-zinc-400">
            {t("project.ctaDesc")}
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/posts/new"
              className="rounded-lg bg-blue-600 px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
            >
              {t("project.ctaButton")}
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
