Jinja Template → Carga JS → APIClient → Backend API → StateManager → UI Update

## 📄 PÁGINAS A CREAR + ARCHIVOS BACKEND

### 🌐 **1. PÚBLICAS (Sin autenticación)**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`home.html`** | Ninguno | Ninguno | Landing page pura |
| **`pricing.html`** | `/public-api/routers/subscriptions.py` (GET /plans) | Ninguno | Mostrar planes |
| **`features.html`** | Ninguno | Ninguno | Contenido estático |
| **`about.html`** | Ninguno | Ninguno | Contenido estático |
| **`contact.html`** | Ninguno | Form handler | Contacto simple |
| **`login.html`** | `/public-api/routers/auth.py` (POST /login) | `core/app.js` | Form → API |
| **`signup.html`** | `/public-api/routers/auth.py` (POST /register) | `core/app.js` | Form → API |
| **`forgot-password.html`** | `/public-api/routers/auth.py` | `core/app.js` | Reset password |

---

### 🏠 **2. DASHBOARD PRINCIPAL**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`dashboard.html`** | `/public-api/routers/analytics.py`<br>`/public-api/routers/experiments.py`<br>`/public-api/routers/subscriptions.py` | `managers/metrics-manager.js`<br>`components/charts.js` | Dashboard unificado con:<br>- Resumen de experimentos web<br>- Resumen de campañas email<br>- Resumen de ads<br>- Métricas en tiempo real<br>- Gráficas de conversión |

**Endpoints que consulta:**
```
GET /api/experiments?status=active
GET /api/analytics/summary
GET /api/subscriptions/usage
```

---

### 🧪 **3. WEB EXPERIMENTS (A/B Testing Web)**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`experiments/list.html`** | `/public-api/routers/experiments.py` (GET /experiments) | `managers/experiment-manager.js` | Lista con filtros y búsqueda |
| **`experiments/create.html`** | `/public-api/routers/experiments.py` (POST /experiments)<br>`/public-api/models/experiment_models.py` | `managers/experiment-manager.js` | Form para crear experimento multi-elemento |
| **`experiments/detail.html`** | `/public-api/routers/experiments.py` (GET /{id})<br>`/public-api/routers/analytics.py` (GET /{id}/analytics) | `managers/metrics-manager.js`<br>`components/charts.js` | Analytics detallado:<br>- Performance por variante<br>- Gráficas de conversión<br>- Bayesian insights<br>- Timeline |
| **`experiments/visual-editor.html`** ⭐ | `/public-api/routers/tracker.py` (GET /experiments)<br>Ninguno para el editor visual | **Custom JS:**<br>`visual-editor.js`<br>(Permite seleccionar elementos del DOM) | **CRÍTICO:**<br>Renderiza web del usuario en iframe<br>Permite seleccionar elementos<br>Guardar selectores CSS |

**Visual Editor Flow:**
```
1. Usuario ingresa URL
2. Se carga en iframe
3. JavaScript permite click en elementos
4. Guarda selector CSS + tipo de elemento
5. Usuario define variantes
6. POST /api/experiments con toda la config
```

---

### 📧 **4. EMAIL CAMPAIGNS**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`emails/list.html`** | `/public-api/routers/emails.py` (GET /campaigns) | Básico | Lista de campañas |
| **`emails/create.html`** | `/public-api/routers/emails.py` (POST /campaigns)<br>`/public-api/models/email_models.py` | Form builder | Form para crear campaña:<br>- Configuración básica<br>- Elementos a testear<br>- Variantes por elemento |
| **`emails/detail.html`** | `/public-api/routers/emails.py` (GET /{id}/analytics) | `components/charts.js` | Analytics:<br>- Open rate por variante<br>- Click rate<br>- Conversiones<br>- Thompson Sampling insights |
| **`emails/oauth-callback.html`** | `/public-api/routers/emails.py` (GET /integrations/callback) | Redirect handler | Procesa OAuth de Mailchimp/SendGrid |
| **`emails/connect.html`** | `/public-api/routers/emails.py` (POST /integrations/connect) | OAuth flow | Conectar plataforma email |

---

### 📊 **5. ADS CAMPAIGNS**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`ads/list.html`** | `/public-api/routers/ads.py` (GET /campaigns) | Básico | Lista de campañas ads |
| **`ads/create.html`** | `/public-api/routers/ads.py` (POST /campaigns)<br>`/public-api/models/ads_models.py` | Form builder | Crear campaña con múltiples creatives |
| **`ads/detail.html`** | `/public-api/routers/ads.py` (GET /{id}/analytics) | `components/charts.js` | Analytics:<br>- Performance por creative<br>- CTR, CPC, CPA<br>- Thompson Sampling probabilities<br>- Recomendaciones |
| **`ads/connect-meta.html`** | `/public-api/routers/ads.py` (POST /integrations/meta) | OAuth flow | Conectar Meta Ads |
| **`ads/connect-google.html`** | `/public-api/routers/ads.py` (POST /integrations/google) | OAuth flow | Conectar Google Ads |

---

### ⚙️ **6. SETTINGS (Configuración)**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`settings/profile.html`** | `/public-api/routers/auth.py` (GET /me, PATCH /me) | Form | Editar perfil |
| **`settings/billing.html`** | `/public-api/routers/subscriptions.py` | Stripe integration | Plan actual, usage, upgrade |
| **`settings/team.html`** | (No implementado aún) | Table + forms | Gestión de usuarios y roles |
| **`settings/integrations.html`** | `/public-api/routers/emails.py` (GET /integrations)<br>`/public-api/routers/ads.py` (GET /integrations) | OAuth buttons | Lista de integraciones conectadas |
| **`settings/installations.html`** | `/public-api/routers/installations.py` | Installation manager | Lista de sitios instalados |

---

### 📦 **7. INSTALACIONES (Setup de tracking)**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`installations/create.html`** | `/public-api/routers/installations.py` (POST /) | Form + code display | Wizard para crear instalación:<br>- Manual snippet<br>- WordPress plugin<br>- Proxy middleware |
| **`installations/detail.html`** | `/public-api/routers/installations.py` (GET /{id}/details) | Verification status | Ver detalles de instalación<br>Verificar que funciona |
| **`installations/verify.html`** | `/public-api/routers/installations.py` (POST /{id}/verify) | Verification flow | Verificar instalación |

---

### 📚 **8. DOCUMENTACIÓN/ONBOARDING**

| Página | Archivos Backend | Componentes JS | Notas |
|--------|------------------|----------------|-------|
| **`docs/getting-started.html`** | Ninguno | Ninguno | Guía de inicio |
| **`docs/web-setup.html`** | Ninguno | Code snippets | Cómo configurar web experiments |
| **`docs/email-setup.html`** | Ninguno | OAuth docs | Cómo configurar email optimization |
| **`docs/ads-setup.html`** | Ninguno | API docs | Cómo configurar ads optimization |
| **`onboarding/welcome.html`** | `/public-api/routers/auth.py` | Multi-step wizard | Wizard de onboarding para nuevos usuarios |

---

## 🧩 **9. COMPONENTES REUTILIZABLES (Jinja Partials)**

Estos son includes que usarás en múltiples páginas:
```
templates/
├── components/
│   ├── sidebar.html                 → Sidebar común a todas las páginas auth
│   ├── header.html                  → Header con user menu
│   ├── footer.html                  → Footer
│   ├── experiment-card.html         → Card para lista de experimentos
│   ├── campaign-card.html           → Card para lista de campañas
│   ├── stats-widget.html            → Widget de estadística (para dashboard)
│   ├── chart-line.html              → Gráfica de línea
│   ├── chart-bar.html               → Gráfica de barras
│   ├── modal.html                   → Modal genérico
│   ├── toast.html                   → Notificación toast
│   └── loading-overlay.html         → Overlay de carga
```

---

## 📊 **10. ESTRUCTURA DE CARPETAS PROPUESTA**
```
samplit-platform/
├── templates/
│   ├── base.html                    → Base template con <head>, scripts
│   ├── auth_base.html               → Base para páginas autenticadas (incluye sidebar)
│   │
│   ├── public/                      → Páginas públicas
│   │   ├── home.html
│   │   ├── pricing.html
│   │   ├── features.html
│   │   ├── about.html
│   │   ├── contact.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── forgot-password.html
│   │
│   ├── dashboard/
│   │   └── index.html               → Dashboard principal unificado
│   │
│   ├── experiments/                 → Web A/B Testing
│   │   ├── list.html
│   │   ├── create.html
│   │   ├── detail.html
│   │   └── visual-editor.html       ⭐ CRÍTICO
│   │
│   ├── emails/                      → Email campaigns
│   │   ├── list.html
│   │   ├── create.html
│   │   ├── detail.html
│   │   ├── connect.html
│   │   └── oauth-callback.html
│   │
│   ├── ads/                         → Ads campaigns
│   │   ├── list.html
│   │   ├── create.html
│   │   ├── detail.html
│   │   ├── connect-meta.html
│   │   └── connect-google.html
│   │
│   ├── settings/                    → Configuración
│   │   ├── profile.html
│   │   ├── billing.html
│   │   ├── team.html
│   │   ├── integrations.html
│   │   └── installations.html
│   │
│   ├── installations/               → Setup tracking
│   │   ├── create.html
│   │   ├── detail.html
│   │   └── verify.html
│   │
│   ├── docs/                        → Documentación
│   │   ├── getting-started.html
│   │   ├── web-setup.html
│   │   ├── email-setup.html
│   │   └── ads-setup.html
│   │
│   ├── onboarding/
│   │   └── welcome.html             → Wizard multi-step
│   │
│   └── components/                  → Componentes reutilizables
│       ├── sidebar.html
│       ├── header.html
│       ├── footer.html
│       ├── experiment-card.html
│       ├── campaign-card.html
│       ├── stats-widget.html
│       ├── chart-line.html
│       ├── chart-bar.html
│       ├── modal.html
│       ├── toast.html
│       └── loading-overlay.html
│
├── static/
│   ├── css/
│   │   └── tailwind.css             → Tailwind compilado
│   │
│   ├── js/
│   │   ├── core/                    → Ya tienes estos ✅
│   │   ├── managers/                → Ya tienes estos ✅
│   │   ├── components/              → Nuevos componentes específicos
│   │   │   ├── charts.js
│   │   │   ├── tables.js
│   │   │   └── visual-editor.js     ⭐ CRÍTICO
│   │   └── init.js                  → Ya tienes ✅
│   │
│   └── images/
│       └── logo.svg
