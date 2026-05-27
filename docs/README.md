# ⚠️ OBSERVACIÓN IMPORTANTE: DOCUMENTO Y DIRECTORIO OBSOLETOS (LEGACY)

> [!WARNING]
> **Este directorio (`docs/`) y toda la lógica de frontend estático desplegada en GitHub Pages han sido deprecados y marcados como obsoletos.** El proyecto actualmente emplea una arquitectura dinámica desplegada de la siguiente manera:
> - **Frontend**: Next.js 16 con React 19 y Tailwind CSS 4, alojado en **Vercel** (`/frontend`).
> - **Persistencia**: Base de datos Postgres en **Supabase**.
> - **Backend**: Orquestador multiagente serverless alojado en **Modal** (`/backend`).
>
> La información descrita a continuación se conserva únicamente por motivos de registro histórico y consistencia académica del Trabajo Fin de Grado.

---

# GitHub Pages - Frontend Estático (Legacy)

Este directorio contiene el frontend estático del proyecto Blogger Agent TFG, desplegado en GitHub Pages.

## :link: URL de Producción

**[https://alejandroors21.github.io/blogger-agent-tfg/](https://alejandroors21.github.io/blogger-agent-tfg/)**

## :file_folder: Estructura

```
docs/
├── index.html         # Página principal - lista de posts
├── post.html          # Template para posts individuales
├── posts.json         # Índice de posts generados
├── posts/             # Directorio de posts HTML
│   └── [slug].html    # Posts individuales
└── README.md          # Este archivo
```

## :gear: Tecnología

- **HTML5**: Estructura semántica
- **CSS**: Tailwind CSS vía CDN
- **JavaScript**: Vanilla JS para cargar posts dinámicamente
- **Deployment**: GitHub Pages automático

## :wrench: Desarrollo Local

Para servir los archivos localmente:

```bash
cd docs
python -m http.server 8000
# → http://localhost:8000
```

O con Node.js:

```bash
cd docs
npx http-server -p 8000
# → http://localhost:8000
```

## :art: Diseño

El diseño está inspirado en blogs modernos con:
- Tipografía clara y legible (Inter + Lora)
- Grid responsive para lista de posts
- Carga dinámica de contenido desde `posts.json`
- Sin dependencias de JavaScript externas

## :robot: Generación de Contenido

Los posts son generados automáticamente por el sistema de agentes de IA del backend:

1. El backend ejecuta el workflow Daggr con 7 agentes
2. El HTML Builder genera archivos HTML estáticos
3. Los archivos se guardan en `docs/` y `docs/posts/`
4. GitHub Pages sirve automáticamente el contenido actualizado

## :construction: Mantenimiento

Este directorio es gestionado automáticamente por el backend. **No edites manualmente** los archivos HTML generados, ya que serán sobrescritos en la próxima ejecución del workflow.

Archivos seguros para editar:
- `README.md` (este archivo)
- Estilos personalizados (si se agregan)

---

**Última actualización**: 17 de febrero de 2026  
**Repositorio**: [AlejandroRS21/blogger-agent-tfg](https://github.com/AlejandroRS21/blogger-agent-tfg)
