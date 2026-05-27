# ⚠️ OBSERVACIÓN IMPORTANTE: DOCUMENTO OBSOLETO (LEGACY)

> [!WARNING]
> **Este informe de coherencia documental corresponde a un estado técnico anterior del proyecto (donde se utilizaba una web estática en GitHub Pages).** Actualmente el ecosistema ha migrado a un modelo dinámico con:
> - **Frontend**: Next.js 16 (desplegado en **Vercel**).
> - **Persistencia**: Base de datos **Supabase**.
> - **Backend**: Orquestador serverless (desplegado en **Modal**).
> 
> La información de esta auditoría se conserva únicamente por valor histórico y registro académico.

---

# Coherence Report — Blogger Agent TFG

> Última revisión: mayo 2026

## Resumen General

- **Proyecto**: Sistema multi-agente para mimetizar estilo de bloggers, con generación de posts y persistencia dinámica en base de datos.
- **Stack principal**: Backend Python (orquestador en Modal), frontend en Next.js 16 (Vercel) y persistencia relacional en Supabase.
- **Estructura clave**: `backend/aphra_blogger` (llm providers, agentes, workflows), `backend/src/orchestrator` (orquestador 7 fases), `frontend/` (aplicación Next.js), `tests/` (~80 tests).

## Coherencia Resuelta (mayo 2026)

### ✅ Unificado: conteo de tests
- **Valor único**: ~80 tests (79 funciones test en 6 archivos)
- Actualizado en: README.md, backend/README.md, PROJECT_STATUS.md

### ✅ Unificado: número de agentes
- **Orquestador**: 6 agentes principales (StyleAnalyzer, KeywordExtractor, ContentGenerator, Critic, HTMLBuilder, ImageSelector)
- **Pipeline simplificado**: 3 agentes (StyleExtractor, NewsResearchAgent, ContentGenerator)
- **Total en código**: 8 agentes (incluye AnonymousBloggerEmulator y StyleExtractor legacy)
- Actualizado en todos los READMEs

### ✅ Unificado: URLs del repositorio
- **URL canónica**: `https://github.com/AlejandroRS21/blogger-agent-tfg`
- Actualizado en: README.md, pyproject.toml, AGENTS_GUIDE.md

### ✅ Resuelto: estado de Modal
- **Estado real**: Webhook productivo (`modal_app.py` + `llm_modal_host.py`) desplegado y funcional.
- Actualizado en: README.md, backend/README.md, PROJECT_STATUS.md

### ✅ Resuelto: frontend Next.js
- Tras ser desestimado a principios de año, el frontend fue completamente rediseñado y reconstruido utilizando Next.js 16, React 19 y Tailwind CSS 4, conectándolo directamente con Supabase y Modal.
- Desplegado exitosamente en Vercel.

---

## 🧭 Maintenance Checklist

- [ ] Verificar conteo de tests después de cada release y actualizar docs si cambia
- [ ] Validar que los enlaces a `project_docs/` sigan siendo correctos
- [ ] Confirmar estado de Modal después de pruebas en producción
- [ ] Mantener `.env.example` sincronizado con nuevas variables de entorno
- [ ] Revisar coherencia entre `requirements.txt` y `pyproject.toml` al agregar dependencias
