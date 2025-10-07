-- database/migrations/001_initial_schema.sql

-- ============================================
-- SAMPLIT DATABASE SCHEMA
-- ⚠️  CONFIDENTIAL - Proprietary Structure
-- ============================================

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
-- EXPERIMENTS
-- ============================================

CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    
    -- Type and strategy
    experiment_type VARCHAR(50) DEFAULT 'standard',
    optimization_strategy VARCHAR(50) DEFAULT 'adaptive',
    
    -- Config (JSON - flexible)
    config JSONB DEFAULT '{}',
    
    -- Target
    target_url VARCHAR(500),
    target_type VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived'))
);

CREATE INDEX idx_experiments_user_id ON experiments(user_id);
CREATE INDEX idx_experiments_status ON experiments(status);

-- ============================================
-- VARIANTS (NO "arms")
-- ============================================

CREATE TABLE IF NOT EXISTS variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    
    -- Content
    content JSONB DEFAULT '{}',
    
    -- Public metrics
    total_allocations INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    observed_conversion_rate DECIMAL(10,6) DEFAULT 0.0,
    
    -- ⚠️ CRITICAL: Encrypted algorithm state
    algorithm_state BYTEA,
    state_version INTEGER DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id, name)
);

CREATE INDEX idx_variants_experiment ON variants(experiment_id);

-- ============================================
-- ALLOCATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    
    -- User identification
    user_identifier VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    
    -- Context
    context JSONB DEFAULT '{}',
    
    -- Outcomes
    allocated_at TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ,
    conversion_value DECIMAL(10,2) DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(experiment_id, user_identifier)
);

CREATE INDEX idx_allocations_experiment ON allocations(experiment_id);
CREATE INDEX idx_allocations_variant ON allocations(variant_id);
CREATE INDEX idx_allocations_user ON allocations(user_identifier);

-- ============================================
-- PERFORMANCE SNAPSHOTS
-- ============================================

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    variant_id UUID REFERENCES variants(id) ON DELETE CASCADE,
    
    -- Period
    snapshot_date DATE NOT NULL,
    snapshot_hour INTEGER,
    
    -- Public metrics
    allocations_count INTEGER DEFAULT 0,
    conversions_count INTEGER DEFAULT 0,
    conversion_rate DECIMAL(10,6) DEFAULT 0.0,
    
    -- Confidence
    confidence_score DECIMAL(5,4) DEFAULT 0.0,
    statistical_significance BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(experiment_id, variant_id, snapshot_date, snapshot_hour)
);

CREATE INDEX idx_perf_snapshots_experiment ON performance_snapshots(experiment_id);

-- ============================================
-- FUNNEL OPTIMIZATION
-- ============================================

CREATE TABLE IF NOT EXISTS funnels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    
    -- Config
    config JSONB DEFAULT '{}',
    
    -- Steps (array of step definitions)
    steps JSONB NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funnels_user ON funnels(user_id);

-- ============================================
-- FUNNEL SESSIONS
-- ============================================

CREATE TABLE IF NOT EXISTS funnel_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    funnel_id UUID NOT NULL REFERENCES funnels(id) ON DELETE CASCADE,
    
    -- User
    user_identifier VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Progress
    current_step_index INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    converted BOOLEAN DEFAULT false,
    
    -- Path (variant selections per step)
    selected_variants JSONB DEFAULT '[]',
    
    -- Context
    user_context JSONB DEFAULT '{}',
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funnel_sessions_funnel ON funnel_sessions(funnel_id);
CREATE INDEX idx_funnel_sessions_user ON funnel_sessions(user_identifier);

-- ⚠️ CRITICAL: Path Performance (TRADE SECRET)
CREATE TABLE IF NOT EXISTS funnel_path_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    funnel_id UUID NOT NULL REFERENCES funnels(id) ON DELETE CASCADE,
    
    -- Path (hashed for privacy)
    path_hash VARCHAR(64) NOT NULL,
    
    -- Path data (ENCRYPTED)
    path_data BYTEA,
    
    -- Performance (public)
    attempts INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(10,6) DEFAULT 0.0,
    
    -- Algorithm state (ENCRYPTED)
    optimization_state BYTEA,
    
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(funnel_id, path_hash)
);

CREATE INDEX idx_path_performance_funnel ON funnel_path_performance(funnel_id);

-- ============================================
-- EMAIL & PUSH OPTIMIZATION
-- ============================================

CREATE TABLE IF NOT EXISTS email_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    
    -- Optimization
    optimization_enabled BOOLEAN DEFAULT true,
    strategy VARCHAR(50) DEFAULT 'adaptive',
    
    -- Variants
    subject_variants JSONB,
    content_variants JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES email_campaigns(id) ON DELETE CASCADE,
    
    recipient_hash VARCHAR(64) NOT NULL,
    variant_id VARCHAR(255),
    
    -- Outcomes
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    converted_at TIMESTAMPTZ,
    
    -- Context
    context JSONB DEFAULT '{}'
);

CREATE INDEX idx_email_deliveries_campaign ON email_deliveries(campaign_id);

CREATE TABLE IF NOT EXISTS push_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    
    optimization_enabled BOOLEAN DEFAULT true,
    strategy VARCHAR(50) DEFAULT 'adaptive',
    
    message_variants JSONB,
    timing_strategy JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- OPTIMIZATION STATE (CRITICAL)
-- ============================================

CREATE TABLE IF NOT EXISTS optimization_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Reference
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    variant_id UUID,
    
    -- ⚠️ Encrypted state
    encrypted_state BYTEA NOT NULL,
    state_version INTEGER DEFAULT 1,
    
    -- Metadata (non-sensitive)
    state_type VARCHAR(50),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    update_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(entity_type, entity_id, variant_id)
);

CREATE INDEX idx_optimization_state_entity ON optimization_state(entity_type, entity_id);

-- ============================================
-- AUDIT LOG
-- ============================================

CREATE TABLE IF NOT EXISTS algorithm_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    experiment_id UUID NOT NULL,
    user_identifier VARCHAR(255),
    
    -- Decision
    selected_variant_id UUID,
    decision_type VARCHAR(50),
    
    -- Metadata (sanitized - NO algorithm details)
    decision_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_decisions_experiment ON algorithm_decisions(experiment_id);

-- ============================================
-- VIEWS
-- ============================================

CREATE OR REPLACE VIEW variant_performance_view AS
SELECT 
    v.id,
    v.experiment_id,
    v.name,
    v.total_allocations,
    v.total_conversions,
    v.observed_conversion_rate,
    CASE 
        WHEN v.total_allocations >= 100 THEN true
        ELSE false
    END as has_statistical_significance,
    v.updated_at
FROM variants v
WHERE v.is_active = true;

-- ============================================
-- FUNCTIONS
-- ============================================

CREATE OR REPLACE FUNCTION update_variant_metrics(
    p_variant_id UUID,
    p_conversion BOOLEAN
) RETURNS VOID AS $$
BEGIN
    UPDATE variants
    SET 
        total_allocations = total_allocations + 1,
        total_conversions = total_conversions + CASE WHEN p_conversion THEN 1 ELSE 0 END,
        observed_conversion_rate = 
            (total_conversions + CASE WHEN p_conversion THEN 1 ELSE 0 END)::DECIMAL / 
            (total_allocations + 1)::DECIMAL,
        updated_at = NOW()
    WHERE id = p_variant_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_experiments_updated_at 
    BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variants_updated_at 
    BEFORE UPDATE ON variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_funnels_updated_at 
    BEFORE UPDATE ON funnels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE funnels ENABLE ROW LEVEL SECURITY;

-- Users can only see their own experiments
CREATE POLICY experiments_user_policy ON experiments
    FOR ALL
    USING (auth.uid()::uuid = user_id);

-- Variants visible if experiment is accessible
CREATE POLICY variants_user_policy ON variants
    FOR ALL
    USING (
        experiment_id IN (
            SELECT id FROM experiments WHERE user_id = auth.uid()::uuid
        )
    );

-- Allocations visible if experiment is accessible
CREATE POLICY allocations_user_policy ON allocations
    FOR ALL
    USING (
        experiment_id IN (
            SELECT id FROM experiments WHERE user_id = auth.uid()::uuid
        )
    );

-- Funnels accessible to owner
CREATE POLICY funnels_user_policy ON funnels
    FOR ALL
    USING (auth.uid()::uuid = user_id);

-- ⚠️ CRITICAL: optimization_state NEVER accessible via direct queries
ALTER TABLE optimization_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY optimization_state_no_direct_access ON optimization_state
    FOR ALL
    USING (false);

-- Only service role can access
GRANT SELECT, INSERT, UPDATE ON optimization_state TO service_role;
REVOKE ALL ON optimization_state FROM authenticated;
REVOKE ALL ON optimization_state FROM anon;

-- ============================================
-- INITIAL DATA (optional)
-- ============================================

-- Create default admin user (change password!)
-- INSERT INTO users (email, password_hash, name) 
-- VALUES (
--     'admin@samplit.com',
--     crypt('CHANGE_THIS_PASSWORD', gen_salt('bf')),
--     'Admin User'
-- );
