# Blogger Agent TFG — Frontend

Frontend Next.js 16 para el sistema multi-agente de IA que mimetiza estilos de escritura.

## Stack

- **Next.js 16.1** (App Router)
- **React 19**
- **TypeScript 5**
- **Tailwind CSS 4**

## Requisitos

- Node.js 22+
- npm 10+

## Instalacion

```bash
cd frontend
npm install
```

## Desarrollo

```bash
npm run dev
```

Abrir [http://localhost:3000](http://localhost:3000).

## Producción

```bash
npm run build
npm start
```

## 🚀 Deploy a Vercel

### Opción 1: Vercel Dashboard (recomendado)

1. Ir a [vercel.com](https://vercel.com) e importar el repo
2. En **Root Directory**, seleccionar `frontend`
3. Framework se autodetecta como **Next.js**
4. Agregar variables de entorno en **Environment Variables**:

| Variable | Valor |
|----------|-------|
| `USE_MOCK` | `true` (para demo) o `false` (con backend) |
| `BACKEND_URL` | URL del webhook Modal (si `USE_MOCK=false`) |
| `NEXT_PUBLIC_APP_NAME` | `Blogger Agent TFG` |
| `NEXT_PUBLIC_GITHUB_URL` | `https://github.com/AlejandroRS21/bloggeria` |

5. Clic **Deploy** 🚀

### Opción 2: Vercel CLI

```bash
cd frontend
npx vercel login
npx vercel --prod
```

### Build verificado

```
Route (app)
┌ ○ /                    Static
├ ○ /_not-found          Static
├ ƒ /api/generate-post   Dynamic (serverless)
├ ○ /generate            Static
└ ƒ /posts/[slug]        Dynamic (serverless)
```

## Modo Mock vs Real

Por defecto, la aplicacion opera en **modo mock** (no necesita backend). Para conectarse al backend real:

1. Editar `.env.local`:
   ```
   USE_MOCK=false
   BACKEND_URL=https://tu-app-modal.modal.run
   ```

2. La URL del backend es el endpoint de Modal donde corre el sistema multi-agente.

## Estructura

```
frontend/
├── app/
│   ├── layout.tsx           # Layout raiz con Header + Footer
│   ├── page.tsx             # Homepage
│   ├── globals.css          # Estilos globales Tailwind
│   ├── generate/
│   │   └── page.tsx         # Pagina de generacion
│   ├── posts/
│   │   └── [slug]/
│   │       └── page.tsx     # Vista de post individual
│   └── api/
│       └── generate-post/
│           └── route.ts     # API endpoint
├── components/
│   ├── Header.tsx
│   ├── Footer.tsx
│   ├── PostCard.tsx
│   ├── PostContent.tsx
│   └── GenerateForm.tsx
├── types/
│   └── post.ts              # Tipos TypeScript
├── lib/
│   └── api.ts               # Cliente API
├── .env.local
├── package.json
├── tsconfig.json
├── next.config.ts
└── postcss.config.mjs
```

## Variables de Entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `BACKEND_URL` | URL del backend Modal | `https://your-modal-app.modal.run` |
| `USE_MOCK` | Usar datos simulados | `true` |
| `NEXT_PUBLIC_APP_NAME` | Nombre de la app | Blogger Agent TFG |
| `NEXT_PUBLIC_APP_DESCRIPTION` | Descripcion | Sistema multi-agente... |
| `NEXT_PUBLIC_GITHUB_URL` | URL del repo | GitHub URL |
