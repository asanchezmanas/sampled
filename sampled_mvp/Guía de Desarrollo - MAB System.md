# Guía de Desarrollo - MAB System

## Tabla de Contenidos
1. [Arquitectura General](#arquitectura-general)
2. [Añadir Nueva Funcionalidad](#añadir-nueva-funcionalidad)
3. [Crear Nueva Página](#crear-nueva-página)
4. [Modificar API Existente](#modificar-api-existente)
5. [Añadir Nuevos Servicios](#añadir-nuevos-servicios)
6. [Casos de Uso Específicos](#casos-de-uso-específicos)
7. [Testing y Debugging](#testing-y-debugging)
8. [Deployment](#deployment)

---

## Arquitectura General

### Estructura del Proyecto
```
sampled_mvp/
├── backend/
│   ├── main.py              # FastAPI app + rutas HTML
│   ├── database.py          # Gestión de base de datos
│   ├── auth.py              # Autenticación JWT
│   ├── models.py            # Modelos Pydantic
│   ├── thompson.py          # Algoritmo Thompson Sampling
│   ├── utils.py             # Utilidades generales
│   │
│   ├── static/              # Archivos estáticos (CSS/JS)
│   │   ├── css/
│   │   │   └── main.css     # Todos los estilos
│   │   └── js/
│   │       ├── core/        # JavaScript base
│   │       │   ├── app.js   # Aplicación principal
│   │       │   ├── state.js # Manejo de estado
│   │       │   ├── api.js   # Cliente HTTP
│   │       │   └── utils.js # Utilidades JS
│   │       └── pages/       # JS específico por página
│   │           ├── Dashboard.js
│   │           ├── Experiments.js
│   │           └── Analytics.js
│   │
│   └── templates/           # Templates HTML (Jinja2)
│       ├── base.html        # Layout base
│       └── pages/           # Páginas específicas
│           ├── dashboard.html
│           ├── experiments.html
│           └── analytics.html
│
├── migrations/              # Migraciones de DB
└── docker-compose.yml       # Configuración Docker
```

### Flujo de Datos
```
User Request → FastAPI → Database → Template → HTML + Data → Browser → JavaScript → Interactive UI
```

---

## Añadir Nueva Funcionalidad

### Metodología: Feature-First Development

Para cualquier nueva funcionalidad, sigue este orden:

#### 1. Definir la Funcionalidad
- ¿Qué problema resuelve?
- ¿Qué datos necesita?
- ¿Cómo interactúa el usuario?

#### 2. Backend First (Base de Datos → API → Template)
1. **Modificar base de datos** (`database.py`)
2. **Crear/modificar modelos** (`models.py`)
3. **Añadir endpoints API** (`main.py`)
4. **Crear template HTML** (`templates/`)

#### 3. Frontend Second (Estilos → Interactividad)
1. **Añadir estilos** (`static/css/main.css`)
2. **Crear JavaScript** (`static/js/pages/`)
3. **Conectar con API** (`static/js/core/api.js`)

---

## Crear Nueva Página

### Ejemplo: Página de "Team Management"

#### Paso 1: Crear el Template HTML
**Archivo**: `backend/templates/pages/team.html`
```html
{% extends "base.html" %}

{% block title %}Team Management - MAB System{% endblock %}

{% block breadcrumb %}
<div class="flex items-center gap-2 text-sm">
    <a href="/" class="text-gray-500 hover:text-gray-700">Dashboard</a>
    <svg class="w-4 h-4 text-gray-400"><!-- icon --></svg>
    <span class="text-gray-900 font-medium">Team</span>
</div>
{% endblock %}

{% block content %}
<div class="mb-8">
    <h1 class="text-2xl font-bold text-gray-900">Team Management</h1>
    <p class="text-gray-600 mt-1">Manage team members and permissions</p>
</div>

<!-- Tu contenido específico aquí -->
<div class="card">
    <div class="card-body">
        <!-- Lista de miembros del equipo -->
        {% for member in initial_data.team_members %}
            <div class="team-member" data-member-id="{{ member.id }}">
                {{ member.name }}
            </div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="/static/js/pages/Team.js"></script>
<script>
    function initializePage() {
        if (typeof TeamPage !== 'undefined') {
            window.teamPage = new TeamPage();
        }
    }
</script>
{% endblock %}
```

#### Paso 2: Añadir Ruta en FastAPI
**Archivo**: `backend/main.py` (añadir estas funciones)
```python
@app.get("/team", response_class=HTMLResponse)
async def team_page(request: Request):
    user = await get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Obtener datos iniciales
    team_members = await db.get_team_members(user['id'])
    initial_data = {
        'team_members': team_members
    }
    
    return templates.TemplateResponse("pages/team.html", {
        "request": request,
        "user": user,
        "initial_data": initial_data,
        "csrf_token": csrf_token
    })

# API endpoints
@app.get("/api/team/members")
async def get_team_members(user_id: str = Depends(get_current_user)):
    members = await db.get_team_members(user_id)
    return {"success": True, "data": members}

@app.post("/api/team/members")
async def add_team_member(request: AddMemberRequest, user_id: str = Depends(get_current_user)):
    member_id = await db.add_team_member(user_id, request.email, request.role)
    return {"success": True, "member_id": member_id}
```

#### Paso 3: Añadir Métodos a Database
**Archivo**: `backend/database.py` (añadir estos métodos)
```python
async def get_team_members(self, user_id: str) -> List[Dict[str, Any]]:
    """Get team members for user"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, email, name, role, created_at 
            FROM team_members 
            WHERE team_owner_id = $1
            ORDER BY created_at DESC
        """, user_id)
    return [dict(row) for row in rows]

async def add_team_member(self, owner_id: str, email: str, role: str) -> str:
    """Add new team member"""
    async with self.pool.acquire() as conn:
        member_id = await conn.fetchval("""
            INSERT INTO team_members (team_owner_id, email, role)
            VALUES ($1, $2, $3)
            RETURNING id
        """, owner_id, email, role)
    return str(member_id)
```

#### Paso 4: Crear Modelos Pydantic
**Archivo**: `backend/models.py` (añadir estos modelos)
```python
class AddMemberRequest(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: str = Field(..., regex=r'^(admin|editor|viewer)$')

class TeamMemberResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    created_at: datetime
```

#### Paso 5: Crear JavaScript de Página
**Archivo**: `backend/static/js/pages/Team.js`
```javascript
class TeamPage {
    constructor() {
        this.app = window.MAB;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        console.log('Team page initialized');
    }
    
    setupEventListeners() {
        // Manejar clicks en botones de invitar
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="invite-member"]')) {
                this.showInviteModal();
            }
        });
    }
    
    async inviteMember(email, role) {
        try {
            this.app.showLoading(true);
            const response = await this.app.api.post('/api/team/members', {
                email, role
            });
            
            if (response.success) {
                this.app.showToast('Member invited successfully!', 'success');
                this.refreshMembersList();
            }
        } catch (error) {
            this.app.handleAPIError(error);
        } finally {
            this.app.showLoading(false);
        }
    }
}

window.TeamPage = TeamPage;
```

#### Paso 6: Añadir Enlace en Navegación
**Archivo**: `backend/templates/base.html` (modificar la navegación)
```html
<a href="/team" class="menu-item {% if '/team' in request.url.path %}active{% endif %}">
    <svg class="menu-item-icon"><!-- team icon --></svg>
    <span class="menu-item-text">Team</span>
</a>
```

---

## Modificar API Existente

### Ejemplo: Añadir filtros avanzados a experimentos

#### Paso 1: Modificar el Endpoint
**Archivo**: `backend/main.py`
```python
@app.get("/api/experiments", response_model=List[ExperimentResponse])
async def get_experiments(
    user_id: str = Depends(get_current_user),
    status: Optional[str] = None,          # NUEVO: filtro por estado
    date_from: Optional[datetime] = None,  # NUEVO: filtro fecha desde
    date_to: Optional[datetime] = None,    # NUEVO: filtro fecha hasta
    search: Optional[str] = None           # NUEVO: búsqueda por nombre
):
    try:
        experiments = await db.get_user_experiments(
            user_id, status, date_from, date_to, search
        )
        return [ExperimentResponse(**exp) for exp in experiments]
    except Exception as e:
        logger.error(f"Failed to fetch experiments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch experiments")
```

#### Paso 2: Modificar Método de Database
**Archivo**: `backend/database.py`
```python
async def get_user_experiments(
    self, 
    user_id: str,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get experiments with filters"""
    
    # Construir query dinámicamente
    query = """
        SELECT e.id, e.name, e.description, e.status, e.created_at, e.started_at,
               COUNT(a.id) as arms_count,
               COALESCE(SUM(a.assignments), 0) as total_users
        FROM experiments e
        LEFT JOIN arms a ON e.id = a.experiment_id
        WHERE e.user_id = $1
    """
    params = [user_id]
    param_count = 1
    
    # Añadir filtros condicionalmente
    if status:
        param_count += 1
        query += f" AND e.status = ${param_count}"
        params.append(status)
    
    if date_from:
        param_count += 1
        query += f" AND e.created_at >= ${param_count}"
        params.append(date_from)
    
    if date_to:
        param_count += 1
        query += f" AND e.created_at <= ${param_count}"
        params.append(date_to)
    
    if search:
        param_count += 1
        query += f" AND e.name ILIKE ${param_count}"
        params.append(f"%{search}%")
    
    query += """
        GROUP BY e.id, e.name, e.description, e.status, e.created_at, e.started_at
        ORDER BY e.created_at DESC
    """
    
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    
    return [dict(row) for row in rows]
```

#### Paso 3: Actualizar JavaScript
**Archivo**: `backend/static/js/pages/Experiments.js`
```javascript
// Añadir método para usar nuevos filtros
async applyAdvancedFilters() {
    const filters = {
        status: this.filters.status,
        date_from: this.filters.dateFrom,
        date_to: this.filters.dateTo,
        search: this.filters.search
    };
    
    try {
        this.app.showLoading(true);
        const response = await this.app.api.get('/api/experiments', filters);
        
        if (response.success) {
            this.experiments = response.data;
            this.filteredExperiments = [...this.experiments];
            this.renderExperiments();
        }
    } catch (error) {
        this.app.handleAPIError(error);
    } finally {
        this.app.showLoading(false);
    }
}
```

---

## Añadir Nuevos Servicios

### Ejemplo: Sistema de Emails

#### Paso 1: Crear Servicio Email
**Archivo**: `backend/email_service.py` (NUEVO ARCHIVO)
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import os
from jinja2 import Template
from utils import Logger

class EmailService:
    def __init__(self):
        self.logger = Logger()
        self.smtp_server = os.environ.get("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        
    async def send_experiment_report(self, user_email: str, experiment_data: dict):
        """Send experiment results via email"""
        template = Template("""
        <h2>Experiment Results: {{ experiment.name }}</h2>
        <p>Status: {{ experiment.status }}</p>
        <p>Visitors: {{ experiment.total_visitors }}</p>
        <p>Conversion Rate: {{ experiment.conversion_rate }}%</p>
        """)
        
        html_content = template.render(experiment=experiment_data)
        
        await self._send_email(
            to_email=user_email,
            subject=f"Results for {experiment_data['name']}",
            html_content=html_content
        )
    
    async def _send_email(self, to_email: str, subject: str, html_content: str):
        """Internal method to send email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email sent to {to_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            raise
```

#### Paso 2: Integrar en Main.py
**Archivo**: `backend/main.py`
```python
# Añadir import
from email_service import EmailService

# Añadir al inicio con otros managers
email_service = EmailService()

# Añadir endpoint
@app.post("/api/experiments/{experiment_id}/send-report")
async def send_experiment_report(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    try:
        experiment = await db.get_experiment_with_arms(experiment_id, user_id)
        user = await db.get_user_by_id(user_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        await email_service.send_experiment_report(user['email'], experiment)
        
        return {"success": True, "message": "Report sent successfully"}
        
    except Exception as e:
        logger.error(f"Failed to send report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send report")
```

#### Paso 3: Añadir a Requirements
**Archivo**: `requirements.txt`
```txt
# Añadir estas líneas
jinja2>=3.0.0
smtplib
```

---

## Casos de Uso Específicos

### A. Añadir Sistema de Notificaciones

#### Archivos a Modificar/Crear:

1. **Database Schema** (crear migración):
```sql
-- migrations/002_notifications.sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

2. **Database Methods** (`database.py`):
```python
async def create_notification(self, user_id: str, type: str, title: str, message: str):
async def get_user_notifications(self, user_id: str, limit: int = 50):
async def mark_notification_read(self, notification_id: str):
```

3. **Models** (`models.py`):
```python
class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read_at: Optional[datetime]
    created_at: datetime
```

4. **API Endpoints** (`main.py`):
```python
@app.get("/api/notifications")
@app.post("/api/notifications/{notification_id}/read")
```

5. **Frontend Component** (`static/js/core/app.js`):
```javascript
// Añadir método para mostrar notificaciones
showNotifications() {
    // Lógica para mostrar panel de notificaciones
}
```

### B. Añadir Sistema de Roles y Permisos

#### Archivos a Modificar:

1. **Database Schema**:
```sql
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
CREATE TABLE permissions (...);
CREATE TABLE role_permissions (...);
```

2. **Auth System** (`auth.py`):
```python
def check_permission(self, user_role: str, required_permission: str) -> bool:
    # Lógica de permisos
```

3. **Middleware** (`main.py`):
```python
def require_permission(permission: str):
    def decorator(func):
        # Decorator para proteger endpoints
    return decorator
```

4. **Templates** (`base.html`):
```html
{% if user.role == 'admin' %}
    <!-- Mostrar opciones de admin -->
{% endif %}
```

### C. Añadir Integración con External API

#### Archivos a Crear/Modificar:

1. **Service Class** (`integrations/google_analytics.py`):
```python
class GoogleAnalyticsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def get_traffic_data(self, experiment_url: str):
        # Integración con GA API
```

2. **Configuration** (añadir a `main.py`):
```python
ga_service = GoogleAnalyticsService(os.environ.get("GA_API_KEY"))
```

3. **Database** (guardar datos de integración):
```python
async def save_ga_data(self, experiment_id: str, traffic_data: dict):
```

4. **Background Jobs** (`background_tasks.py`):
```python
async def sync_ga_data_task():
    # Tarea para sincronizar datos periódicamente
```

---

## Testing y Debugging

### Estructura de Tests
```
tests/
├── test_api.py          # Tests de API endpoints
├── test_database.py     # Tests de base de datos
├── test_auth.py         # Tests de autenticación
├── test_thompson.py     # Tests de algoritmo
└── frontend/
    ├── test_app.js      # Tests de JavaScript
    └── test_pages.js    # Tests de páginas específicas
```

### Debugging Frontend
```javascript
// En DevTools Console
MAB.state.getAll()           // Ver estado actual
MAB.api.get('/api/experiments') // Test API call
MAB.showToast('Test')        // Test notificaciones

// Para debug de componentes
window.experimentsPage.experiments  // Ver datos de página
```

### Debugging Backend
```python
# Logging en desarrollo
logger.debug("User data", user_id=user_id, action="create_experiment")

# Para inspeccionar requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    return response
```

---

## Deployment

### Variables de Entorno Nuevas
```bash
# Email service
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-password

# External APIs
GA_API_KEY=your-google-analytics-key
SENDGRID_API_KEY=your-sendgrid-key
```

### Build Process
```bash
# Para añadir nuevas dependencias
pip install new-package
pip freeze > requirements.txt

# Para nuevas migraciones
docker-compose exec web python -c "
import asyncio
from migrations.run_migration import run_migration
asyncio.run(run_migration('002_notifications.sql'))
"
```

### Checklist para Nueva Funcionalidad
- [ ] Tests unitarios escritos
- [ ] Database migration creada
- [ ] API documentada en README
- [ ] Frontend responsive
- [ ] Error handling implementado
- [ ] Logging añadido
- [ ] Variables de entorno documentadas
- [ ] Security review hecho

---

## Resumen: Flujo de Desarrollo

1. **Planificar**: Define la funcionalidad y sus requisitos
2. **Backend**: Database → Models → API → Template
3. **Frontend**: Styles → JavaScript → Integration
4. **Testing**: Unit tests → Integration tests → Manual testing
5. **Documentation**: Update README, add comments
6. **Deploy**: Environment variables → Migration → Release

Esta guía te permite escalar el proyecto de manera organizada, manteniendo la arquitectura consistente mientras añades nuevas funcionalidades.
