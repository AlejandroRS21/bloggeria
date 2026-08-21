# Guía de Setup - Blogger Agent TFG

Esta guía te explica **cómo configurar el proyecto** para que el orquestador funcione automáticamente.

---

## 🎯 Dos Opciones de Desarrollo

### **Opción 1: Desarrollo Local (VSCode) + Modal** ⭐ RECOMENDADO

**¿Por qué?** Tienes control total, GitHub Copilot te ayuda, y puedes debuggear fácilmente.

#### Paso 1: Clonar el Repositorio en tu PC

```bash
# Abre una terminal en tu ordenador
cd ~/Documents  # O donde quieras trabajar
git clone https://github.com/AlejandroRS21/bloggeria.git
cd blogger-agent-tfg
```

#### Paso 2: Instalar Python y Dependencias

```bash
# Asegúrate de tener Python 3.11+
python --version

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\\Scripts\\activate
# En Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

**Crear `requirements.txt` si no existe:**
```txt
aphra>=0.1.0
modal>=0.55.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
python-dotenv>=1.0.0
spacy>=3.7.0
transformers>=4.35.0
beautifulsoup4>=4.12.0
openai>=1.3.0
anthropic>=0.7.0
langchain>=0.1.0
```

#### Paso 3: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# .env
OPENAI_API_KEY=tu-api-key-aqui
ANTHROPIC_API_KEY=tu-api-key-aqui
MODAL_TOKEN_ID=tu-modal-token
MODAL_TOKEN_SECRET=tu-modal-secret
BLOG_URL=https://javipas.com
```

#### Paso 4: Abrir en VSCode con Copilot

```bash
code .
```

**Instalar extensiones recomendadas:**
- GitHub Copilot
- Python
- Pylance
- GitLens

#### Paso 5: Desarrollar el Orquestador

Sigue la **Issue #9** para implementar:

1. Crear `src/orchestrator/main.py`
2. Implementar clase `BloggerOrchestrator`
3. Crear CLI en `src/orchestrator/cli.py`

**Ejemplo de `src/orchestrator/main.py`:**

```python
# src/orchestrator/main.py
from typing import Dict, List
import asyncio
from aphra import Workflow, Agent

class BloggerOrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.workflow = Workflow("blogger-content-generation")
        self._setup_agents()
    
    def _setup_agents(self):
        # Fase 1: Análisis
        self.tone_analyzer = Agent("tone-analyzer")
        self.topic_extractor = Agent("topic-extractor")
        self.frequency_analyzer = Agent("frequency-analyzer")
        
        # Fase 2: Generación
        self.base_writer = Agent("base-writer")
        self.mimicry_expert = Agent("mimicry-expert")
        self.image_selector = Agent("image-selector")
        
        # Fase 3: Revisión
        self.critic = Agent("critic-agent")
        
        # Fase 4: Construcción
        self.nextjs_builder = Agent("nextjs-builder")
    
    async def run(self, topic: str) -> Dict:
        print("[INFO] 🚀 Iniciando orquestador...")
        
        # Fase 1: Análisis
        print("[INFO] Fase 1: Análisis iniciado...")
        analysis_results = await self._run_analysis_phase()
        
        # Fase 2: Generación
        print("[INFO] Fase 2: Generación iniciado...")
        content = await self._run_generation_phase(topic, analysis_results)
        
        # Fase 3: Revisión
        print("[INFO] Fase 3: Revisión iniciado...")
        final_content = await self._run_review_phase(content)
        
        # Fase 4: Construcción
        print("[INFO] Fase 4: Construcción final...")
        output = await self._run_build_phase(final_content)
        
        print("[SUCCESS] ✅ Artículo generado exitosamente")
        return output
    
    async def _run_analysis_phase(self) -> Dict:
        # TODO: Implementar ejecución paralela de agentes
        tasks = [
            self.tone_analyzer.execute(),
            self.topic_extractor.execute(),
            self.frequency_analyzer.execute()
        ]
        results = await asyncio.gather(*tasks)
        return {"tone": results[0], "topics": results[1], "keywords": results[2]}
    
    async def _run_generation_phase(self, topic: str, analysis: Dict) -> Dict:
        # TODO: Implementar generación secuencial
        draft = await self.base_writer.execute(topic)
        mimicked = await self.mimicry_expert.execute(draft, analysis)
        images = await self.image_selector.execute(mimicked)
        return {"text": mimicked, "images": images}
    
    async def _run_review_phase(self, content: Dict) -> Dict:
        # TODO: Implementar bucle de feedback
        is_approved = False
        while not is_approved:
            feedback = await self.critic.execute(content)
            if feedback["status"] == "approved":
                is_approved = True
            else:
                content = await self.mimicry_expert.execute(content, feedback)
        return content
    
    async def _run_build_phase(self, content: Dict) -> Dict:
        # TODO: Construir output final
        output = await self.nextjs_builder.execute(content)
        return output

# Ejemplo de uso
if __name__ == "__main__":
    config = {"blog_url": "https://javipas.com"}
    orchestrator = BloggerOrchestrator(config)
    result = asyncio.run(orchestrator.run("OpenClaw me alucina"))
    print(result)
```

#### Paso 6: Probar Localmente

```bash
# Ejecutar el orquestador
python -m src.orchestrator.main

# O si tienes CLI:
python -m src.orchestrator.cli --topic "Inteligencia Artificial"
```

#### Paso 7: Deployar a Modal

**Instalar Modal CLI:**
```bash
pip install modal
modal setup
```

**Crear `modal_app.py`:**
```python
import modal
from src.orchestrator.main import BloggerOrchestrator

stub = modal.Stub("blogger-agent")

@stub.function(
    image=modal.Image.debian_slim().pip_install_from_requirements("requirements.txt"),
    secrets=[modal.Secret.from_name("openai-secret")]
)
async def generate_post(topic: str):
    config = {"blog_url": "https://javipas.com"}
    orchestrator = BloggerOrchestrator(config)
    return await orchestrator.run(topic)

@stub.local_entrypoint()
def main(topic: str):
    result = generate_post.remote(topic)
    print(result)
```

**Deployar:**
```bash
modal deploy modal_app.py
```

**Ejecutar en Modal:**
```bash
modal run modal_app.py --topic "OpenClaw me alucina"
```

---

### **Opción 2: Todo en Cloud (GitHub + Modal)**

⚠️ **Menos recomendado para desarrollo**, pero útil para deployment automático.

#### Configurar GitHub Actions

Crea `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Modal

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install modal
          pip install -r requirements.txt
      
      - name: Deploy to Modal
        env:
          MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
          MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
        run: |
          modal token set --token-id $MODAL_TOKEN_ID --token-secret $MODAL_TOKEN_SECRET
          modal deploy modal_app.py
```

#### Añadir Secrets en GitHub

1. Ve a: **Settings** → **Secrets and variables** → **Actions**
2. Añade:
   - `MODAL_TOKEN_ID`
   - `MODAL_TOKEN_SECRET`
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`

#### Workflow Automatizado

Cuando hagas `git push`:
1. GitHub Actions ejecuta tests
2. Si pasan, auto-deploya a Modal
3. El orquestador queda disponible en la nube

---

## 📝 Resumen: ¿Qué Hacer?

### Para Desarrollo (Recomendado):
1. ✅ Clona el repo en tu PC
2. ✅ Abre con VSCode + Copilot
3. ✅ Implementa el orquestador siguiendo Issue #9
4. ✅ Prueba localmente
5. ✅ Deploy a Modal cuando funcione

### Para Auto-Deployment:
1. ✅ Configura GitHub Actions
2. ✅ Añade secrets
3. ✅ Haz push y deja que se despliegue automáticamente

---

## 🎯 Próximos Pasos

1. **Clona el repo**: `git clone https://github.com/AlejandroRS21/bloggeria.git`
2. **Lee Issue #9**: Tiene el plan completo de implementación
3. **Comienza con VSCode**: GitHub Copilot te ayudará mucho
4. **Pregunta en el equipo**: Usa las issues para dudas

---

**Última actualización**: 10 de febrero de 2026
