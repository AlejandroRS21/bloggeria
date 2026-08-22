# Backend - Blogger Agent TFG

Backend Python del sistema multiagente para mimetizar el estilo de escritura de bloggers.

## 🏗️ Estructura

```
backend/
├── aphra_blogger/
│   ├── llm/                          # Abstracción LLM multiproveedor
│   │   ├── __init__.py
│   │   ├── base.py                   # Clases abstractas
│   │   ├── factory.py                # Factory para proveedores
│   │   ├── huggingface_provider.py   # HuggingFace (primario, gratis)
│   │   ├── openai_provider.py        # OpenAI (fallback)
│   │   └── gemini_provider.py        # Google Gemini (alternativo)
│   ├── agents/                       # Agentes especializados
│   │   ├── __init__.py
│   │   ├── style_analyzer.py         # Análisis de estilo
│   │   ├── keyword_extractor.py      # Extracción de keywords
│   │   ├── content_generator.py      # Generación de contenido
│   │   ├── critic.py                 # Crítica y evaluación
│   │   ├── image_selector.py         # Selección de imágenes
│   │   ├── html_builder.py           # Markdown → HTML/JSX
│   │   ├── anonymous_blogger.py      # Emulación de blogueros anónimos
│   │   ├── style_extractor.py        # Extracción legacy de estilo
│   │   └── README.md                 # Documentación de agentes
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── blogger_style.py          # Workflow principal
│   ├── config/
│   │   ├── __init__.py
│   │   └── default.toml              # Configuración LLM
│   ├── __init__.py
│   └── context.py                    # Contexto compartido
├── src/
│   └── orchestrator/                 # Sistema de orquestación
│       ├── __init__.py
│       ├── main.py                   # BloggerOrchestrator (7 fases)
│       ├── config.py                 # OrchestratorConfig
│       ├── state.py                  # StateManager y WorkflowState
│       ├── runner.py                 # Interfaz de línea de comandos (CLI)
│       └── README.md                 # Documentación del orquestador
├── tools/                            # Herramientas de apoyo
│   ├── __init__.py
│   ├── scraper.py                    # Web scraper WordPress
│   └── README.md                     # Documentación del scraper
├── tests/                            # Batería de pruebas (~80 tests)
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   ├── test_html_builder.py
│   ├── test_scraper.py
│   ├── test_workflow.py
│   └── test_anonymous_blogger.py
├── daggr_blogger_workflow.py         # ⭐ Workflow visual con Daggr
├── modal_app.py                      # Endpoint serverless de Modal
├── generate_and_deploy.py            # (Legacy) Script simplificado local
├── test_full_pipeline.py             # Test de integración local
├── requirements.txt                  # Dependencias del backend
├── pyproject.toml                    # Configuración de linter y empaquetado
├── setup.sh / setup.ps1              # Scripts de instalación
└── README.md                         # Este archivo
```

---

## 🚀 Instalación y Ejecución Local

### Requisitos Previos

- Python 3.11+
- **uv** (gestor de paquetes Python recomendado)
- **HuggingFace Token** (gratuito): `HF_TOKEN`
- Proveedores alternativos: `GEMINI_API_KEY` (gratuito con límites), `OPENAI_API_KEY` (pago)

### Instalación con uv ⚡

**Opción automatizada** (recomendada):

```bash
# En Linux o macOS
chmod +x setup.sh
./setup.sh

# En Windows
.\setup.ps1
```

**Opción manual:**

```bash
# Crear entorno virtual e instalar dependencias
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Ejecución del Orquestador (7 fases)

```bash
export HF_TOKEN="hf_..."
python -m src.orchestrator.runner \
  --topic "Desarrollo de microservicios serverless" \
  --blog-url "https://javipas.com" \
  --output "resultado.json" \
  --provider huggingface
```

Las fases del orquestador son:
1. **STYLE_ANALYSIS**: El StyleAnalyzer procesa posts del corpus para extraer métricas estilísticas.
2. **KEYWORD_EXTRACTION**: Extracción de palabras clave semánticas relevantes.
3. **CONTENT_GENERATION_DRAFT**: Redacción del borrador en base a los datos de estilo.
4. **CRITIQUE**: CriticAgent evalúa el borrador estilísticamente (puntuación de 0 a 10).
5. **REFINEMENT**: El generador refina el texto aplicando las sugerencias críticas si el puntaje es menor a 7.
6. **HTML_BUILD**: Conversión del Markdown final a HTML estructurado y componentes JSX.
7. **IMAGE_SELECTION**: Selección de imágenes temáticas con prompts descriptivos.

---

## 🎨 Workflow Visual interactivo con Daggr

Daggr proporciona un lienzo interactivo y visual para controlar el flujo de agentes:

```bash
python daggr_blogger_workflow.py
# Abrir http://localhost:7860 en el navegador
```

---

## 🧪 Pruebas unitarias y de integración

```bash
cd backend
# Ejecutar todo el conjunto de pruebas (~80 tests)
pytest tests/ -v

# Pruebas de integración E2E local
python test_full_pipeline.py
```

---

## 🌐 Despliegue Serverless en Modal

El backend expone su lógica a través de un webhook de Modal para interactuar directamente con el frontend y persistir los artículos en la base de datos de Supabase.

### 1. Configuración de secretos en Modal

Debe registrar las credenciales necesarias en su panel de control de Modal:

```bash
modal secret create openai-secret OPENAI_API_KEY="sk-..."
modal secret create gemini-secret GEMINI_API_KEY="..."
modal secret create huggingface-secret HF_TOKEN="hf_..."
modal secret create supabase-secret SUPABASE_URL="https://..." SUPABASE_SERVICE_KEY="..." SUPABASE_ANON_KEY="..."
```

### 2. Desplegar el webhook

```bash
modal deploy backend/modal_app.py
```

### 3. Probar el endpoint expuesto

```bash
curl -X POST https://[nombre-usuario]--blogger-agent-tfg-webhook.modal.run \
  -H "Content-Type: application/json" \
  -d '{
    "blogger_urls": ["https://javipas.com"],
    "topic": "Arquitectura serverless en 2026"
  }'
```

---

## 📋 Hitos de Desarrollo

**Completado:**
- ✅ Workflow de 7 fases con persistencia automática de estado.
- ✅ 8 agentes especializados integrados con soporte multimodelo (HuggingFace Inference API, Gemini, OpenAI).
- ✅ Batería de pruebas unitarias y de integración robusta.
- ✅ Interfaz gráfica Daggr interactiva en Gradio.
- ✅ Conexión y almacenamiento de posts directamente en Supabase.
- ✅ Endpoint serverless en Modal y despliegue del frontend Next.js en Vercel.

**Pendientes:**
- ⏳ Automatización de pruebas mediante GitHub Actions (CI/CD).
- ⏳ Pruebas E2E de interfaz de extremo a extremo utilizando Playwright.
