"""
Blogger Agent TFG - Visualización Real del Flujo de Agentes con Daggr
====================================================================

Esta aplicación utiliza los agentes reales del backend para generar
posts de blog, visualizando cada paso en el grafo de Daggr.

Uso:
    uv run python daggr_blogger_workflow.py
    
Luego abrir: http://localhost:7860
"""

import os
import sys
import json
import gradio as gr
from daggr import FnNode, Graph
from typing import Dict, Any, List
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno de forma robusta
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Variables de entorno cargadas desde {env_path}")
else:
    print(f"⚠️ No se encontró el archivo .env en {env_path}")

# Asegurar que el path del backend esté disponible
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from src.orchestrator.config import OrchestratorConfig
from aphra_blogger.llm.factory import create_llm_provider
from aphra_blogger.agents.style_analyzer import StyleAnalyzer
from aphra_blogger.agents.keyword_extractor import KeywordExtractor
from aphra_blogger.agents.content_generator import ContentGenerator
from aphra_blogger.agents.critic import CriticAgent
from aphra_blogger.agents.image_selector import ImageSelectorAgent
from aphra_blogger.agents.html_builder import HTMLBuilder

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

class WorkflowState:
    def __init__(self):
        self.config = OrchestratorConfig.default()
        self.llm = None
        self.agents = {}

state = WorkflowState()

def initialize_agents(provider: str, api_key: str):
    if provider:
        state.config.provider = provider
    
    # Priorizar API key pasada por el usuario, si no usar la de .env
    actual_key = api_key if api_key and api_key.strip() != "" else None
    
    # Debug info
    print(f"Initializing agents with provider: {provider}")
    print(f"MODAL_TOKEN_ID present in env: {bool(os.getenv('MODAL_TOKEN_ID'))}")

    if provider == "modal":
        state.config.modal_api_key = actual_key or os.getenv("MODAL_TOKEN_ID")
    elif provider == "huggingface":
        state.config.hf_token = actual_key or os.getenv("HF_TOKEN")
        if actual_key: os.environ["HF_TOKEN"] = actual_key
    elif provider == "openai":
        state.config.openai_api_key = actual_key or os.getenv("OPENAI_API_KEY")
        if actual_key: os.environ["OPENAI_API_KEY"] = actual_key
    elif provider == "gemini":
        state.config.gemini_api_key = actual_key or os.getenv("GEMINI_API_KEY")
        if actual_key: os.environ["GEMINI_API_KEY"] = actual_key

    # Crear LLM
    try:
        state.llm = create_llm_provider(
            provider=state.config.provider,
            api_key=actual_key,
            temperature=state.config.temperature
        )
        
        # Crear Agentes usando el LLM ya inicializado
        state.agents = {
            "style": StyleAnalyzer(provider=state.config.provider, api_key=actual_key),
            "keywords": KeywordExtractor(provider=state.config.provider, api_key=actual_key),
            "generator": ContentGenerator(provider=state.config.provider, api_key=actual_key),
            "critic": CriticAgent(provider=state.config.provider, api_key=actual_key),
            "images": ImageSelectorAgent(provider=state.config.provider, api_key=actual_key),
            "html": HTMLBuilder(provider=state.config.provider, api_key=actual_key)
        }
        return f"✅ Agentes listos con {state.config.provider.upper()}"
    except Exception as e:
        return f"❌ Error al inicializar: {str(e)}"

# ============================================================================
# COMPONENTES COMPARTIDOS
# ============================================================================

# Entradas
provider_input = gr.Dropdown(choices=["gemini", "modal", "huggingface", "openai"], value="gemini", label="Proveedor LLM")
api_key_input = gr.Textbox(label="API Key / Token", placeholder="Opcional si está en .env", type="password")
blogger_name_input = gr.Textbox(label="Nombre del Blogger", value="TechGuru")
sample_posts_input = gr.Textbox(label="Muestras de Estilo", lines=5, value="Hoy aprendí sobre React Hooks.\nLa IA está cambiando el mundo.")
topic_input = gr.Textbox(label="Tema del Post", value="El futuro de Next.js")

# Salidas (compartidas entre nodos individuales y el botón "Run All")
style_output = gr.Textbox(label="Análisis de Estilo", lines=10)
keywords_output = gr.Textbox(label="Keywords Extraídas")
topic_out_output = gr.Textbox(label="Tema Original", visible=False)
draft_output = gr.Textbox(label="Borrador", lines=20)
critique_output = gr.Textbox(label="Crítica", lines=10)
refined_output = gr.Textbox(label="Contenido Refinado", lines=20)
images_output = gr.Textbox(label="Imágenes")
html_output = gr.Textbox(label="Código HTML Final", lines=10)

# ============================================================================
# NODOS DEL GRAFO
# ============================================================================

def setup_workflow(provider: str, api_key: str) -> Dict[str, str]:
    return {"status": initialize_agents(provider, api_key)}

config_node = FnNode(
    fn=setup_workflow,
    name="⚙️ Configuración",
    inputs={
        "provider": provider_input,
        "api_key": api_key_input
    },
    outputs={"status": gr.Textbox(label="Estado")}
)

def ensure_agents():
    if not state.agents:
        res = initialize_agents("modal", "")
        if "❌" in res:
            raise Exception(res)

def safe_json_load(data: Any) -> Any:
    """Helper to handle both JSON strings and already parsed objects (dict/list)."""
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, str) and data.strip():
        try:
            # Clean up potential markdown code blocks if the LLM included them
            clean_data = data.strip()
            if clean_data.startswith("```json"):
                clean_data = clean_data[7:].strip()
            if clean_data.endswith("```"):
                clean_data = clean_data[:-3].strip()
            return json.loads(clean_data)
        except Exception as e:
            print(f"⚠️ Warning: Could not parse JSON, returning raw string: {e}")
            return data
    return {}

def ensure_dict(data: Any) -> Dict[str, Any]:
    """Ensures we have a dictionary."""
    parsed = safe_json_load(data)
    if isinstance(parsed, dict):
        return parsed
    return {}

def ensure_list(data: Any) -> List[Any]:
    """Ensures we have a list."""
    parsed = safe_json_load(data)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return [parsed]
    return []

def ensure_string(data: Any, key: str = None) -> str:
    """Ensures we have a string, extracting from dict if necessary."""
    if data is None:
        return ""
    
    # Si ya es un diccionario
    if isinstance(data, dict):
        if key and key in data:
            return str(data[key])
        for k in ["topic_out", "topic", "content", "text", "refined_content"]:
            if k in data:
                return str(data[k])
        # Si no hay ninguna de las claves que buscamos, devolver el primer valor no-dict
        for k, v in data.items():
            if not isinstance(v, (dict, list)):
                return str(v)
        return str(next(iter(data.values()))) if data else ""
    
    # Si es un string, podría ser un diccionario serializado (típico en Gradio/Daggr)
    if isinstance(data, str):
        data_stripped = data.strip()
        # Caso especial para Gradio: a veces es un string de un dict de Python
        if data_stripped.startswith("{") and data_stripped.endswith("}"):
            try:
                # Intentar parsear como JSON pero manejar comillas simples de Python repr()
                import json
                # Reemplazo agresivo de comillas simples por dobles para reprs de Python
                # pero solo si no es JSON válido ya
                try:
                    parsed = json.loads(data_stripped)
                except:
                    # Intento ast.literal_eval que es más seguro para strings de Python
                    import ast
                    parsed = ast.literal_eval(data_stripped)
                
                if isinstance(parsed, dict):
                    if key and key in parsed:
                        return str(parsed[key])
                    for k in ["topic_out", "topic", "content", "text", "refined_content"]:
                        if k in parsed:
                            return str(parsed[k])
                    # Si no, devolver el valor de la primera clave
                    if parsed:
                        return str(next(iter(parsed.values())))
            except Exception as e:
                print(f"⚠️ Error parsing potential dict string: {e}")
        return data_stripped
    
    return str(data)

def analyze_style(status: str, blogger_name: str, sample_posts: str) -> Dict[str, str]:
    ensure_agents()
    print(f"🔍 Analyzing style for: {blogger_name}")
    analysis = state.agents["style"].analyze(blogger_urls=[], sample_text=sample_posts)
    return {"style_json": json.dumps(analysis, indent=2, ensure_ascii=False)}

style_analyzer = FnNode(
    fn=analyze_style,
    name="1️⃣ Style Analyzer",
    inputs={
        "status": config_node.status,
        "blogger_name": blogger_name_input,
        "sample_posts": sample_posts_input
    },
    outputs={"style_json": style_output}
)

def extract_keywords(topic: Any, style_json: Any) -> Dict[str, Any]:
    ensure_agents()
    actual_topic = ensure_string(topic, "topic")
    print(f"🔍 Extracting keywords for: {actual_topic} (Style type: {type(style_json)})")
    style = ensure_dict(style_json)
    res = state.agents["keywords"].extract(blogger_urls=[], sample_text=actual_topic)
    keywords = res.get("keywords", [])
    if isinstance(keywords, list):
        kw_str = ", ".join(keywords)
    else:
        kw_str = str(keywords)
    return {"keywords": kw_str, "topic_out": actual_topic}

keyword_extractor = FnNode(
    fn=extract_keywords,
    name="2️⃣ Keyword Extractor",
    inputs={
        "topic": topic_input,
        "style_json": style_analyzer.style_json
    },
    outputs={
        "keywords": keywords_output,
        "topic_out": topic_out_output
    }
)

def generate_content(topic_out: Any, keywords: Any, style_json: Any) -> Dict[str, str]:
    ensure_agents()
    actual_topic = ensure_string(topic_out, "topic_out")
    actual_keywords = ensure_string(keywords, "keywords")
    
    style = ensure_dict(style_json)
    kw_list = [k.strip() for k in actual_keywords.split(",") if k.strip()]
    
    # ... existing logic ...
    related_links = ""
    try:
        index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "posts.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                posts = json.load(f)
                # Filtramos posts que tengan palabras similares en el título o descripción
                topic_words = set(actual_topic.lower().split())
                matches = []
                for p in posts:
                    p_title_words = set(p["title"].lower().split())
                    if topic_words.intersection(p_title_words):
                        matches.append(f"- [{p['title']}](post.html?id={p['id']})")
                
                if matches:
                    related_links = "\n\n### Artículos relacionados que ya hemos escrito:\n" + "\n".join(matches[:3])
    except Exception as e:
        print(f"⚠️ Error buscando memoria: {e}")

    content = state.agents["generator"].generate_draft(
        topic=actual_topic,
        style_profile=style,
        keywords=kw_list,
        blogger_urls=state.get("blogger_urls", None)
    )
    
    if related_links:
        content += related_links
        
    return {"draft_content": content}

content_generator = FnNode(
    fn=generate_content,
    name="3️⃣ Content Generator",
    inputs={
        "topic_out": keyword_extractor.topic_out,
        "keywords": keyword_extractor.keywords,
        "style_json": style_analyzer.style_json
    },
    outputs={"draft_content": draft_output}
)

def critique_content(topic_out: Any, content: Any, style_json: Any) -> Dict[str, str]:
    ensure_agents()
    actual_topic = ensure_string(topic_out, "topic_out")
    actual_content = ensure_string(content, "draft_content")
    style = ensure_dict(style_json)
    critique = state.agents["critic"].critique(content=actual_content, style_profile=style, topic=actual_topic)
    return {"critique_json": json.dumps(critique, indent=2, ensure_ascii=False)}

critic_agent = FnNode(
    fn=critique_content,
    name="4️⃣ Critic Agent",
    inputs={
        "topic_out": keyword_extractor.topic_out,
        "content": content_generator.draft_content,
        "style_json": style_analyzer.style_json
    },
    outputs={"critique_json": critique_output}
)

def refine_content(draft: Any, critique_json: Any, style_json: Any) -> Dict[str, str]:
    ensure_agents()
    actual_draft = ensure_string(draft, "draft_content")
    critique = ensure_dict(critique_json)
    style = ensure_dict(style_json)
    
    print("🔍 Refining content based on critique...")
    refined = state.agents["generator"].refine_content(
        draft=actual_draft, 
        critique_feedback=critique, 
        style_profile=style
    )
    return {"refined_content": refined}

content_refiner = FnNode(
    fn=refine_content,
    name="4.5️⃣ Content Refiner",
    inputs={
        "draft": content_generator.draft_content,
        "critique_json": critic_agent.critique_json,
        "style_json": style_analyzer.style_json
    },
    outputs={"refined_content": refined_output}
)

def select_images(topic_out: Any, content: Any) -> Dict[str, str]:
    ensure_agents()
    actual_topic = ensure_string(topic_out, "topic_out")
    actual_content = ensure_string(content, "refined_content")
    images = state.agents["images"].select_images(content=actual_content, topic=actual_topic)
    return {"image_urls": json.dumps(images, indent=2)}

image_selector = FnNode(
    fn=select_images,
    name="5️⃣ Image Selector",
    inputs={
        "topic_out": keyword_extractor.topic_out,
        "content": content_refiner.refined_content
    },
    outputs={"image_urls": images_output}
)

def build_html(topic_out: Any, content: Any, images_json: Any, style_json: Any) -> Dict[str, str]:
    ensure_agents()
    actual_topic = ensure_string(topic_out, "topic_out")
    actual_content = ensure_string(content, "refined_content")
    style = ensure_dict(style_json)
    images = safe_json_load(images_json)
    if not isinstance(images, list):
        if isinstance(images, dict) and "images" in images:
            images = images["images"]
        else:
            images = []
    
    # Inyectar URLs de loremflickr si no hay una real (para tener imágenes visibles)
    import time
    for i, img in enumerate(images):
        if not img.get("url") or "/api/placeholder/" in img.get("url", ""):
            # Usamos el topic como keyword
            kw = actual_topic.split()[-1] if actual_topic else "tech"
            img["url"] = f"https://loremflickr.com/800/400/{kw}?random={i}_{int(time.time())}"
            
    output = state.agents["html"].build(content=actual_content, topic=actual_topic, images=images, style_profile=style)
    
    # Guardar el post para el frontend
    try:
        # Generar slug y asegurar que no esté vacío, con límite para evitar problemas de ruta
        slug = actual_topic.lower().replace(" ", "-")
        slug = "".join([c for c in slug if c.isalnum() or c == '-'])
        if len(slug) > 100:
            slug = slug[:100].rstrip("-")
            
        if not slug:
            slug = f"post-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        # Rutas absolutas para evitar confusiones
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(workspace_root, "docs", "posts")
        os.makedirs(output_dir, exist_ok=True)
        
        post_data = {
            "id": slug,
            "title": actual_topic,
            "description": actual_content[:150] + "...",
            "html_code": output.html,
            "metadata": {
                "word_count": len(actual_content.split()),
                "reading_time": max(1, len(actual_content.split()) // 200),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "author": "Blogger Agent",
                "tags": style.get("personality_traits", ["AI"]) if isinstance(style, dict) else ["AI"]
            }
        }
        
        # Guardar archivo individual
        post_file_path = os.path.join(output_dir, f"{slug}.html")
        with open(post_file_path, "w", encoding="utf-8") as f:
            f.write(output.html)
            
        print(f"✅ Post individual guardado en: {post_file_path}")
        
        # Actualizar el índice posts.json
        index_path = os.path.join(workspace_root, "docs", "posts.json")
        posts_index = []
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    content_json = f.read().strip()
                    if content_json and content_json != "[]":
                        posts_index = json.loads(content_json)
            except Exception as e:
                print(f"⚠️ Error leyendo índice actual: {e}")
                posts_index = []
        
        # Evitar duplicados
        posts_index = [p for p in posts_index if p.get("id") != slug]
        
        # Añadir resumen del post al principio
        posts_index.insert(0, {
            "id": post_data["id"],
            "title": post_data["title"],
            "description": post_data["description"],
            "date": post_data["metadata"]["date"],
            "author": post_data["metadata"]["author"],
            "tags": post_data["metadata"]["tags"]
        })
        
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(posts_index, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Índice de posts actualizado: {index_path} (Total: {len(posts_index)})")
    except Exception as e:
        print(f"❌ Error crítico al guardar el post: {e}")
        import traceback
        traceback.print_exc()

    return {"final_html": output.html}

html_builder = FnNode(
    fn=build_html,
    name="6️⃣ HTML Builder",
    inputs={
        "topic_out": keyword_extractor.topic_out,
        "content": content_refiner.refined_content,
        "images_json": image_selector.image_urls,
        "style_json": style_analyzer.style_json
    },
    outputs={"final_html": html_output}
)

def run_full_pipeline(provider: str, api_key: str, blogger_name: str, sample_posts: str, topic: str) -> Dict[str, Any]:
    """Ejecuta todos los nodos en secuencia y actualiza todos los cuadros de texto del tirón."""
    print("🚀 Iniciando ejecución completa del workflow...")
    
    # Asegurar que los agentes se inicializan con la config actual
    initialize_agents(provider, api_key)
    
    try:
        # 1. Estilo
        print("-> Analizando estilo...")
        style_out = analyze_style("Ready", blogger_name, sample_posts)
        style_json = style_out["style_json"]
        
        # 2. Keywords
        print("-> Extrayendo keywords...")
        kw_out = extract_keywords(topic, style_json)
        keywords = kw_out["keywords"]
        actual_topic = kw_out["topic_out"]
        
        # 4. Generator
        print("-> Generando contenido...")
        gen_out = generate_content(actual_topic, keywords, style_json)
        draft = gen_out["draft_content"]
        
        # 5. Critic
        print("-> Criticando...")
        crit_out = critique_content(actual_topic, draft, style_json)
        critique = crit_out["critique_json"]
        
        # 6. Refiner
        print("-> Refinando...")
        ref_out = refine_content(draft, critique, style_json)
        refined = ref_out["refined_content"]
        
        # 7. Images
        print("-> Seleccionando imágenes...")
        img_out = select_images(actual_topic, refined)
        images_json = img_out["image_urls"]
        
        # 8. HTML
        print("-> Construyendo HTML final...")
        html_out = build_html(actual_topic, refined, images_json, style_json)
        final_html = html_out["final_html"]
        
        print("✅ ¡Pipeline completado con éxito!")
        return {
            "style_json": style_json,
            "keywords": keywords,
            "draft": draft,
            "critique": critique,
            "refined": refined,
            "images": images_json,
            "final_html": final_html
        }
    except Exception as e:
        print(f"❌ Error en pipeline: {e}")
        import traceback
        traceback.print_exc()
        return {"final_html": f"Error: {str(e)}"}

full_pipeline_node = FnNode(
    fn=run_full_pipeline,
    name="🚀 GENERACIÓN AUTOMÁTICA",
    inputs={
        "provider": provider_input,
        "api_key": api_key_input,
        "blogger_name": blogger_name_input,
        "sample_posts": sample_posts_input,
        "topic": topic_input
    },
    outputs={
        "style_json": style_output,
        "keywords": keywords_output,
        "draft": draft_output,
        "critique": critique_output,
        "refined": refined_output,
        "images": images_output,
        "final_html": html_output
    }
)

def run_deploy() -> str:
    """Ejecuta el script de despliegue y devuelve el resultado."""
    print("🚀 Iniciando despliegue en GitHub Pages...")
    import subprocess
    import os
    
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Añadir y Commitear cambios en docs
        subprocess.run(["git", "add", "docs/"], capture_output=True, cwd=root_dir)
        subprocess.run(["git", "commit", "-m", "Deploy automático desde Daggr UI"], capture_output=True, cwd=root_dir)
        
        # Eliminar local por si acaso
        subprocess.run(["git", "branch", "-D", "feature/github-pages-static"], capture_output=True, cwd=root_dir)
        
        # Deploy a la rama correcta empujando el proyecto completo
        result = subprocess.run(
            ["git", "push", "origin", "HEAD:feature/github-pages-static", "--force"],
            capture_output=True,
            text=True,
            cwd=root_dir
        )
        
        if result.returncode == 0:
            print("✅ Despliegue completado con éxito.")
            return f"✅ ¡Desplegado en GitHub Pages!\nUrl: https://alejandrors21.github.io/blogger-agent-tfg/"
        else:
            print(f"❌ Error en despliegue: {result.stderr}")
            return f"❌ Error:\n{result.stderr}\n{result.stdout}"
    except Exception as e:
        return f"❌ Excepción ejecutando git: {str(e)}"

deploy_node = FnNode(
    fn=run_deploy,
    name="🌐 DESPLEGAR BLOG",
    inputs={},
    outputs={"res": gr.Textbox(label="Resultado del Despliegue")}
)

# ============================================================================
# LANZAMIENTO
# ============================================================================

graph = Graph(
    name="🚀 Blogger Agent TFG - LIVE Workflow",
    nodes=[
        config_node, 
        full_pipeline_node, # ✅ Nodo maestro añadido
        deploy_node,      # ✅ Botón de despliegue
        style_analyzer, 
        keyword_extractor, 
        content_generator, 
        critic_agent, 
        content_refiner,
        image_selector, 
        html_builder
    ],
)

if __name__ == "__main__":
    print("-" * 50)
    print("Lanzando Daggr con agentes reales del backend...")
    print("Abriendo en http://localhost:7860")
    print("-" * 50)
    graph.launch(share=False)
