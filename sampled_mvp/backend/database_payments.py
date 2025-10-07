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

async def update_subscription_status
