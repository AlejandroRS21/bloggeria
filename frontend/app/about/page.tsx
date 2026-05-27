import Link from "next/link";

export const metadata = {
  title: "Sobre el proyecto",
};

const timeline = [
  {
    year: "2024",
    title: "Investigación Académica",
    desc: "Estudio de metodologías de Procesamiento del Lenguaje Natural (NLP), análisis estilométrico tradicional y mimetización lingüística basada en Large Language Models (LLMs). Se selecciona el proyecto Aphra como base conceptual.",
  },
  {
    year: "2025",
    title: "Diseño y Construcción Multiagente",
    desc: "Definición de la topología del pipeline de 8 agentes de IA independientes. Desarrollo e implementación de la lógica asíncrona de orquestación, gestión de estados y reintentos del backend en Python.",
  },
  {
    year: "2026",
    title: "Despliegue y Validación E2E",
    desc: "Integración de la persistencia relacional con Supabase, despliegue serverless de contenedores en Modal y desarrollo del frontend dinámico en Next.js. Ejecución del banco de pruebas estilísticas y evaluación cualitativa.",
  },
];

export default function AboutPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-gray-200 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-block rounded-full bg-blue-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-blue-700">
              Sobre el proyecto académico
            </span>
            <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl">
              Generación de Contenido por{" "}
              <span className="text-blue-600">Sistemas Multiagente</span>
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-gray-600 sm:text-xl">
              Este blog dinámico presenta los resultados reales de un proyecto académico enfocado en la mimetización estilística y generación adaptativa mediante inteligencia artificial.
            </p>
          </div>
        </div>
      </section>

      {/* Qué es */}
      <section className="border-b border-gray-200 bg-white py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">
              Contexto Académico y Motivación
            </h2>
            <p className="mt-6 text-base leading-relaxed text-gray-600">
              <strong>Blogger Agent</strong> es un proyecto académico de investigación aplicada que explora los límites de la mimetización del estilo de escritura humana utilizando modelos de lenguaje open-source y pipelines estructurados de agentes.
            </p>
            <p className="mt-4 text-base leading-relaxed text-gray-600">
              El desarrollo de este sistema está fuertemente inspirado en la arquitectura conceptual de{" "}
              <a
                href="https://github.com/DavidLMS/aphra"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-blue-600 underline decoration-blue-200 underline-offset-2 hover:text-blue-800"
              >
                Aphra
              </a>
              , un framework pionero en la coordinación de agentes para la generación estilística de textos. Basándose en dicha inspiración, este proyecto amplía y formaliza el pipeline para adaptarlo al formato de artículos web e implementa una infraestructura serverless real y escalable.
            </p>
            <p className="mt-4 text-base leading-relaxed text-gray-600">
              La meta principal es responder a una pregunta académica clave: <em>¿Puede una red descentralizada de agentes lingüísticos especializados imitar el registro, el dialecto y la estructura de un bloguero profesional hasta el punto de generar artículos coherentes y listos para publicar?</em>
            </p>
          </div>
        </div>
      </section>

      {/* Cronología */}
      <section className="border-b border-gray-200 bg-gray-50 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 text-center">
              Desarrollo del Proyecto Académico
            </h2>

            <div className="relative mt-12">
              {/* Vertical line */}
              <div className="absolute left-4 top-0 h-full w-0.5 bg-gradient-to-b from-blue-200 via-indigo-200 to-purple-200" />

              {timeline.map((item, i) => (
                <div key={item.year} className="relative ml-12 pb-12 last:pb-0">
                  {/* Dot */}
                  <div className="absolute -left-[3.25rem] mt-1 flex h-6 w-6 items-center justify-center rounded-full border-4 border-white bg-blue-500 shadow">
                    <span className="text-[10px] font-bold text-white">
                      {i + 1}
                    </span>
                  </div>
                  <div>
                    <span className="inline-block rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                      {item.year}
                    </span>
                    <h3 className="mt-2 text-xl font-bold text-gray-900">
                      {item.title}
                    </h3>
                    <p className="mt-2 text-base leading-relaxed text-gray-600">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Resumen del Stack */}
      <section className="border-b border-gray-200 bg-white py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 text-center">
              Resumen Tecnológico del Sistema
            </h2>
            <p className="mt-4 text-gray-600 text-center">
              El sistema se compone de tres bloques fundamentales que garantizan un flujo de datos asíncrono y desacoplado.
            </p>
            <div className="mt-10 grid gap-6 sm:grid-cols-3">
              {[
                {
                  label: "Frontend & UI",
                  desc: "Desarrollado en Next.js 16 con React 19 y Tailwind CSS, ofreciendo un blog ágil que consulta datos de Supabase de manera dinámica.",
                },
                {
                  label: "Orquestación Serverless",
                  desc: "Módulo en Python alojado en la plataforma serverless de Modal que orquesta y ejecuta de forma aislada el pipeline multiagente.",
                },
                {
                  label: "Base de Datos",
                  desc: "Persistencia relacional mediante Supabase PostgreSQL, que almacena en campos JSONB estructurados el contenido, tags y metadatos SEO.",
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-gray-200 bg-gray-50 p-6"
                >
                  <h3 className="font-bold text-gray-900 text-lg">{item.label}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-gray-600">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Autor */}
      <section className="border-b border-gray-200 bg-gray-50 py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900">
              Sobre el Autor
            </h2>
            <p className="mt-6 text-base leading-relaxed text-gray-600">
              Este proyecto ha sido diseñado e implementado en su totalidad por <strong>Alejandro Ramírez Salado</strong> como un proyecto académico en Big Data e Inteligencia Artificial.
            </p>
            <p className="mt-4 text-base leading-relaxed text-gray-600">
              Si quieres conocer más sobre el desarrollo, reportar errores o contribuir a la mejora de la arquitectura de agentes, puedes visitar el repositorio del proyecto en GitHub.
            </p>
            <div className="mt-8 flex justify-center">
              <a
                href="https://github.com/AlejandroRS21/blogger-agent-tfg"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2.5 rounded-lg bg-gray-900 px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-gray-800"
              >
                <svg className="h-5 w-5 fill-current" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482C19.138 20.193 22 16.44 22 12.017 22 6.484 17.522 2 12 2z" />
                </svg>
                Ver Repositorio en GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-white py-20 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 text-center sm:px-6">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            ¿Quieres probar el orquestador?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-gray-600">
            Define una temática de tu interés e introduce un blog de referencia de WordPress. Observa el funcionamiento del pipeline.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link
              href="/posts/new"
              className="rounded-lg bg-blue-600 px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
            >
              Generar Post
            </Link>
            <Link
              href="/project"
              className="rounded-lg border border-gray-300 bg-white px-8 py-3.5 text-sm font-semibold text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
            >
              Ver arquitectura técnica
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
