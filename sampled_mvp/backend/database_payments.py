# backend/database_payments.py
"""
Extensión de DatabaseManager para soportar sistema de pagos
Agregar estos métodos a la clase DatabaseManager existente
"""

async def _create_payment_tables(self):
    """
    Crear tablas para sistema de pagos (llamar desde _create_tables)
    """
    
    payment_schema = """
    -- Subscriptions table
    CREATE TABLE IF NOT EXISTS subscriptions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
        
        -- Plan info
        plan VARCHAR(20) NOT NULL DEFAULT 'free',
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        
        -- Stripe info
        stripe_customer_id VARCHAR(255),
        stripe_subscription_id VARCHAR(255),
        stripe_price_id VARCHAR(255),
        
        -- Billing cycle
        current_period_start TIMESTAMPTZ,
        current_period_end TIMESTAMPTZ,
        cancel_at_period_end BOOLEAN DEFAULT false,
        canceled_at TIMESTAMPTZ,
        
        -- Trial
        trial_start TIMESTAMPTZ,
        trial_end TIMESTAMPTZ,
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        
        CONSTRAINT valid_plan CHECK (plan IN ('free', 'starter', 'professional', 'enterprise')),
        CONSTRAINT valid_status CHECK (status IN ('active', 'canceled', 'past_due', 'trialing', 'incomplete'))
    );
    
    -- Usage tracking table
    CREATE TABLE IF NOT EXISTS usage_tracking (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        
        -- Resource type
        resource_type VARCHAR(50) NOT NULL,
        
        -- Counts
        count INTEGER DEFAULT 0,
        
        -- Period (for monthly limits)
        period_start TIMESTAMPTZ NOT NULL,
        period_end TIMESTAMPTZ NOT NULL,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        
        UNIQUE(user_id, resource_type, period_start)
    );
    
    -- Payment history table
    CREATE TABLE IF NOT EXISTS payment_history (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
        
        -- Stripe info
        stripe_payment_intent_id VARCHAR(255),
        stripe_invoice_id VARCHAR(255),
        
        -- Payment details
        amount DECIMAL(10,2) NOT NULL,
        currency VARCHAR(3) DEFAULT 'USD',
        status VARCHAR(20) NOT NULL,
        
        -- Metadata
        description TEXT,
        metadata JSONB DEFAULT '{}',
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        
        CONSTRAINT valid_payment_status CHECK (status IN ('succeeded', 'failed', 'pending', 'refunded'))
    );
    
    -- Invoices table
    CREATE TABLE IF NOT EXISTS invoices (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
        
        -- Stripe info
        stripe_invoice_id VARCHAR(255) UNIQUE,
        
        -- Invoice details
        amount_due DECIMAL(10,2) NOT NULL,
        amount_paid DECIMAL(10,2) DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'USD',
        status VARCHAR(20) NOT NULL,
        
        -- Dates
        invoice_date TIMESTAMPTZ NOT NULL,
        due_date TIMESTAMPTZ,
        paid_at TIMESTAMPTZ,
        
        -- Files
        invoice_pdf_url VARCHAR(500),
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        
        CONSTRAINT valid_invoice_status CHECK (status IN ('draft', 'open', 'paid', 'void', 'uncollectible'))
    );
    
    -- Índices
    CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
    CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);
    CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
    CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_period ON usage_tracking(user_id, period_start, period_end);
    CREATE INDEX IF NOT EXISTS idx_payment_history_user ON payment_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id);
    CREATE INDEX IF NOT EXISTS idx_invoices_stripe ON invoices(stripe_invoice_id);
    
    -- Trigger para updated_at
    DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
    CREATE TRIGGER update_subscriptions_updated_at 
        BEFORE UPDATE ON subscriptions 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
    DROP TRIGGER IF EXISTS update_usage_tracking_updated_at ON usage_tracking;
    CREATE TRIGGER update_usage_tracking_updated_at
        BEFORE UPDATE ON usage_tracking
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    
    async with self.pool.acquire() as conn:
        await conn.execute(payment_schema)
    
    self.logger.info("Payment tables created successfully")

# ===== MÉTODOS DE SUBSCRIPCIÓN =====

async def get_user_stripe_customer_id(self, user_id: str) -> Optional[str]:
    """Obtener Stripe customer ID del usuario"""
    async with self.pool.acquire() as conn:
        customer_id = await conn.fetchval(
            "SELECT stripe_customer_id FROM subscriptions WHERE user_id = $1",
            user_id
        )
    return customer_id

async def update_user_stripe_customer(self, user_id: str, customer_id: str) -> None:
    """Actualizar Stripe customer ID"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO subscriptions (user_id, stripe_customer_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET stripe_customer_id = $2
            """,
            user_id, customer_id
        )

async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Obtener usuario por ID"""
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name, created_at FROM users WHERE id = $1",
            user_id
        )
    return dict(row) if row else None

async def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Obtener suscripción del usuario"""
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM subscriptions WHERE user_id = $1
            """,
            user_id
        )
    return dict(row) if row else None

async def create_or_update_subscription(
    self,
    user_id: str,
    plan: str,
    status: str,
    stripe_subscription_id: str = None,
    stripe_customer_id: str = None,
    current_period_start: datetime = None,
    current_period_end: datetime = None,
    cancel_at_period_end: bool = False,
    trial_end: datetime = None
) -> None:
    """Crear o actualizar suscripción"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO subscriptions (
                user_id, plan, status, stripe_subscription_id, stripe_customer_id,
                current_period_start, current_period_end, cancel_at_period_end, trial_end
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = $2, status = $3, stripe_subscription_id = $4,
                stripe_customer_id = $5, current_period_start = $6,
                current_period_end = $7, cancel_at_period_end = $8, trial_end = $9
            """,
            user_id, plan, status, stripe_subscription_id, stripe_customer_id,
            current_period_start, current_period_end, cancel_at_period_end, trial_end
        )

async def update_subscription_status(self, user_id: str, status: str) -> None:
    """Actualizar estado de suscripción"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            "UPDATE subscriptions SET status = $1 WHERE user_id = $2",
            status, user_id
        )

async def update_subscription_plan(self, user_id: str, plan: str) -> None:
    """Actualizar plan de suscripción"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            "UPDATE subscriptions SET plan = $1 WHERE user_id = $2",
            plan, user_id
        )

async def update_subscription(
    self,
    user_id: str,
    status: str = None,
    current_period_end: datetime = None,
    cancel_at_period_end: bool = None
) -> None:
    """Actualizar campos específicos de suscripción"""
    updates = []
    params = []
    param_count = 1
    
    if status is not None:
        updates.append(f"status = ${param_count}")
        params.append(status)
        param_count += 1
    
    if current_period_end is not None:
        updates.append(f"current_period_end = ${param_count}")
        params.append(current_period_end)
        param_count += 1
    
    if cancel_at_period_end is not None:
        updates.append(f"cancel_at_period_end = ${param_count}")
        params.append(cancel_at_period_end)
        param_count += 1
    
    if not updates:
        return
    
    params.append(user_id)
    query = f"UPDATE subscriptions SET {', '.join(updates)} WHERE user_id = ${param_count}"
    
    async with self.pool.acquire() as conn:
        await conn.execute(query, *params)

async def update_subscription_status_by_stripe_id(
    self,
    stripe_subscription_id: str,
    status: str
) -> None:
    """Actualizar estado por Stripe subscription ID"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            "UPDATE subscriptions SET status = $1 WHERE stripe_subscription_id = $2",
            status, stripe_subscription_id
        )

async def update_subscription_last_payment(self, stripe_subscription_id: str) -> None:
    """Actualizar última fecha de pago"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE subscriptions 
            SET updated_at = NOW() 
            WHERE stripe_subscription_id = $1
            """,
            stripe_subscription_id
        )

# ===== MÉTODOS DE USAGE TRACKING =====

async def get_user_resource_count(self, user_id: str, resource_type: str) -> int:
    """Obtener conteo de recurso del usuario"""
    async with self.pool.acquire() as conn:
        # Para recursos permanentes (experimentos, etc)
        if resource_type == 'experiments':
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM experiments WHERE user_id = $1",
                user_id
            )
        elif resource_type == 'team_members':
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM team_members WHERE user_id = $1",
                user_id
            ) or 1  # Al menos 1 (el owner)
        # Para recursos con límite mensual
        elif resource_type == 'api_calls_per_month':
            now = datetime.now(timezone.utc)
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            count = await conn.fetchval(
                """
                SELECT count FROM usage_tracking 
                WHERE user_id = $1 
                  AND resource_type = $2 
                  AND period_start = $3
                """,
                user_id, resource_type, period_start
            ) or 0
        elif resource_type == 'monthly_visitors':
            now = datetime.now(timezone.utc)
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            count = await conn.fetchval(
                """
                SELECT COUNT(DISTINCT user_id) FROM assignments
                WHERE experiment_id IN (
                    SELECT id FROM experiments WHERE user_id = $1
                )
                AND assigned_at >= $2
                """,
                user_id, period_start
            ) or 0
        else:
            count = 0
        
        return count

async def increment_api_calls(self, user_id: str) -> int:
    """Incrementar contador de API calls y retornar total"""
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    async with self.pool.acquire() as conn:
        count = await conn.fetchval(
            """
            INSERT INTO usage_tracking (user_id, resource_type, count, period_start, period_end)
            VALUES ($1, 'api_calls_per_month', 1, $2, $3)
            ON CONFLICT (user_id, resource_type, period_start) DO UPDATE
            SET count = usage_tracking.count + 1
            RETURNING count
            """,
            user_id, period_start, period_end
        )
    
    return count

async def reset_monthly_usage(self, user_id: str) -> None:
    """Reset usage mensual (llamar al inicio de cada mes)"""
    now = datetime.now(timezone.utc)
    last_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    
    async with self.pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM usage_tracking 
            WHERE user_id = $1 
              AND period_start < $2
              AND resource_type LIKE '%_per_month'
            """,
            user_id, last_month_start
        )

# ===== MÉTODOS DE PAYMENT HISTORY =====

async def create_payment_record(
    self,
    user_id: str,
    subscription_id: str,
    stripe_payment_intent_id: str,
    amount: float,
    status: str,
    description: str = None
) -> str:
    """Crear registro de pago"""
    async with self.pool.acquire() as conn:
        payment_id = await conn.fetchval(
            """
            INSERT INTO payment_history 
            (user_id, subscription_id, stripe_payment_intent_id, amount, status, description)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            user_id, subscription_id, stripe_payment_intent_id, amount, status, description
        )
    
    return str(payment_id)

async def get_user_payment_history(
    self,
    user_id: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Obtener historial de pagos del usuario"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM payment_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
            """,
            user_id, limit
        )
    
    return [dict(row) for row in rows]

# ===== MÉTODOS DE INVOICES =====

async def create_invoice(
    self,
    user_id: str,
    subscription_id: str,
    stripe_invoice_id: str,
    amount_due: float,
    status: str,
    invoice_date: datetime
) -> str:
    """Crear factura"""
    async with self.pool.acquire() as conn:
        invoice_id = await conn.fetchval(
            """
            INSERT INTO invoices 
            (user_id, subscription_id, stripe_invoice_id, amount_due, status, invoice_date)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            user_id, subscription_id, stripe_invoice_id, amount_due, status, invoice_date
        )
    
    return str(invoice_id)

async def get_user_invoices(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Obtener facturas del usuario"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM invoices 
            WHERE user_id = $1 
            ORDER BY invoice_date DESC 
            LIMIT $2
            """,
            user_id, limit
        )
    
    return [dict(row) for row in rows]

# ===== MÉTODOS DE ESTADÍSTICAS =====

async def get_subscription_stats(self) -> Dict[str, Any]:
    """Obtener estadísticas de suscripciones (admin)"""
    async with self.pool.acquire() as conn:
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) FILTER (WHERE plan = 'free') as free_users,
                COUNT(*) FILTER (WHERE plan = 'starter') as starter_users,
                COUNT(*) FILTER (WHERE plan = 'professional') as professional_users,
                COUNT(*) FILTER (WHERE plan = 'enterprise') as enterprise_users,
                COUNT(*) FILTER (WHERE status = 'active') as active_subscriptions,
                COUNT(*) FILTER (WHERE status = 'trialing') as trialing_subscriptions,
                COUNT(*) FILTER (WHERE status = 'past_due') as past_due_subscriptions,
                SUM(CASE 
                    WHEN plan = 'starter' THEN 29
                    WHEN plan = 'professional' THEN 99
                    WHEN plan = 'enterprise' THEN 299
                    ELSE 0
                END) as monthly_recurring_revenue
            FROM subscriptions
            """
        )
    
    return dict(stats) if stats else {}

async def get_churn_data(self, days: int = 30) -> Dict[str, Any]:
    """Obtener datos de churn"""
    async with self.pool.acquire() as conn:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) FILTER (WHERE canceled_at >= $1) as cancellations,
                COUNT(*) FILTER (WHERE created_at >= $1) as new_subscriptions,
                COUNT(*) FILTER (WHERE status = 'active') as total_active
            FROM subscriptions
            """,
            start_date
        )
    
    result = dict(stats) if stats else {}
    
    # Calcular churn rate
    if result.get('total_active', 0) > 0:
        result['churn_rate'] = result.get('cancellations', 0) / result['total_active']
    else:
        result['churn_rate'] = 0
    
    return result
