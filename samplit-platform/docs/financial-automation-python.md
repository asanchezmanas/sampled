# AUTOMATIZACIÓN FINANCIERA CON PYTHON - SAMPLIT

## 🎯 QUÉ SE PUEDE AUTOMATIZAR

### ✅ TOTALMENTE AUTOMATIZABLE:

**1. Tracking Automático:**
- MRR actual
- Churn rate
- New MRR
- Cash flow
- Runway
- Métricas SaaS

**2. Reportes Automáticos:**
- Dashboard financiero
- Email semanal con métricas
- Alertas (runway bajo, churn alto)

**3. Integraciones:**
- Stripe (pagos, suscripciones)
- Banco (transacciones via API)
- Google Sheets (sync automático)

**4. Proyecciones:**
- Revenue forecast
- Cash flow projection
- Burn rate trends

---

### ⚠️ NECESITA REVISIÓN HUMANA:

**1. Categorización Inteligente:**
- Gastos (marketing vs hosting vs salario)
- Ingresos (revenue vs deferred)

**2. Decisiones Estratégicas:**
- Cuándo levantar dinero
- Qué gastos cortar
- Pricing changes

**3. Compliance Legal:**
- Tax filings (hacer con contador)
- Legal reviews

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Stack Recomendado:

```
┌─────────────────────────────────────────┐
│         SOURCES (Data In)               │
├─────────────────────────────────────────┤
│  • Stripe API (subscriptions)           │
│  • Bank API (transactions)              │
│  • Your DB (users, plans)               │
│  • Manual entries (CSV upload)          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      PYTHON BACKEND (FastAPI)           │
├─────────────────────────────────────────┤
│  • Cron jobs (daily metrics)            │
│  • Webhooks (Stripe events)             │
│  • Calculations (MRR, churn, runway)    │
│  • Data storage (PostgreSQL)            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         OUTPUTS (Data Out)              │
├─────────────────────────────────────────┤
│  • Dashboard (React/Vue/HTML)           │
│  • Email alerts (SendGrid/SMTP)         │
│  • Google Sheets sync                   │
│  • CSV exports                          │
└─────────────────────────────────────────┘
```

---

## 📦 SETUP INICIAL

### 1. Instalar Dependencias

```bash
pip install stripe
pip install pandas
pip install sqlalchemy
pip install fastapi
pip install python-dotenv
pip install schedule
pip install gspread oauth2client  # Google Sheets
pip install plaid  # Bank integration
pip install sendgrid  # Emails
```

---

### 2. Estructura de Proyecto

```
samplit/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── finance.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   └── finance.py
│   ├── services/
│   │   ├── stripe_service.py
│   │   ├── metrics_calculator.py
│   │   └── alerts.py
│   └── cron/
│       └── daily_metrics.py
├── scripts/
│   ├── calculate_mrr.py
│   ├── sync_stripe.py
│   └── generate_reports.py
├── .env
└── requirements.txt
```

---

## 🔌 INTEGRACIÓN CON STRIPE

### services/stripe_service.py

```python
import stripe
from datetime import datetime, timedelta
from typing import List, Dict
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeService:
    """Servicio para interactuar con Stripe API"""
    
    def __init__(self):
        self.stripe = stripe
    
    def get_active_subscriptions(self) -> List[Dict]:
        """Obtiene todas las suscripciones activas"""
        subscriptions = []
        
        # Paginar resultados (Stripe limita a 100)
        has_more = True
        starting_after = None
        
        while has_more:
            params = {
                'status': 'active',
                'limit': 100
            }
            if starting_after:
                params['starting_after'] = starting_after
            
            response = stripe.Subscription.list(**params)
            subscriptions.extend(response.data)
            
            has_more = response.has_more
            if has_more:
                starting_after = response.data[-1].id
        
        return [self._parse_subscription(sub) for sub in subscriptions]
    
    def _parse_subscription(self, sub) -> Dict:
        """Parsea suscripción de Stripe a formato interno"""
        
        # Determinar si es mensual o anual
        interval = sub.items.data[0].price.recurring.interval
        amount = sub.items.data[0].price.unit_amount / 100  # Convertir de centavos
        
        # Calcular MRR
        if interval == 'month':
            mrr = amount
        elif interval == 'year':
            mrr = amount / 12
        else:
            mrr = 0
        
        return {
            'subscription_id': sub.id,
            'customer_id': sub.customer,
            'status': sub.status,
            'current_period_start': datetime.fromtimestamp(sub.current_period_start),
            'current_period_end': datetime.fromtimestamp(sub.current_period_end),
            'interval': interval,
            'amount': amount,
            'mrr': mrr,
            'created': datetime.fromtimestamp(sub.created)
        }
    
    def get_charges_for_period(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Obtiene todos los cobros (charges) en un período"""
        charges = []
        
        has_more = True
        starting_after = None
        
        while has_more:
            params = {
                'created': {
                    'gte': int(start_date.timestamp()),
                    'lte': int(end_date.timestamp())
                },
                'limit': 100
            }
            if starting_after:
                params['starting_after'] = starting_after
            
            response = stripe.Charge.list(**params)
            charges.extend(response.data)
            
            has_more = response.has_more
            if has_more:
                starting_after = response.data[-1].id
        
        return [self._parse_charge(charge) for charge in charges if charge.paid]
    
    def _parse_charge(self, charge) -> Dict:
        """Parsea charge de Stripe"""
        return {
            'charge_id': charge.id,
            'amount': charge.amount / 100,
            'currency': charge.currency,
            'customer_id': charge.customer,
            'created': datetime.fromtimestamp(charge.created),
            'description': charge.description,
            'fee': self._calculate_fee(charge)
        }
    
    def _calculate_fee(self, charge) -> float:
        """Calcula fee de Stripe (si disponible en balance transaction)"""
        if hasattr(charge, 'balance_transaction'):
            bt = stripe.BalanceTransaction.retrieve(charge.balance_transaction)
            return bt.fee / 100
        return charge.amount * 0.029 + 0.30  # Estimación: 2.9% + €0.30
    
    def get_canceled_subscriptions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Obtiene suscripciones canceladas en un período"""
        # Stripe no tiene filtro directo por fecha de cancelación
        # Necesitas mantener esto en tu DB con webhooks
        
        events = stripe.Event.list(
            type='customer.subscription.deleted',
            created={
                'gte': int(start_date.timestamp()),
                'lte': int(end_date.timestamp())
            }
        )
        
        return [event.data.object for event in events.data]

# Uso:
# service = StripeService()
# active_subs = service.get_active_subscriptions()
```

---

## 📊 CÁLCULO DE MÉTRICAS

### services/metrics_calculator.py

```python
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from decimal import Decimal

class MetricsCalculator:
    """Calcula todas las métricas financieras"""
    
    def __init__(self, db: Session, stripe_service):
        self.db = db
        self.stripe = stripe_service
    
    def calculate_mrr(self) -> Dict:
        """Calcula MRR actual y breakdown"""
        
        active_subs = self.stripe.get_active_subscriptions()
        
        total_mrr = sum(sub['mrr'] for sub in active_subs)
        
        # Breakdown por plan
        by_plan = {}
        for sub in active_subs:
            plan = sub['interval']
            if plan not in by_plan:
                by_plan[plan] = {'count': 0, 'mrr': 0}
            by_plan[plan]['count'] += 1
            by_plan[plan]['mrr'] += sub['mrr']
        
        return {
            'total_mrr': round(total_mrr, 2),
            'total_customers': len(active_subs),
            'by_plan': by_plan,
            'arr': round(total_mrr * 12, 2),
            'calculated_at': datetime.utcnow()
        }
    
    def calculate_churn_rate(self, period_days: int = 30) -> Dict:
        """Calcula churn rate para un período"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Clientes al inicio del período
        customers_start = self._get_customer_count_at_date(start_date)
        
        # Cancelaciones en el período
        canceled = self.stripe.get_canceled_subscriptions(start_date, end_date)
        canceled_count = len(canceled)
        
        # Churn rate
        if customers_start > 0:
            churn_rate = (canceled_count / customers_start) * 100
        else:
            churn_rate = 0
        
        # MRR churn
        mrr_start = self._get_mrr_at_date(start_date)
        mrr_lost = sum(self._get_subscription_mrr(sub) for sub in canceled)
        
        if mrr_start > 0:
            mrr_churn_rate = (mrr_lost / mrr_start) * 100
        else:
            mrr_churn_rate = 0
        
        return {
            'period_days': period_days,
            'customers_start': customers_start,
            'customers_canceled': canceled_count,
            'customer_churn_rate': round(churn_rate, 2),
            'mrr_start': round(mrr_start, 2),
            'mrr_lost': round(mrr_lost, 2),
            'mrr_churn_rate': round(mrr_churn_rate, 2)
        }
    
    def calculate_cash_flow(self, month: int = None, year: int = None) -> Dict:
        """Calcula cash flow para un mes específico"""
        
        if not month or not year:
            now = datetime.utcnow()
            month = now.month
            year = now.year
        
        # Primer y último día del mes
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # CASH IN (cobros reales en Stripe)
        charges = self.stripe.get_charges_for_period(start_date, end_date)
        cash_in = sum(charge['amount'] for charge in charges)
        stripe_fees = sum(charge['fee'] for charge in charges)
        
        # CASH OUT (de tu base de datos de gastos)
        expenses = self._get_expenses_for_period(start_date, end_date)
        cash_out = sum(exp['amount'] for exp in expenses)
        
        net_cash_flow = cash_in - stripe_fees - cash_out
        
        return {
            'month': month,
            'year': year,
            'cash_in': round(cash_in, 2),
            'stripe_fees': round(stripe_fees, 2),
            'cash_out': round(cash_out, 2),
            'net_cash_flow': round(net_cash_flow, 2),
            'by_category': self._group_expenses_by_category(expenses)
        }
    
    def calculate_runway(self) -> Dict:
        """Calcula runway actual"""
        
        # Cash actual (de tu banco o balance)
        current_cash = self._get_current_cash_balance()
        
        # Calcular burn rate promedio últimos 3 meses
        burn_rates = []
        for i in range(3):
            date = datetime.utcnow() - timedelta(days=30 * i)
            cf = self.calculate_cash_flow(date.month, date.year)
            burn_rates.append(cf['net_cash_flow'])
        
        avg_burn_rate = sum(burn_rates) / len(burn_rates)
        
        # Si estás ganando dinero, runway es infinito
        if avg_burn_rate >= 0:
            runway_months = float('inf')
        else:
            runway_months = current_cash / abs(avg_burn_rate)
        
        return {
            'current_cash': round(current_cash, 2),
            'avg_monthly_burn': round(avg_burn_rate, 2),
            'runway_months': round(runway_months, 1) if runway_months != float('inf') else 'infinite',
            'runway_days': round(runway_months * 30, 0) if runway_months != float('inf') else 'infinite',
            'calculated_at': datetime.utcnow()
        }
    
    def calculate_ltv(self) -> Dict:
        """Calcula LTV (Lifetime Value) promedio"""
        
        # Churn mensual
        churn = self.calculate_churn_rate(30)
        churn_rate = churn['customer_churn_rate'] / 100
        
        if churn_rate == 0:
            avg_lifetime_months = float('inf')
        else:
            avg_lifetime_months = 1 / churn_rate
        
        # ARPU (Average Revenue Per User)
        mrr_data = self.calculate_mrr()
        arpu = mrr_data['total_mrr'] / mrr_data['total_customers'] if mrr_data['total_customers'] > 0 else 0
        
        # LTV = ARPU × Average Lifetime
        ltv = arpu * avg_lifetime_months
        
        return {
            'arpu': round(arpu, 2),
            'avg_lifetime_months': round(avg_lifetime_months, 1) if avg_lifetime_months != float('inf') else 'infinite',
            'ltv': round(ltv, 2) if ltv != float('inf') else 'infinite'
        }
    
    def _get_customer_count_at_date(self, date: datetime) -> int:
        """Helper: cuenta clientes activos en una fecha"""
        # Implementar según tu DB
        pass
    
    def _get_mrr_at_date(self, date: datetime) -> float:
        """Helper: MRR en una fecha específica"""
        # Implementar según tu DB
        pass
    
    def _get_subscription_mrr(self, subscription) -> float:
        """Helper: calcula MRR de una suscripción"""
        # Implementar
        pass
    
    def _get_expenses_for_period(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Helper: obtiene gastos de tu DB"""
        # Implementar según tu modelo de expenses
        pass
    
    def _get_current_cash_balance(self) -> float:
        """Helper: obtiene cash actual del banco"""
        # Implementar (API banco o manual entry)
        pass
    
    def _group_expenses_by_category(self, expenses: List[Dict]) -> Dict:
        """Helper: agrupa gastos por categoría"""
        by_category = {}
        for exp in expenses:
            cat = exp.get('category', 'other')
            if cat not in by_category:
                by_category[cat] = 0
            by_category[cat] += exp['amount']
        return by_category
```

---

## 🤖 WEBHOOKS DE STRIPE

### api/routes/webhooks.py

```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import stripe
import os

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Recibe webhooks de Stripe para actualizar métricas en tiempo real"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle evento
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        # Actualizar métricas: nuevo cliente, MRR aumenta
        await handle_new_subscription(subscription)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        # Actualizar métricas: cambio de plan
        await handle_subscription_update(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Actualizar métricas: churn, MRR disminuye
        await handle_subscription_cancellation(subscription)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        # Registrar cash in
        await handle_payment_success(invoice)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        # Alerta: pago fallido
        await handle_payment_failure(invoice)
    
    return JSONResponse(content={"status": "success"})


async def handle_new_subscription(subscription):
    """Procesa nueva suscripción"""
    # Guardar en DB
    # Recalcular MRR
    # Enviar notificación
    pass

async def handle_subscription_update(subscription):
    """Procesa actualización de suscripción"""
    # Actualizar DB
    # Recalcular MRR si cambió plan
    pass

async def handle_subscription_cancellation(subscription):
    """Procesa cancelación"""
    # Marcar como cancelada
    # Recalcular churn
    # Enviar alerta si churn alto
    pass

async def handle_payment_success(invoice):
    """Procesa pago exitoso"""
    # Registrar cash in
    # Actualizar cash flow
    pass

async def handle_payment_failure(invoice):
    """Procesa pago fallido"""
    # Alerta al equipo
    # Email al cliente
    pass
```

---

## 📅 CRON JOBS (Tareas Programadas)

### cron/daily_metrics.py

```python
import schedule
import time
from datetime import datetime
from services.metrics_calculator import MetricsCalculator
from services.alerts import AlertService
from services.stripe_service import StripeService
from core.database import get_db

def calculate_and_store_daily_metrics():
    """Corre diariamente para calcular y guardar métricas"""
    
    print(f"[{datetime.utcnow()}] Calculating daily metrics...")
    
    db = next(get_db())
    stripe_service = StripeService()
    calculator = MetricsCalculator(db, stripe_service)
    alert_service = AlertService()
    
    # Calcular métricas
    mrr = calculator.calculate_mrr()
    churn = calculator.calculate_churn_rate(30)
    cash_flow = calculator.calculate_cash_flow()
    runway = calculator.calculate_runway()
    ltv = calculator.calculate_ltv()
    
    # Guardar en DB
    from models.finance import DailyMetrics
    
    metrics = DailyMetrics(
        date=datetime.utcnow().date(),
        mrr=mrr['total_mrr'],
        arr=mrr['arr'],
        customers=mrr['total_customers'],
        churn_rate=churn['customer_churn_rate'],
        mrr_churn_rate=churn['mrr_churn_rate'],
        cash_flow=cash_flow['net_cash_flow'],
        runway_months=runway['runway_months'] if runway['runway_months'] != 'infinite' else None,
        ltv=ltv['ltv'] if ltv['ltv'] != 'infinite' else None
    )
    
    db.add(metrics)
    db.commit()
    
    print(f"✅ Metrics saved: MRR={mrr['total_mrr']}, Runway={runway['runway_months']} months")
    
    # Revisar alertas
    check_alerts(calculator, alert_service)
    
    db.close()


def check_alerts(calculator, alert_service):
    """Revisa condiciones de alerta y envía notificaciones"""
    
    runway = calculator.calculate_runway()
    churn = calculator.calculate_churn_rate(30)
    
    # Alert: Runway crítico
    if runway['runway_months'] != 'infinite' and runway['runway_months'] < 3:
        alert_service.send_alert(
            level='CRITICAL',
            title='🚨 Runway Crítico',
            message=f'Solo quedan {runway["runway_months"]:.1f} meses de runway. Acción inmediata requerida.'
        )
    elif runway['runway_months'] != 'infinite' and runway['runway_months'] < 6:
        alert_service.send_alert(
            level='WARNING',
            title='⚠️ Runway Bajo',
            message=f'Runway: {runway["runway_months"]:.1f} meses. Considera opciones de financiamiento.'
        )
    
    # Alert: Churn alto
    if churn['customer_churn_rate'] > 10:
        alert_service.send_alert(
            level='WARNING',
            title='⚠️ Churn Alto',
            message=f'Churn rate: {churn["customer_churn_rate"]:.1f}%. Investiga causas.'
        )


def send_weekly_report():
    """Envía reporte semanal por email"""
    
    print(f"[{datetime.utcnow()}] Sending weekly report...")
    
    db = next(get_db())
    stripe_service = StripeService()
    calculator = MetricsCalculator(db, stripe_service)
    
    # Calcular métricas
    mrr = calculator.calculate_mrr()
    churn = calculator.calculate_churn_rate(30)
    runway = calculator.calculate_runway()
    
    # Generar email
    from services.email_service import EmailService
    email_service = EmailService()
    
    html_content = f"""
    <h2>📊 Weekly Financial Report</h2>
    
    <h3>Key Metrics:</h3>
    <ul>
        <li><strong>MRR:</strong> €{mrr['total_mrr']:,.2f}</li>
        <li><strong>ARR:</strong> €{mrr['arr']:,.2f}</li>
        <li><strong>Customers:</strong> {mrr['total_customers']}</li>
        <li><strong>Churn Rate:</strong> {churn['customer_churn_rate']:.1f}%</li>
        <li><strong>Runway:</strong> {runway['runway_months']} months</li>
    </ul>
    
    <p>Full dashboard: <a href="https://samplit.com/admin/finance">View Dashboard</a></p>
    """
    
    email_service.send_email(
        to=os.getenv("FOUNDER_EMAIL"),
        subject=f"📊 Weekly Financial Report - {datetime.utcnow().strftime('%Y-%m-%d')}",
        html=html_content
    )
    
    print("✅ Weekly report sent")
    
    db.close()


# Schedule jobs
schedule.every().day.at("08:00").do(calculate_and_store_daily_metrics)
schedule.every().monday.at("09:00").do(send_weekly_report)

if __name__ == "__main__":
    print("🤖 Starting financial cron jobs...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

---

## 🚨 SISTEMA DE ALERTAS

### services/alerts.py

```python
from typing import Literal
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

AlertLevel = Literal['INFO', 'WARNING', 'CRITICAL']

class AlertService:
    """Servicio para enviar alertas por email/Slack"""
    
    def __init__(self):
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY")
        self.founder_email = os.getenv("FOUNDER_EMAIL")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")  # Opcional
    
    def send_alert(self, level: AlertLevel, title: str, message: str):
        """Envía alerta por email (y opcionalmente Slack)"""
        
        # Email
        self._send_email_alert(level, title, message)
        
        # Slack (opcional)
        if self.slack_webhook and level in ['WARNING', 'CRITICAL']:
            self._send_slack_alert(level, title, message)
    
    def _send_email_alert(self, level: AlertLevel, title: str, message: str):
        """Envía email con alerta"""
        
        # Color según nivel
        colors = {
            'INFO': '#3498db',
            'WARNING': '#f39c12',
            'CRITICAL': '#e74c3c'
        }
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif;">
            <div style="background-color: {colors[level]}; color: white; padding: 15px;">
                <h2>{title}</h2>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa;">
                <p style="font-size: 16px;">{message}</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    Alert triggered at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                </p>
                <p>
                    <a href="https://samplit.com/admin/finance" style="
                        background-color: {colors[level]};
                        color: white;
                        padding: 10px 20px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                    ">View Dashboard</a>
                </p>
            </div>
        </div>
        """
        
        message = Mail(
            from_email='alerts@samplit.com',
            to_emails=self.founder_email,
            subject=f'[{level}] {title}',
            html_content=html_content
        )
        
        try:
            sg = SendGridAPIClient(self.sendgrid_key)
            response = sg.send(message)
            print(f"✅ Alert email sent: {title}")
        except Exception as e:
            print(f"❌ Failed to send alert email: {e}")
    
    def _send_slack_alert(self, level: AlertLevel, title: str, message: str):
        """Envía alerta a Slack"""
        import requests
        
        # Emoji según nivel
        emojis = {
            'WARNING': ':warning:',
            'CRITICAL': ':rotating_light:'
        }
        
        payload = {
            "text": f"{emojis.get(level, '')} *{title}*\n{message}"
        }
        
        try:
            requests.post(self.slack_webhook, json=payload)
            print(f"✅ Slack alert sent: {title}")
        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")
```

---

## 📈 DASHBOARD API

### api/routes/finance.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.metrics_calculator import MetricsCalculator
from services.stripe_service import StripeService

router = APIRouter(prefix="/api/finance", tags=["finance"])

@router.get("/metrics/current")
async def get_current_metrics(db: Session = Depends(get_db)):
    """Obtiene métricas actuales"""
    
    stripe_service = StripeService()
    calculator = MetricsCalculator(db, stripe_service)
    
    return {
        "mrr": calculator.calculate_mrr(),
        "churn": calculator.calculate_churn_rate(30),
        "runway": calculator.calculate_runway(),
        "ltv": calculator.calculate_ltv()
    }

@router.get("/cash-flow/{year}/{month}")
async def get_cash_flow(year: int, month: int, db: Session = Depends(get_db)):
    """Obtiene cash flow de un mes específico"""
    
    stripe_service = StripeService()
    calculator = MetricsCalculator(db, stripe_service)
    
    return calculator.calculate_cash_flow(month, year)

@router.get("/trends")
async def get_trends(db: Session = Depends(get_db), days: int = 90):
    """Obtiene tendencias de métricas (últimos N días)"""
    
    from models.finance import DailyMetrics
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    metrics = db.query(DailyMetrics)\
        .filter(DailyMetrics.date >= start_date.date())\
        .order_by(DailyMetrics.date.asc())\
        .all()
    
    return {
        "dates": [m.date.isoformat() for m in metrics],
        "mrr": [float(m.mrr) for m in metrics],
        "customers": [m.customers for m in metrics],
        "churn_rate": [float(m.churn_rate) for m in metrics],
        "cash_flow": [float(m.cash_flow) for m in metrics]
    }

@router.get("/forecast")
async def get_forecast(db: Session = Depends(get_db), months: int = 12):
    """Proyección financiera simple"""
    
    stripe_service = StripeService()
    calculator = MetricsCalculator(db, stripe_service)
    
    current_mrr = calculator.calculate_mrr()['total_mrr']
    churn_rate = calculator.calculate_churn_rate(30)['customer_churn_rate'] / 100
    
    # Asumiendo crecimiento de nuevos clientes constante
    avg_new_mrr = 500  # Ajusta según tu histórico
    
    forecast = []
    mrr = current_mrr
    
    for month in range(1, months + 1):
        # MRR next month = MRR current - (MRR * churn) + new MRR
        mrr_lost = mrr * churn_rate
        mrr = mrr - mrr_lost + avg_new_mrr
        
        forecast.append({
            "month": month,
            "mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2)
        })
    
    return {
        "forecast": forecast,
        "assumptions": {
            "starting_mrr": current_mrr,
            "monthly_churn_rate": churn_rate,
            "avg_new_mrr_per_month": avg_new_mrr
        }
    }
```

---

## 📊 MODELOS DE BASE DE DATOS

### models/finance.py

```python
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Enum
from sqlalchemy.sql import func
from core.database import Base
import enum

class ExpenseCategory(str, enum.Enum):
    HOSTING = "hosting"
    SOFTWARE = "software"
    MARKETING = "marketing"
    SALARY = "salary"
    LEGAL = "legal"
    OTHER = "other"

class DailyMetrics(Base):
    """Snapshot diario de métricas"""
    __tablename__ = "daily_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    
    # Revenue metrics
    mrr = Column(Float, nullable=False)
    arr = Column(Float, nullable=False)
    customers = Column(Integer, nullable=False)
    
    # Churn metrics
    churn_rate = Column(Float)  # %
    mrr_churn_rate = Column(Float)  # %
    
    # Cash metrics
    cash_flow = Column(Float)
    runway_months = Column(Float, nullable=True)
    
    # Customer metrics
    ltv = Column(Float, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

class Expense(Base):
    """Registro de gastos"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=False)
    description = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    receipt_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

class CashBalance(Base):
    """Saldo de cash (banco)"""
    __tablename__ = "cash_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    balance = Column(Float, nullable=False)
    bank_name = Column(String)
    
    created_at = Column(DateTime, server_default=func.now())
```

---

## 🚀 DEPLOYMENT & AUTOMATIZACIÓN

### Docker + Cron

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run cron jobs
CMD ["python", "cron/daily_metrics.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    env_file: .env
    depends_on:
      - db
  
  finance_cron:
    build: .
    command: python cron/daily_metrics.py
    env_file: .env
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: samplit
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 📲 SYNC CON GOOGLE SHEETS (Opcional)

### scripts/sync_to_sheets.py

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

class SheetsSync:
    """Sincroniza métricas con Google Sheets"""
    
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', scope)
        
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open("Samplit Finances").sheet1
    
    def update_metrics(self, metrics: dict):
        """Actualiza sheet con métricas actuales"""
        
        # Preparar datos
        row = [
            datetime.utcnow().strftime('%Y-%m-%d'),
            metrics['mrr'],
            metrics['customers'],
            metrics['churn_rate'],
            metrics['cash_flow'],
            metrics['runway_months']
        ]
        
        # Append row
        self.sheet.append_row(row)
        print("✅ Synced to Google Sheets")

# Uso:
# sync = SheetsSync()
# sync.update_metrics(metrics_dict)
```

---

## ⚙️ CONFIGURACIÓN

### .env

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Database
DATABASE_URL=postgresql://user:pass@localhost/samplit

# Email
SENDGRID_API_KEY=SG...
FOUNDER_EMAIL=you@samplit.com

# Slack (opcional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Google Sheets (opcional)
GOOGLE_SHEETS_CREDENTIALS=credentials.json
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Setup Básico (Semana 1)
- [ ] Instalar dependencias
- [ ] Crear modelos DB (DailyMetrics, Expense, CashBalance)
- [ ] Implementar StripeService
- [ ] Webhook de Stripe configurado

### Fase 2: Cálculos (Semana 2)
- [ ] MetricsCalculator completo
- [ ] calculate_mrr()
- [ ] calculate_churn_rate()
- [ ] calculate_cash_flow()
- [ ] calculate_runway()

### Fase 3: Automatización (Semana 3)
- [ ] Cron job diario
- [ ] Sistema de alertas
- [ ] Email semanal

### Fase 4: Dashboard (Semana 4)
- [ ] API endpoints
- [ ] Frontend básico (React/Vue/HTML)
- [ ] Gráficos (Chart.js/Recharts)

---

## 💡 TIPS & BEST PRACTICES

### 1. Empezar Simple
```python
# Fase 1: Manual pero automatizado
# - Stripe sync automático
# - Gastos manuales (pero trackados)
# - Métricas calculadas automáticamente

# Fase 2: Más integraciones
# - Bank API
# - Google Sheets sync
# - Más alertas

# Fase 3: ML/Predictivo
# - Forecast con ML
# - Anomaly detection
# - Recomendaciones automáticas
```

### 2. Validar Datos
```python
# Siempre cross-check contra Stripe dashboard
assert calculated_mrr == stripe_dashboard_mrr, "MRR mismatch!"
```

### 3. Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"MRR calculated: {mrr}")
logger.warning(f"Churn high: {churn_rate}%")
logger.error(f"Failed to calculate runway: {error}")
```

### 4. Testing
```python
# Test con datos fake antes de producción
def test_mrr_calculation():
    fake_subs = [...]
    mrr = calculate_mrr(fake_subs)
    assert mrr == expected_value
```

---

## 🎯 RESULTADO FINAL

Con este sistema automatizado:

**✅ Tendrás:**
- Dashboard en vivo con todas las métricas
- Email semanal automático con números
- Alertas cuando runway < 6 meses
- Alertas cuando churn > 10%
- Histórico de métricas (trends)
- Proyecciones automáticas

**✅ Ahorras:**
- 5-10 horas/semana de cálculos manuales
- Errores humanos
- Susto de quedarte sin cash (alertas tempranas)

**✅ Ganas:**
- Visibilidad real-time de tu negocio
- Decisiones basadas en data
- Peace of mind

---

**¿Quieres que profundice en alguna parte específica?**

Por ejemplo:
- Código completo del dashboard frontend
- Integración con banco específico (API)
- Sistema de presupuestos y forecasting avanzado
- Export automático para contador

¡Dime y lo desarrollo! 🚀
