# Blogger Agent TFG - Documentación para Agentes IA

> Última actualización: mayo 2026

## 📋 Resumen del Proyecto

Sistema multi-agente que analiza el estilo de escritura de un blogger y genera artículos nuevos imitando su estilo, almacenándolos en la base de datos de Supabase y visualizándolos dinámicamente en Next.js.

### Características principales:
- ✅ Extrae estilo de blogger (vocabulario, expresiones, tono)
- ✅ Busca noticias actuales sobre cualquier tema
- ✅ Genera artículos con el estilo del blogger
- ✅ Workflow visual con Daggr para debugging
- ✅ Almacena y persiste publicaciones directamente en Supabase
- ✅ Deployment serverless en Modal con GPU y frontend en Vercel

---

## 🏗️ Arquitectura del Sistema

Hay **dos pipelines** disponibles:

### Pipeline Principal: Orquestador (7 fases) ⭐

```
┌──────────────────────────────────────────────────────────────────┐
│                   BloggerOrchestrator (src/orchestrator)          │
├──────────────────────────────────────────────────────────────────┤
│  1. STYLE ANALYSIS    → StyleAnalyzer                            │
│  2. KEYWORD EXTRACTION → KeywordExtractor                        │
│  3. CONTENT GENERATION → ContentGenerator (borrador)              │
│  4. CRITIQUE          → CriticAgent (score 0-10)                 │
│  5. REFINEMENT        → ContentGenerator (si score < 7)          │
│  6. HTML BUILD        → HTMLBuilder (Markdown → HTML/JSX)        │
│  7. IMAGE SELECTION   → ImageSelectorAgent                       │
└──────────────────────────────────────────────────────────────────┘
```

### Pipeline Simplificado: generate_and_deploy.py (5 pasos - Legacy)

```
┌──────────────────────────────────────────────────────────────────┐
│                   generate_and_deploy.py                          │
├──────────────────────────────────────────────────────────────────┤
│  1. SCRAPER          → Extrae artículos del blogger              │
│  2. STYLE EXTRACTOR  → Analiza estilo (vocabulario, etc.)        │
│  3. NEWS RESEARCH    → Busca noticias actuales                   │
│  4. CONTENT GEN      → Genera artículo con estilo                │
│  5. SAVE LOCAL       → Guarda localmente en formato HTML         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Cómo Usar el Sistema

### 1. Requisitos Previos

- Python 3.11+
- Token de API (HuggingFace recomendado, gratis)

### 2. Configuración

```bash
# Opción A: HuggingFace (Recomendado - Gratis)
export HF_TOKEN="hf_..."

# Opción B: Google Gemini (Gratis con límites)
export GEMINI_API_KEY="..."

# Opción C: OpenAI (De pago)
export OPENAI_API_KEY="sk-..."
```

### 3. Generar un Artículo

**Opción A: Orquestador completo (recomendado)**
```bash
cd backend
python -m src.orchestrator.runner \
  --topic "El futuro de la IA" \
  --blog-url "https://javipas.com" \
  --output "post.json" \
  --provider huggingface
```

**Opción B: Pipeline simplificado**
```bash
cd backend
python generate_and_deploy.py "Elon Musk y la IA en 2026"
```

**Opción C: Workflow visual con Daggr**
```bash
cd backend
python daggr_blogger_workflow.py
# → http://localhost:7860
```

---

## 🔧 Componentes del Sistema

### Agentes del Orquestador (7 fases)

| Agente | Archivo | Función |
|--------|---------|---------|
| StyleAnalyzer | `style_analyzer.py` | Analiza tono, voz, expresiones del blogger |
| KeywordExtractor | `keyword_extractor.py` | Extrae keywords y patrones |
| ContentGenerator | `content_generator.py` | Genera y refina contenido |
| CriticAgent | `critic.py` | Evalúa calidad (score 0-10) |
| ImageSelectorAgent | `image_selector.py` | Prompts y ubicaciones de imágenes |
| HTMLBuilder | `html_builder.py` | Markdown → HTML/JSX con SEO |

### Agentes del Pipeline Simplificado

| Agente | Archivo | Función |
|--------|---------|---------|
| StyleExtractor | `style_extractor.py` | Extrae perfil de estilo completo |
| NewsResearchAgent | `news_research_agent.py` | Busca noticias actuales |
| ContentGenerator | `content_generator.py` | Genera artículos con estilo |

### Agentes Adicionales

| Agente | Archivo | Función |
|--------|---------|---------|
| AnonymousBloggerEmulator | `anonymous_blogger.py` | Emula blogueros anónimos con disclaimer |

### Proveedores LLM

| Provider | Archivo | Costo |
|----------|---------|-------|
| HuggingFace | `huggingface_provider.py` | 🆓 Gratis |
| Google Gemini | `gemini_provider.py` | 🆓 Gratis (con límites) |
| OpenAI | `openai_provider.py` | 💰 Pago |

---

## 📝 Ejemplos de Uso

### Generar artículo con orquestador
```bash
python -m src.orchestrator.runner \
  --topic "Apple Intelligence 2026" \
  --blog-url "https://javipas.com"
```

### Pipeline rápido sin deploy
```bash
echo "n" | python generate_and_deploy.py "Tu tema"
```

### Interfaz visual
```bash
python daggr_blogger_workflow.py
# Abrir http://localhost:7860
```

---

## ⚠️ Notas Importantes

1. **Sin token API**: El sistema usa fallback básico (~300 palabras)
2. **Con HuggingFace**: Artículos completos de 1500-2500 palabras
3. **Persistencia**: Los artículos generados vía webhook se guardan de forma instantánea en la base de datos centralizada de Supabase
4. **Estilo del blogger**: Configurado para imitar a Javi Pas (javipas.com)
5. **Modal**: Para producción, usar `modal_app.py`

---

## 📚 Archivos de Referencia

- `javipas_corpus.json` — Artículos extraídos de javipas.com
- `javipas_style_profile.json` — Perfil de estilo calculado
- `javipas_prompt_context.txt` — Contexto para prompts
- `docs/posts/` — Artículos generados (HTML)
- `docs/posts.json` — Índice de artículos
- `outputs/` — Posts generados (JSON)

---

## 🤖 Para Agentes de IA

Si usted es un agente de IA utilizando este repositorio:

1. **Configure la clave de API (API key)** antes de generar contenido.
2. **Utilice el orquestador** (`python -m src.orchestrator.runner`) como punto de entrada principal.
3. **El estilo está predefinido** en el archivo `javipas_style_profile.json`.
4. **No requiere modificar el scraper** — el corpus de datos ya ha sido extraído.
5. **Para temas diferentes**, simplemente modifique el argumento `--topic`.

### Ejemplo de uso programático:

```python
from src.orchestrator.main import BloggerOrchestrator
from src.orchestrator.config import OrchestratorConfig

config = OrchestratorConfig(
    huggingface_token="hf_...",
    provider="huggingface",
)
orchestrator = BloggerOrchestrator(config)
result = orchestrator.run(
    topic="Tu tema",
    blogger_urls=["https://javipas.com"]
)
```

---

## 📞 Soporte

- **Repo**: https://github.com/AlejandroRS21/bloggeria
- **Frontend / Vercel**: (Despliegue dinámico en producción)
- **Autor**: AlejandroRS21
- **Proyecto**: TFG — IES Rafael Alberti
