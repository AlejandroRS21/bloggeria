# Próximos Pasos - Blogger Agent TFG

> Guía de implementación por fases con tareas pendientes

## ✅ Completado

### Fase 0: Setup Inicial ✅
- [x] Estructura base del proyecto
- [x] `BloggerStyleWorkflow` con placeholders
- [x] Configuración TOML
- [x] Tests básicos
- [x] **Documentación Vercel** (deployment pendiente)

### Fase 1: Orquestador (Issue #9) ✅
- [x] Estructura `src/orchestrator/`
- [x] `BloggerOrchestrator` clase principal
- [x] `StateManager` para tracking de fases
- [x] `OrchestratorConfig` con validación
- [x] CLI ejecutable (`runner.py`)
- [x] Sistema de reintentos con backoff exponencial
- [x] Tests unitarios completos
- [x] Documentación del orquestador

**Estado:** ✅ COMPLETADO - Sistema funcional

### Fase 2: Agentes de Análisis (Issue #6) ✅

#### Agente 1: StyleAnalyzer 🎭 ✅
**Archivo:** `backend/aphra_blogger/agents/style_analyzer.py`

Completado:
- [x] Crear clase `StyleAnalyzer`
- [x] Implementar análisis de tono (conversacional, formal, etc.)
- [x] Extraer voz narrativa (primera/tercera persona)
- [x] Detectar estructura común (intro-desarrollo-conclusión)
- [x] Identificar expresiones características
- [x] Calcular métricas (longitud promedio de frases, párrafos)
- [x] Integración con OpenAI GPT-4
- [x] Fallback sin API key
- [x] Tests unitarios

#### Agente 2: KeywordExtractor 🔑 ✅
**Archivo:** `backend/aphra_blogger/agents/keyword_extractor.py`

Completado:
- [x] Crear clase `KeywordExtractor`
- [x] Extracción de keywords principales (20-30)
- [x] Identificar expresiones frecuentes (10-15)
- [x] Detectar términos técnicos
- [x] Categorización de temas (5-10)
- [x] Integración con OpenAI GPT-3.5-turbo
- [x] Fallback sin API key
- [x] Tests unitarios

**Estado:** ✅ COMPLETADO

### Fase 3: Agentes de Generación (Issue #7) ✅

#### Agente 1: ContentGenerator 📝 ✅
**Archivo:** `backend/aphra_blogger/agents/content_generator.py`

Completado:
- [x] Crear clase `ContentGenerator`
- [x] Método `generate_draft()` - Borrador inicial
- [x] Método `refine_content()` - Refinamiento basado en crítica
- [x] Control de longitud (min_words, max_words)
- [x] Aplicación de style_profile y keywords
- [x] Integración con OpenAI GPT-4
- [x] Fallback template-based
- [x] Tests unitarios

#### Agente 2: CriticAgent 🔍 ✅
**Archivo:** `backend/aphra_blogger/agents/critic.py`

Completado:
- [x] Crear clase `CriticAgent`
- [x] Scoring de coherencia (0-10)
- [x] Scoring de match de estilo (0-10)
- [x] Scoring de engagement (0-10)
- [x] Scoring de autenticidad (0-10)
- [x] Generación de sugerencias (3-5 items)
- [x] Determinación de `needs_revision` (score < 7)
- [x] Integración con OpenAI GPT-4-turbo
- [x] Fallback heurístico
- [x] Tests unitarios

#### Agente 3: ImageSelectorAgent 🖼️ ✅
**Archivo:** `backend/aphra_blogger/agents/image_selector.py`

Completado:
- [x] Crear clase `ImageSelectorAgent`
- [x] Selección estratégica de posiciones (header, sections)
- [x] Generación de prompts para AI image tools
- [x] Generación de alt text accesible
- [x] Context awareness (por qué cada imagen)
- [x] Integración con OpenAI GPT-3.5-turbo
- [x] Fallback posicional
- [x] Tests unitarios

**Estado:** ✅ COMPLETADO

### Integración Completa ✅
- [x] Todos los agentes integrados en `src/orchestrator/main.py`
- [x] Pipeline completo de 7 fases funcional
- [x] Tests de integración (test_full_pipeline_fallback)
- [x] Documentación completa en `aphra_blogger/agents/README.md`
- [x] READMEs actualizados (backend y raíz)

### Infraestructura y Tooling ✅

#### Migración a UV Package Manager ✅
**Completado:**
- [x] Crear `backend/pyproject.toml` con configuración PEP 621
- [x] Setup script para Windows (`backend/setup.ps1`)
- [x] Setup script para Unix (`backend/setup.sh`)
- [x] Actualizar `backend/requirements.txt` (Markdown, no python-markdown)
- [x] Actualizar documentación (README.md, backend/README.md)
- [x] Configuración de herramientas (black, ruff, pytest)
- [x] Tests verificados: 7/7 pasando con UV

**Resultado:** Entorno con UV funcional (10-100x más rápido que pip)

#### Modal Deployment Infrastructure ✅
**Completado:**
- [x] Crear `backend/modal_app.py` con webhook endpoint
- [x] Documentación completa `project_docs/MODAL_DEPLOYMENT.md`
- [x] Documentar objetivo de migración a HuggingFace models
- [x] Función `generate_blog_post()` con timeout 10min
- [x] Helper `scrape_blogger_corpus()`
- [x] Testing local con mock API key

**Pendiente:** Deploy real a Modal cloud (código listo)

---

## 🔄 En Progreso

Ninguna tarea en progreso actualmente.

---

## 📋 Pendiente

### Fase 2 (Continuación): Agentes Adicionales (Opcionales)

#### Agente: ThematicAnalyzer 📚 (Opcional)
**Archivo:** `backend/aphra_blogger/agents/thematic_analyzer.py`

Tareas:
- [ ] Crear clase `ThematicAnalyzer`
- [ ] Scraping de posts del blog
- [ ] Extracción de temáticas con NLP
- [ ] Clustering de temas relacionados
- [ ] Frecuencia de temáticas
- [ ] Tests unitarios

**Nota:** Este agente es opcional ya que KeywordExtractor ya extrae temas principales.

#### Agente: StructureAnalyzer 📐 (Opcional)
**Archivo:** `backend/aphra_blogger/agents/structure_analyzer.py`

Tareas:
- [ ] Crear clase `StructureAnalyzer`
- [ ] Analizar longitud promedio de posts
- [ ] Detectar patrones de secciones
- [ ] Analizar uso de imágenes
- [ ] Estructura de párrafos
- [ ] Tests unitarios

**Nota:** Este agente es opcional ya que StyleAnalyzer ya analiza estructura básica.

### Issue #2: Research - Corpus de Javi Pas ✅

**Prioridad:** ✅ COMPLETADO  
**Tiempo estimado:** 1 día (completado)

Completado:
- [x] Implementar scraper para blogs WordPress
- [x] Manejo de paginación (configurable)
- [x] Extracción de contenido limpio (sin ads, scripts, estilos)
- [x] Guardado de corpus local en JSON estructurado
- [x] Rate limiting para no sobrecargar (configurable delay)
- [x] Extracción de metadata (autor, fecha, tags, categorías)
- [x] Tests completos del scraper
- [x] Documentación detallada (tools/README.md)
- [x] Función de conveniencia `scrape_javipas()`
- [x] CLI ejecutable directo

**Archivo:** `backend/tools/scraper.py` ✅

**Uso:**
```bash
# Scraping directo
python -m tools.scraper

# O desde código
from tools.scraper import scrape_javipas
posts = scrape_javipas(max_posts=30, output_file="corpus.json")
```

---

### Issue #3: Agente HTMLBuilder ✅

**Prioridad:** MEDIA  
**Tiempo estimado:** 2 días (completado)
**Estado:** ✅ COMPLETADO

#### Agente: HTMLBuilder 🏗️
**Archivo:** `backend/aphra_blogger/agents/html_builder.py`

Completado:
- [x] Crear clase `HTMLBuilder`
- [x] Convertir Markdown a HTML/JSX
- [x] Aplicar estructura semántica
- [x] Insertar placeholders de imágenes
- [x] Meta tags (title, description, keywords)
- [x] Tests unitarios (20+ tests)
- [x] Integración con orquestador (Fase 6 del pipeline)
- [x] Generación de componentes Next.js completos
- [x] Tabla de contenidos (TOC) desde headings
- [x] Cálculo de tiempo de lectura y conteo de palabras
- [x] Generación automática de slug

**Documentación:** `project_docs/HTMLBUILDER_INTEGRATION.md`

---

### Fase 4: Deployment Backend (Issue #5)

**Prioridad:** ALTA ⭐  
**Tiempo estimado:** 1-2 días  
**Estado:** 🔧 INFRAESTRUCTURA COMPLETA - Deploy pendiente

**Completado:**
- [x] Crear `modal_app.py` con webhook endpoint
- [x] Documentar proceso completo en `MODAL_DEPLOYMENT.md`
- [x] Configurar función con timeout y memoria adecuados
- [x] Documentar objetivo de migración a HuggingFace models

**Pendiente:**
- [ ] Crear cuenta Modal
- [ ] Configurar secrets (API keys) en Modal dashboard
- [ ] Ejecutar `modal deploy backend/modal_app.py`
- [ ] Probar webhook endpoint con requests reales
- [ ] Actualizar URL del webhook en documentación

**📝 NOTA IMPORTANTE - Modelos HuggingFace:**
> **OBJETIVO FUTURO:** Migrar a modelos de HuggingFace en Modal o usar su API directamente en Modal para reducir costos y tener mayor control. Esto se implementará después del deployment inicial con OpenAI.
> 
> **Opciones a evaluar:**
> - Usar modelos open-source de HF (Llama, Mistral, etc.) en Modal GPU
> - Usar HuggingFace Inference API desde Modal
> - Combinar ambos según necesidades (análisis vs generación)
> 
> **Referencias pendientes:**
> - Modal GPU containers: https://modal.com/docs/guide/gpu
> - HF Inference API: https://huggingface.co/docs/api-inference/

**Comando objetivo:**
```bash
modal deploy backend/modal_app.py
# Output: https://blogger-agent-tfg.modal.run
```

---

### Fase 5: Frontend Next.js (Issue #4)

**Prioridad:** BAJA (después de backend funcional)  
**Tiempo estimado:** 5-6 días  
**Dependencias:** Backend desplegado en Modal

#### Estructura Base
Tareas:
- [ ] Inicializar proyecto Next.js 14
- [ ] Configurar TypeScript
- [ ] Setup Tailwind CSS
- [ ] Estructura de carpetas

#### Componentes
**Ubicación:** `frontend/app/components/`

Tareas:
- [ ] `BlogLayout.tsx` - Layout general
- [ ] `PostHeader.tsx` - Header del post
- [ ] `PostBody.tsx` - Cuerpo del artículo
- [ ] `PostCard.tsx` - Card para listado
- [ ] `GenerateForm.tsx` - Formulario de generación

#### Páginas
Tareas:
- [ ] `app/page.tsx` - Homepage
- [ ] `app/posts/[slug]/page.tsx` - Post individual
- [ ] `app/generate/page.tsx` - Página de generación

#### API Routes
**Ubicación:** `frontend/app/api/`

Tareas:
- [ ] `app/api/generate-post/route.ts` - Llamar a Modal
- [ ] Manejo de errores
- [ ] Validación de inputs

#### Testing
- [ ] Tests de componentes
- [ ] Tests de API routes
- [ ] Tests E2E con Playwright

---

### Fase 6: Diseño (Issue #8)

**Prioridad:** BAJA  
**Tiempo estimado:** 2-3 días

Tareas:
- [ ] Inspeccionar CSS de javipas.com
- [ ] Adaptar tipografía a Tailwind
- [ ] Replicar paleta de colores
- [ ] Responsive design
- [ ] Dark mode (opcional)

---

### Fase 7: Deployment Final (Vercel)

**Prioridad:** ÚLTIMA FASE  
**Tiempo estimado:** 1 día  
**Dependencias:** Frontend completado

Tareas:
- [ ] Conectar repo a Vercel
- [ ] Configurar variables de entorno en Vercel
- [ ] Deploy inicial
- [ ] Probar integración con Modal
- [ ] Configurar dominio personalizado (opcional)
- [ ] Configurar Analytics

**Documentación:** Ya completada en `project_docs/VERCEL_DEPLOYMENT.md` ✅

**Comando:**
```bash
vercel deploy --prod
```

---

## 🧪 Testing Continuo

A lo largo de todas las fases:

- [ ] Tests unitarios para cada agente nuevo
- [ ] Tests de integración después de cada fase
- [ ] Test end-to-end al completar backend
- [ ] Performance testing
- [ ] Load testing (opcional)

---

## 📊 Cronograma Estimado

```
Semana 1: ✅ COMPLETADA
  - Días 1-3: Orquestador (Issue #9) ✅
  - Días 4-5: Agentes de análisis (Issue #6) ✅
  - Día 5: Agentes de generación (Issue #7) ✅
  - Día 5: Scraper de corpus (Issue #2) ✅
  - Documentación completa ✅

Semana 2: ✅ COMPLETADA
  - Día 1: Agente HTMLBuilder (Issue #3) ✅
  - Día 2: Migración a UV Package Manager ✅
  - Día 2: Modal deployment infrastructure (Issue #5) ✅
  - Progreso: Backend 100% funcional con tooling moderno

Semana 3: SIGUIENTE - Frontend o Deploy
  Opción A: Deploy real a Modal (Issue #5 final)
    - Día 1: Setup Modal + primer deploy
    - Días 2-5: Frontend Next.js (Issue #4)
  
  Opción B: Frontend completo primero (Issue #4)
    - Días 1-5: Frontend Next.js desarrollo completo
    - Luego: Deploy a Modal cuando sea necesario

Semana 4:
  - Día 1-3: Diseño CSS javipas.com (Issue #8)
  - Día 4-5: Testing completo

Semana 5:
  - Día 1-2: Bug fixes y refinamiento
  - Día 3: Deploy a Vercel
  - Día 4-5: Testing en producción y optimización
```

**Total:** ~5 semanas (2 semanas completadas ✅)

---

## 🎯 Comandos Útiles

```bash
# Activar entorno virtual (Windows)
.venv\Scripts\Activate.ps1

# Activar entorno virtual (Unix)
source .venv/bin/activate

# Probar orquestador actual
python -m src.orchestrator.runner \
  --topic "Test Topic" \
  --blog-url "https://javipas.com" \
  --output "test_output.json"

# Ejecutar tests
pytest tests/ -v

# Ejecutar tests con coverage
pytest --cov=aphra_blogger --cov-report=html

# Instalar dependencias nuevas con UV
uv pip install <paquete>

# Actualizar requirements.txt
uv pip freeze > requirements.txt

# Formatear código
black .

# Linting
ruff check .
```

---

## 📝 Notas Importantes

1. **Priorización:** Completar cada fase antes de la siguiente
2. **Testing:** Escribir tests a medida que desarrollas
3. **Documentación:** Actualizar READMEs con cada cambio
4. **Git:** Crear branch específica para cada issue
5. **Code Review:** PRs con descripción clara
6. **Vercel:** Reservado para el final cuando todo funcione

---

## 🔗 Enlaces Rápidos

- [Plan de Orquestación](ORCHESTRATION_PLAN.md) - Plan detallado
- [README Orquestador](../backend/src/orchestrator/README.md) - Docs del orquestador
- [Vercel Deployment](VERCEL_DEPLOYMENT.md) - Guía de deployment (pendiente)
- [Issues GitHub](https://github.com/AlejandroRS21/bloggeria/issues) - Issues tracker

---

**Última actualización:** 10 Feb 2026  
**Fase actual:** Completadas Fases 1-3 + HTMLBuilder (Issue #3) ✅  
**Siguiente:** Issue #5 (Modal Deployment) ⭐  
**Progreso general:** ~75% del backend completado

**Estado del Backend:**
- ✅ 6 agentes implementados (StyleAnalyzer, KeywordExtractor, ContentGenerator, CriticAgent, ImageSelectorAgent, HTMLBuilder)
- ✅ Orchestrador completo (7 fases)
- ✅ Web scraper WordPress-optimizado
- ✅ HTMLBuilder con output Next.js-ready (HTML/JSX/componentes)
- ✅ 40+ tests pasando
- ⏳ Modal deployment (siguiente)
- ⏳ Frontend Next.js
