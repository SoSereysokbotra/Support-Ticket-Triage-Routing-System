-- ============================================================================
-- Migration: 001_enterprise_multi_tenant.sql
-- Description: Multi-Tenancy, RBAC, Enterprise Tickets, SLA & Webhooks
-- Target: PostgreSQL 16
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum Types (Created safely)
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tenant_plan_enum') THEN
        CREATE TYPE tenant_plan_enum AS ENUM ('STARTER', 'GROWTH', 'ENTERPRISE');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
        CREATE TYPE user_role_enum AS ENUM ('SUPERADMIN', 'TENANT_ADMIN', 'TRIAGE_LEAD', 'SUPPORT_AGENT', 'AUDITOR', 'BOT');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticket_status_enum') THEN
        CREATE TYPE ticket_status_enum AS ENUM ('OPEN', 'PENDING_AGENT', 'RESOLVED', 'CLOSED', 'BREACHED');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'priority_enum') THEN
        CREATE TYPE priority_enum AS ENUM ('P1_CRITICAL', 'P2_HIGH', 'P3_MEDIUM', 'P4_LOW');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'customer_tier_enum') THEN
        CREATE TYPE customer_tier_enum AS ENUM ('FREE', 'STANDARD', 'BUSINESS', 'VIP_ENTERPRISE');
    END IF;
END $$;

-- 1. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    slug VARCHAR(64) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    plan VARCHAR(32) NOT NULL DEFAULT 'GROWTH',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'SUPPORT_AGENT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, email)
);

CREATE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email);

-- 3. Enterprise Tickets Table
CREATE TABLE IF NOT EXISTS enterprise_tickets (
    ticket_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    external_ticket_id VARCHAR(128),
    title VARCHAR(512),
    description TEXT NOT NULL,
    customer_id VARCHAR(128) NOT NULL,
    customer_tier VARCHAR(32) NOT NULL DEFAULT 'STANDARD',
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    
    predicted_category VARCHAR(64) NOT NULL,
    confidence NUMERIC(5, 4) NOT NULL,
    probabilities JSONB NOT NULL,
    assigned_team VARCHAR(128) NOT NULL,
    assigned_agent_id VARCHAR(64) REFERENCES users(user_id) ON DELETE SET NULL,
    priority VARCHAR(32) NOT NULL DEFAULT 'P3_MEDIUM',
    auto_routed BOOLEAN NOT NULL DEFAULT FALSE,
    model_version VARCHAR(64) NOT NULL,
    latency_ms NUMERIC(8, 2) NOT NULL,
    
    copilot_suggested_response TEXT,
    copilot_confidence NUMERIC(5, 4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_enterprise_tickets_tenant_status ON enterprise_tickets(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_enterprise_tickets_created_at ON enterprise_tickets(created_at);

-- 4. Agent Feedback Annotations Table (HITL)
CREATE TABLE IF NOT EXISTS agent_feedback_annotations (
    feedback_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    ticket_id VARCHAR(64) NOT NULL REFERENCES enterprise_tickets(ticket_id) ON DELETE CASCADE,
    agent_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    original_category VARCHAR(64) NOT NULL,
    corrected_category VARCHAR(64) NOT NULL,
    original_priority VARCHAR(32) NOT NULL,
    corrected_priority VARCHAR(32) NOT NULL,
    
    model_version VARCHAR(64) NOT NULL,
    original_confidence NUMERIC(5, 4) NOT NULL,
    reclassification_reason TEXT,
    is_used_in_retraining BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_tenant_retrained ON agent_feedback_annotations(tenant_id, is_used_in_retraining);
