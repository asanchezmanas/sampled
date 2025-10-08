-- ============================================
-- SAMPLIT PLATFORM - COMPLETE DATABASE SCHEMA
-- Para copiar/pegar en Supabase SQL Editor
-- ============================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- USERS
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- SUBSCRIPTIONS (Stripe)
-- ============================================

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

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_customer_id);

-- ============================================
-- EXPERIMENTS (Multi-elemento unificado)
-- ============================================

CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    url VARCHAR(500),
    
    -- Config
    traffic_allocation DECIMAL(3,2) DEFAULT 1.0,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.95,
    config JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived'))
);

CREATE INDEX idx_experiments_user ON experiments(user_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_url ON experiments(url);

-- ============================================
-- EXPERIMENT ELEMENTS
-- ============================================

CREATE TABLE IF NOT EXISTS experiment_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    element_order INTEGER NOT NULL DEFAULT 0,
    name VARCHAR(255) NOT NULL,
    
    -- Selector info
    selector_type VARCHAR(20) NOT NULL,
    selector_value VARCHAR(500) NOT NULL,
    fallback_selectors JSONB DEFAULT '[]',
    
    -- Element type
    element_type VARCHAR(50) NOT NULL,
    
    -- Original content
    original_content JSONB NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id, element_order)
);

CREATE INDEX idx_elements_experiment ON experiment_elements(experiment_id);

-- ============================================
-- ELEMENT VARIANTS
-- ============================================

CREATE TABLE IF NOT EXISTS element_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    element_id UUID NOT NULL REFERENCES experiment_elements(id) ON DELETE CASCADE,
    
    variant_order INTEGER NOT NULL DEFAULT 0,
    name VARCHAR(255),
    content JSONB NOT NULL,
    
    -- Stats (públicas)
    total_allocations INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(10,6) DEFAULT 0,
    
    -- Algorithm state (CIFRADO - para producción)
    algorithm_state BYTEA,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(element_id, variant_order)
);

CREATE INDEX idx_variants_element ON element_variants(element_id);

-- ============================================
-- ASSIGNMENTS
-- ============================================

CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- User info
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    
    -- Assignment (JSONB para multi-elemento)
    variant_assignments JSONB NOT NULL,
    
    -- Context
    context JSONB DEFAULT '{}',
    
    -- Conversion
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ,
    conversion_value DECIMAL(10,2) DEFAULT 0,
    
    UNIQUE(experiment_id, user_id)
);

CREATE INDEX idx_assignments_experiment ON assignments(experiment_id);
CREATE INDEX idx_assignments_user ON assignments(user_id);
CREATE INDEX idx_assignments_converted ON assignments(converted_at) WHERE converted_at IS NOT NULL;

-- ============================================
-- PLATFORM INSTALLATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS platform_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Platform info
    platform VARCHAR(50) NOT NULL,
    installation_method VARCHAR(50) NOT NULL,
    
    -- Site info
    site_url VARCHAR(500) NOT NULL,
    site_name VARCHAR(255),
    
    -- Tokens
    installation_token VARCHAR(255) UNIQUE NOT NULL,
    api_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    verified_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    plugin_version VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_installation_status CHECK (status IN ('pending', 'active', 'inactive', 'error', 'archived'))
);

CREATE INDEX idx_installations_user ON platform_installations(user_id);
CREATE INDEX idx_installations_token ON platform_installations(installation_token);
CREATE INDEX idx_installations_status ON platform_installations(status);

-- ============================================
-- INSTALLATION LOGS
-- ============================================

CREATE TABLE IF NOT EXISTS installation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id UUID REFERENCES platform_installations(id) ON DELETE CASCADE,
    
    event_type VARCHAR(50) NOT NULL,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_installation_logs_install ON installation_logs(installation_id);
CREATE INDEX idx_installation_logs_created ON installation_logs(created_at DESC);

-- ============================================
-- EMAIL CAMPAIGNS
-- ============================================

CREATE TABLE IF NOT EXISTS email_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    
    -- Email config
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255) NOT NULL,
    reply_to VARCHAR(255),
    
    -- Template
    template_html TEXT NOT NULL,
    
    -- Platform
    platform VARCHAR(50) DEFAULT 'mock',
    
    -- Test config
    test_percentage DECIMAL(3,2) DEFAULT 0.10,
    winner_criteria VARCHAR(50) DEFAULT 'open_rate',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_email_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived'))
);

CREATE INDEX idx_email_campaigns_user ON email_campaigns(user_id);
CREATE INDEX idx_email_campaigns_status ON email_campaigns(status);

-- ============================================
-- EMAIL ELEMENTS
-- ============================================

CREATE TABLE IF NOT EXISTS email_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES email_campaigns(id) ON DELETE CASCADE,
    
    element_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_elements_campaign ON email_elements(campaign_id);

-- ============================================
-- EMAIL VARIANTS
-- ============================================

CREATE TABLE IF NOT EXISTS email_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    element_id UUID NOT NULL REFERENCES email_elements(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_variants_element ON email_variants(element_id);

-- ============================================
-- EMAIL SEND BATCHES
-- ============================================

CREATE TABLE IF NOT EXISTS email_send_batches (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES email_campaigns(id) ON DELETE CASCADE,
    
    total_recipients INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',
    scheduled_time TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_send_status CHECK (status IN ('queued', 'sending', 'sent', 'failed'))
);

CREATE INDEX idx_email_batches_campaign ON email_send_batches(campaign_id);

-- ============================================
-- EMAIL SENDS
-- ============================================

CREATE TABLE IF NOT EXISTS email_sends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    send_batch_id UUID REFERENCES email_send_batches(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES email_campaigns(id) ON DELETE CASCADE,
    
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    
    variant_id UUID REFERENCES email_variants(id),
    
    status VARCHAR(20) DEFAULT 'queued',
    
    -- Tracking
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,
    unsubscribed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_sends_batch ON email_sends(send_batch_id);
CREATE INDEX idx_email_sends_campaign ON email_sends(campaign_id);
CREATE INDEX idx_email_sends_recipient ON email_sends(recipient_email);

-- ============================================
-- EMAIL INTERACTIONS
-- ============================================

CREATE TABLE IF NOT EXISTS email_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    send_id UUID REFERENCES email_sends(id) ON DELETE CASCADE,
    
    interaction_type VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_interactions_send ON email_interactions(send_id);
CREATE INDEX idx_email_interactions_type ON email_interactions(interaction_type);

-- ============================================
-- TRIGGERS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_installations_updated_at BEFORE UPDATE ON platform_installations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_campaigns_updated_at BEFORE UPDATE ON email_campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE element_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_campaigns ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY experiments_user_policy ON experiments
    FOR ALL USING (auth.uid()::uuid = user_id);

CREATE POLICY elements_user_policy ON experiment_elements
    FOR ALL USING (
        experiment_id IN (SELECT id FROM experiments WHERE user_id = auth.uid()::uuid)
    );

CREATE POLICY variants_user_policy ON element_variants
    FOR ALL USING (
        element_id IN (
            SELECT ee.id FROM experiment_elements ee
            JOIN experiments e ON ee.experiment_id = e.id
            WHERE e.user_id = auth.uid()::uuid
        )
    );

CREATE POLICY installations_user_policy ON platform_installations
    FOR ALL USING (auth.uid()::uuid = user_id);

CREATE POLICY email_campaigns_user_policy ON email_campaigns
    FOR ALL USING (auth.uid()::uuid = user_id);

-- ============================================
-- VIEWS (útiles)
-- ============================================

CREATE OR REPLACE VIEW experiment_stats AS
SELECT 
    e.id as experiment_id,
    e.user_id,
    e.name,
    e.status,
    COUNT(DISTINCT a.user_id) as total_visitors,
    COUNT(DISTINCT a.id) FILTER (WHERE a.converted_at IS NOT NULL) as total_conversions,
    CASE 
        WHEN COUNT(DISTINCT a.user_id) > 0 
        THEN COUNT(DISTINCT a.id) FILTER (WHERE a.converted_at IS NOT NULL)::FLOAT / 
             COUNT(DISTINCT a.user_id)::FLOAT
        ELSE 0
    END as conversion_rate
FROM experiments e
LEFT JOIN assignments a ON e.id = a.experiment_id
GROUP BY e.id, e.user_id, e.name, e.status;

-- ============================================
-- FUNCIONES ÚTILES
-- ============================================

CREATE OR REPLACE FUNCTION get_user_plan_limits(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_plan VARCHAR;
BEGIN
    SELECT COALESCE(plan, 'free') INTO v_plan
    FROM subscriptions
    WHERE user_id = p_user_id;
    
    -- Retornar límites según plan
    RETURN CASE v_plan
        WHEN 'free' THEN '{"experiments": 2, "monthly_visitors": 1000}'::JSONB
        WHEN 'starter' THEN '{"experiments": 10, "monthly_visitors": 50000}'::JSONB
        WHEN 'professional' THEN '{"experiments": 50, "monthly_visitors": 500000}'::JSONB
        WHEN 'enterprise' THEN '{"experiments": -1, "monthly_visitors": -1}'::JSONB
        ELSE '{"experiments": 2, "monthly_visitors": 1000}'::JSONB
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DATOS INICIALES (opcional)
-- ============================================

-- Crear usuario de prueba (comentar en producción)
-- INSERT INTO users (email, password_hash, name) 
-- VALUES (
--     'test@example.com',
--     crypt('password123', gen_salt('bf')),
--     'Test User'
-- );

-- ============================================
-- ÍNDICES ADICIONALES PARA PERFORMANCE
-- ============================================

CREATE INDEX idx_assignments_converted_at ON assignments(converted_at) WHERE converted_at IS NOT NULL;
CREATE INDEX idx_experiments_active ON experiments(user_id, status) WHERE status = 'active';
CREATE INDEX idx_email_sends_opened ON email_sends(opened_at) WHERE opened_at IS NOT NULL;

-- ============================================
-- CLEANUP FUNCTION (opcional)
-- ============================================

CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    -- Eliminar asignaciones antiguas (>90 días)
    WITH deleted AS (
        DELETE FROM assignments 
        WHERE assigned_at < NOW() - INTERVAL '90 days'
        RETURNING id
    )
    SELECT COUNT(*) INTO v_deleted FROM deleted;
    
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMPLETADO
-- ============================================

-- Para ejecutar cleanup manualmente:
-- SELECT cleanup_old_data();

-- Para ver stats de un experimento:
-- SELECT * FROM experiment_stats WHERE experiment_id = 'your-id';

-- Para ver límites de un usuario:
-- SELECT get_user_plan_limits('user-id');
