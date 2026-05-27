# 🚀 Blogger Agent TFG — Estado del Proyecto

> Última actualización: mayo 2026

---

## 📋 Resumen

Sistema multiagente funcional con backend en Python expuesto como servicio serverless en Modal, base de datos relacional y persistencia en Supabase, y frontend interactivo desarrollado en Next.js 16 con React 19, desplegado en Vercel.

### Cambios Recientes

- **Reconstrucción Completa de la Interfaz Web (Mayo 2026)**: Se ha desarrollado un nuevo frontend robusto utilizando Next.js 16, React 19 y Tailwind CSS 4, reemplazando la versión previa por una aplicación moderna y de alto rendimiento.
- **Persistencia en Supabase**: Integración del cliente Supabase en el frontend para realizar consultas dinámicas sin caché y del cliente de base de datos en el backend de Modal para la inserción automática tras la generación.
- **Orquestador Serverless en Modal**: Habilitado el orquestador en un webhook serverless, con soporte de secretos para la comunicación con Supabase y proveedores de LLM.
- **Daggr Integrado**: Mantenimiento del canvas visual e interactivo basado en Gradio para el desarrollo y depuración del flujo de agentes.

---

## 🏗️ Arquitectura de Producción

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BLOGGER AGENT TFG                               │
│                                                                        │
│  ┌───────────────────────┐            ┌─────────────────────────────┐  │
│  │  FRONTEND (Next.js 16)│  Webhook   │  BACKEND (Python / Modal)   │  │
│  │  Vercel               ├───────────►│  Serverless API             │  │
│  ├───────────────────────┤            ├─────────────────────────────┤  │
│  │  • Interfaz React 19  │◄───────────┤  • 8 Agentes IA (Orquestador)│  │
│  │  • Tailwind CSS 4     │  Slug      │  • Modelos HuggingFace/Gemini│  │
│  │  • Consultas dinámicas│            │  • Soporte de GPU (A10G)    │  │
│  └───────────┬───────────┘            └──────────────┬──────────────┘  │
│              │                                       │                 │
│    Lectura   │                                       │ Escritura       │
│    de posts  │                                       │ de posts        │
│              ▼                                       ▼                 │
│        ┌───────────────────────────────────────────────────┐           │
│        │               BASE DE DATOS (Supabase)            │           │
│        │               Tabla relacional "posts"            │           │
│        └───────────────────────────────────────────────────┘           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Estructura de Archivos del Proyecto

```
backend/
├── aphra_blogger/
│   ├── agents/                 # 8 agentes
│   │   ├── style_analyzer.py
│   │   ├── keyword_extractor.py
│   │   ├── content_generator.py
│   │   ├── critic.py
│   │   ├── image_selector.py
│   │   ├── html_builder.py
│   │   ├── anonymous_blogger.py
│   │   └── style_extractor.py
│   ├── llm/                    # 4 providers: HF, OpenAI, Gemini, Modal
│   ├── workflows/
│   └── config/
├── src/orchestrator/           # 7 fases
│   ├── main.py
│   ├── config.py
│   ├── state.py
│   └── runner.py
├── tests/                      # ~80 tests
├── tools/scraper.py
├── daggr_blogger_workflow.py   # ⭐ Workflow visual (Daggr/Gradio)
├── modal_app.py                # Deployment de Webhook en Modal
├── llm_modal_host.py           # Hosting LLM GPU
├── generate_and_deploy.py      # Script legacy de prueba local
└── outputs/                    # Posts de prueba locales (JSON)

frontend/                       # Aplicación Next.js 16 (Vercel)
├── app/
│   ├── page.tsx                # Listado de artículos dinámico
│   ├── posts/[slug]/page.tsx   # Lectura de artículo individual
│   └── posts/new/page.tsx      # Generación autónoma interactiva
├── lib/
│   ├── supabase.ts             # Cliente de conexión de Supabase
│   └── api.ts                  # Métodos de consulta de base de datos
├── components/                 # Componentes visuales React
└── package.json

docs/                           # (Obsoleto) Web estática anterior
project_docs/                   # Documentación de diseño y arquitectura
```

---

## 📊 Métricas

### Backend
- **Agentes**: 8 (StyleAnalyzer, KeywordExtractor, ContentGenerator, Critic, ImageSelector, HTMLBuilder, AnonymousBloggerEmulator, StyleExtractor)
- **Proveedores LLM**: 4 (HuggingFace, OpenAI, Gemini, Modal GPU)
- **Tests**: ~80
- **Fases del orquestador**: 7

### Frontend y Base de Datos
- Next.js 16 (App Router) + React 19 + Tailwind CSS 4
- Base de datos relacional PostgreSQL en Supabase

### Estado Global del Proyecto
- **Progreso**: ~95% completo
- **Pendiente**: Automatización de pruebas y CI/CD

---

## 🎯 Próximos Pasos

### Alta Prioridad
- [ ] **CI/CD**: Configuración de GitHub Actions para el testeo automático del código de agentes.
- [ ] **Tests de Integración E2E**: Implementar Playwright para verificar de extremo a extremo la interfaz Next.js y su llamada a la API de Modal.
- [ ] **Robusteza del Moderador**: Incrementar las reglas semánticas y de seguridad del filtro de contenido de temas en la API de Modal.

### Media Prioridad
- [ ] **Sistema de Colas**: Gestión de múltiples peticiones en paralelo en Modal para evitar colisiones por concurrencia.
- [ ] **Módulo de Autenticación**: Añadir inicio de sesión de administrador en el frontend para gestionar/moderar posts directamente desde la UI.

---

## 📖 Documentación

1. [README.md](../README.md) — Visión general ✅
2. [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) — Guía de publicación moderna ✅
3. [AGENTS_GUIDE.md](AGENTS_GUIDE.md) — Guía para agentes IA ✅
4. [ORCHESTRATION_PLAN.md](../project_docs/ORCHESTRATION_PLAN.md)
5. [HUGGINGFACE_MIGRATION.md](../project_docs/HUGGINGFACE_MIGRATION.md)
6. [MODAL_DEPLOYMENT.md](../project_docs/MODAL_DEPLOYMENT.md)
7. [HTMLBUILDER_INTEGRATION.md](../project_docs/HTMLBUILDER_INTEGRATION.md)

---

## ✅ Checklist Final

- [x] Backend: 8 agentes funcionales integrados
- [x] Backend: Orquestador en 7 fases con gestión de fallos
- [x] Backend: Cobertura de tests (~80 unitarios y de integración)
- [x] Backend: Daggr como visualizador interactivo
- [x] Cloud: Modal webhook serverless desplegado
- [x] Base de datos: Persistencia y mapeo automatizado en Supabase
- [x] Frontend: Aplicación Next.js 16 con React 19 y Tailwind CSS 4
- [x] Frontend: Conectado a Vercel con consultas en tiempo real (sin caché)
- [x] Documentación: Manuales actualizados con el nuevo stack
- [ ] CI/CD: Automatización de tests
- [ ] Tests E2E: Integración frontend-backend

**Estado Global:** 🟢 Funcional y preparado para producción
