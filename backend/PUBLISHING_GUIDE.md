# Guía de Publicación - Blogger Agent TFG

## 📖 Flujo General de Publicación

Este documento detalla el procedimiento de generación y publicación de nuevos artículos en el blog. A diferencia del sistema estático original (legacy), la arquitectura actual publica y expone los contenidos dinámicamente utilizando una base de datos relacional y servicios serverless en la nube.

---

## 🔄 Proceso de Generación y Publicación en Producción

El flujo de publicación está completamente automatizado a través de la API y el orquestador serverless en la plataforma **Modal**:

### Paso 1: Petición desde la Interfaz Web (Next.js)
El usuario accede al formulario de generación en el frontend (desplegado en **Vercel**), usualmente en la ruta `/posts/new` (o `/generate` según configuración), introduce el tema deseado y las URLs del blogger de referencia.

### Paso 2: Invocación de la API de Modal
El frontend realiza una petición HTTP `POST` al webhook de Modal con el siguiente formato:

```bash
curl -X POST https://[nombre-de-usuario]--blogger-agent-tfg-webhook.modal.run \
  -H "Content-Type: application/json" \
  -d '{
    "blogger_urls": ["https://javipas.com"],
    "topic": "El papel de las GPU de NVIDIA en la era de la inteligencia artificial",
    "provider": "gemini"
  }'
```

### Paso 3: Orquestación y Persistencia Automática
Al recibir la petición:
1. El webhook de Modal ejecuta las 7 fases del orquestador multiagente.
2. Tras finalizar la fase de estructuración HTML y selección de imágenes, el backend mapea los resultados al esquema de base de datos de Supabase.
3. El backend realiza un `upsert` directo sobre la tabla `posts` de Supabase utilizando la clave de servicio privada.
4. El webhook devuelve al frontend un JSON indicando el éxito de la operación y el slug asignado al artículo:

```json
{
  "success": true,
  "data": {
    "slug": "el-papel-de-las-gpu-de-nvidia-en-la-era-de-la-inteligencia-artificial-abc123"
  },
  "error": null
}
```

### Paso 4: Visualización Dinámica
El frontend de Next.js redirige al usuario a la página de inicio o a la vista individual del artículo. Dado que las consultas a Supabase se configuran sin caché (`export const revalidate = 0`), el nuevo artículo se muestra de forma inmediata.

---

## 🛠️ Ejecución Local y Depuración

Si se desea generar artículos y cargarlos en Supabase de forma manual desde el entorno de desarrollo local:

### 1. Inserción directa ejecutando el Runner de Python

Es posible ejecutar el runner y guardar el resultado localmente en JSON como método de verificación:

```bash
cd backend
python -m src.orchestrator.runner \
  --topic "Introducción a Next.js 16 y React 19" \
  --blog-url "https://javipas.com" \
  --output "outputs/nextjs_intro.json"
```

### 2. Sincronización Manual con Supabase
Para subir el JSON generado a Supabase desde un script propio o el entorno de depuración, asegúrese de tener configuradas las variables de entorno en el archivo `.env` del backend:

```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_KEY="your-service-role-key"
```

---

## 📁 Estructura del Esquema de Publicación (Supabase)

La tabla `posts` en la base de datos de Supabase sigue la siguiente estructura:

*   `id` (text, primary key): Identificador único del flujo de trabajo de generación.
*   `slug` (text, unique): Dirección URL amigable generada a partir del título y un identificador único para evitar colisiones.
*   `title` (text): Título del artículo.
*   `description` (text): Resumen o meta-descripción corta.
*   `content` (text): Cuerpo del artículo en formato HTML semántico optimizado.
*   `cover_image_url` (text, nullable): URL de la imagen principal del artículo.
*   `author` (text): Alias del blogger emulado (por ejemplo, "JaviPas").
*   `date` (text): Fecha de publicación formateada (`YYYY-MM-DD`).
*   `word_count` (int): Cantidad total de palabras.
*   `reading_time` (int): Tiempo estimado de lectura en minutos.
*   `tags` (text[]): Etiquetas o palabras clave asociadas.
*   `keywords` (text[]): Conceptos clave extraídos de las noticias de investigación.

---

## ⚙️ Tareas de Mantenimiento y Limpieza Automatizada

Para evitar la acumulación excesiva de posts y controlar los límites de uso de Supabase, existe una función programada en Modal (`daily_cleanup` en `modal_app.py`) ejecutada de forma diaria vía Cron que se encarga de:

1. Conservar los 100 artículos más recientes.
2. Eliminar de la base de datos las publicaciones antiguas o aquellas que no cumplan con los estándares de longitud establecidos en las revisiones de calidad.
