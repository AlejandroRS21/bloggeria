# Vercel Deployment - Frontend Next.js

Guía completa para desplegar el frontend de Next.js en Vercel.

## 📋 Índice

- [¿Por qué Vercel?](#por-qué-vercel)
- [Requisitos previos](#requisitos-previos)
- [Métodos de deployment](#métodos-de-deployment)
- [Configuración de variables de entorno](#configuración-de-variables-de-entorno)
- [Deployment automático con Git](#deployment-automático-con-git)
- [Dominios personalizados](#dominios-personalizados)
- [Troubleshooting](#troubleshooting)

## 🎯 ¿Por qué Vercel?

Vercel es la plataforma oficial de Next.js y ofrece:

- ✅ **Zero-config deployment** - Next.js funciona out-of-the-box
- ✅ **Edge Network global** - CDN automático para assets estáticos
- ✅ **Serverless Functions** - API routes de Next.js desplegadas como funciones
- ✅ **Preview deployments** - URL única para cada PR
- ✅ **Automatic HTTPS** - SSL gratuito para todos los dominios
- ✅ **Integración con GitHub** - Deployment automático en cada push
- ✅ **Analytics incorporado** - Monitoreo de performance sin configuración
- ✅ **Free tier generoso** - Perfecto para proyectos académicos

## 📦 Requisitos Previos

1. **Cuenta Vercel** (gratuita)
   - Regístrate en [vercel.com](https://vercel.com)
   - Conecta tu cuenta de GitHub

2. **Proyecto Next.js preparado**
   - Estructura `frontend/` con Next.js 14+
   - `package.json` configurado
   - Build exitoso localmente: `npm run build`

3. **Variables de entorno definidas**
   - URL del backend Modal
   - API keys necesarias

## 🚀 Métodos de Deployment

### Método 1: Vercel Dashboard (Recomendado)

1. **Conectar repositorio:**
   ```
   1. Ve a https://vercel.com/new
   2. Selecciona "Import Git Repository"
   3. Autoriza GitHub y selecciona "IES-Rafael-Alberti/blogger-agent-tfg"
   4. Vercel detectará automáticamente Next.js
   ```

2. **Configurar proyecto:**
   ```
   - Framework Preset: Next.js
   - Root Directory: frontend
   - Build Command: npm run build (auto-detectado)
   - Output Directory: .next (auto-detectado)
   ```

3. **Variables de entorno:**
   ```
   NEXT_PUBLIC_API_URL=https://tu-modal-endpoint.modal.run
   MODAL_WEBHOOK_URL=https://tu-modal-endpoint.modal.run/webhook
   ```

4. **Deploy:**
   - Click "Deploy"
   - Espera 1-2 minutos
   - ¡Listo! Tu app estará en `https://bloggeria-cf0iyl2bv-alejandrors21s-projects.vercel.app`

### Método 2: Vercel CLI

1. **Instalar Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Deploy desde el directorio frontend:**
   ```bash
   cd frontend
   vercel
   ```

4. **Deploy a producción:**
   ```bash
   vercel --prod
   ```

### Método 3: GitHub Integration (Automatic)

Una vez conectado el repositorio:

- **Push a `main`** → Deploy automático a producción
- **Push a otras ramas** → Preview deployment con URL única
- **Pull Request** → Preview deployment comentado automáticamente en el PR

## ⚙️ Configuración de Variables de Entorno

### En Vercel Dashboard:

1. Ve a tu proyecto en Vercel
2. Settings → Environment Variables
3. Agrega las siguientes variables:

```bash
# Backend Modal URL
NEXT_PUBLIC_API_URL=https://your-modal-app.modal.run

# Modal Webhook (usado en API routes)
MODAL_WEBHOOK_URL=https://your-modal-app.modal.run/webhook

# Opcional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### Variables públicas vs privadas:

- **`NEXT_PUBLIC_*`** - Expuestas al navegador (cliente)
- **Sin prefijo** - Solo disponibles en server-side (API routes)

### Configuración por entorno:

Puedes definir diferentes valores para:
- Production
- Preview
- Development

## 🔄 Deployment Automático con Git

### Configuración recomendada:

```yaml
# .github/workflows/vercel-preview.yml
name: Vercel Preview Deployment
on:
  pull_request:
    branches: [main, develop]
    paths:
      - 'frontend/**'

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: vercel/actions/cli@v1
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

### Branches strategy:

- **`main`** → Deploy a producción (`bloggeria-cf0iyl2bv-alejandrors21s-projects.vercel.app`)
- **`develop`** → Preview deployment (`blogger-agent-tfg-git-develop.vercel.app`)
- **Feature branches** → Preview deployments únicos

## 🌐 Dominios Personalizados

### Agregar dominio:

1. **En Vercel Dashboard:**
   ```
   Project → Settings → Domains → Add
   ```

2. **Configurar DNS:**
   ```
   Type: CNAME
   Name: www (o tu subdominio)
   Value: cname.vercel-dns.com
   ```

3. **Ejemplos:**
   - `blogger-agent.tudominio.com`
   - `blog-ai.ies-alberti.es`

### SSL automático:

Vercel configura HTTPS automáticamente en todos los dominios (incluye certificados Let's Encrypt).

## 📊 Monitoreo y Analytics

### Vercel Analytics (integrado):

```typescript
// frontend/app/layout.tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

### Speed Insights:

```bash
npm install @vercel/speed-insights
```

```typescript
import { SpeedInsights } from '@vercel/speed-insights/next'
```

## 🐛 Troubleshooting

### Error: "Build failed"

**Causa:** Errores de TypeScript o build de Next.js

**Solución:**
```bash
cd frontend
npm run build  # Probar localmente
npm run lint   # Verificar linting
```

### Error: "Environment variable not found"

**Causa:** Variables de entorno no configuradas en Vercel

**Solución:**
1. Vercel Dashboard → Settings → Environment Variables
2. Agregar las variables necesarias
3. Redeploy: Settings → Deployments → [último deploy] → "Redeploy"

### Error: "API route returns 500"

**Causa:** Backend Modal no responde o URL incorrecta

**Solución:**
1. Verificar que `MODAL_WEBHOOK_URL` esté correcta
2. Probar endpoint Modal directamente: `curl https://your-modal-app.modal.run/webhook`
3. Verificar logs en Modal dashboard

### Error: "Too Many Requests"

**Causa:** Límites de Vercel Free tier

**Solución:**
- Free tier: 100 GB bandwidth/mes
- Upgrade a Pro si necesitas más: $20/mes

### Builds lentos

**Optimización:**

```javascript
// next.config.js
module.exports = {
  // Cache de builds
  experimental: {
    outputFileTracingRoot: path.join(__dirname, '../../'),
  },
  
  // Excluir dependencias grandes del bundle
  webpack: (config) => {
    config.externals = [...config.externals, 'sharp']
    return config
  }
}
```

## 🔐 Seguridad

### Headers de seguridad:

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },
}
```

### CORS para API routes:

```typescript
// frontend/app/api/generate-post/route.ts
export async function POST(request: Request) {
  // Verificar origin si es necesario
  const origin = request.headers.get('origin')
  
  // Tu lógica aquí...
  
  const response = Response.json(data)
  response.headers.set('Access-Control-Allow-Origin', origin || '*')
  return response
}
```

## 📈 Escalabilidad

### Límites Free Tier:

- 100 GB bandwidth/mes
- 100 GB-Hrs serverless function execution
- 1000 imágenes optimizadas
- 6000 minutos de build time/mes

### Cuando escalar a Pro:

- Más de 10k visitas/mes
- Necesitas más previews simultáneos
- Equipos colaborativos (más seats)
- Analytics avanzado

## 🔗 Enlaces Útiles

- [Vercel Docs](https://vercel.com/docs)
- [Next.js on Vercel](https://vercel.com/docs/frameworks/nextjs)
- [Vercel CLI Reference](https://vercel.com/docs/cli)
- [Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Custom Domains](https://vercel.com/docs/projects/domains)

## ✅ Checklist Final

Antes de hacer deployment a producción:

- [ ] Build local exitoso (`npm run build`)
- [ ] Tests pasando (`npm test`)
- [ ] Variables de entorno configuradas en Vercel
- [ ] Backend Modal desplegado y funcionando
- [ ] API routes probadas
- [ ] Dominio configurado (opcional)
- [ ] Analytics configurado (opcional)
- [ ] README actualizado con URL de producción

---

**¿Problemas?** Abre un issue en GitHub o consulta la [documentación oficial de Vercel](https://vercel.com/docs).
