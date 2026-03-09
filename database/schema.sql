-- ============================================================================
-- ZERO TRUST NETWORK ACCESS (ZTNA) DATABASE SCHEMA
-- PostgreSQL 14+
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- Stores user authentication information
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    lockout_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    password_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '90 days')
);

-- Index for username lookup
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- DEVICES TABLE
-- Stores device information for Zero Trust device verification
-- ============================================================================
CREATE TABLE IF NOT EXISTS devices (
    device_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_uuid VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    device_name VARCHAR(255),
    device_type VARCHAR(50), -- laptop, mobile, iot, etc.
    os_name VARCHAR(50),
    os_version VARCHAR(50),
    mac_address VARCHAR(17),
    ip_address INET,
    is_trusted BOOLEAN DEFAULT FALSE,
    security_level INTEGER DEFAULT 1, -- 1-5 scale
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(20) DEFAULT 'unknown', -- healthy, warning, critical
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    hardware_hash VARCHAR(255),
    secure_boot_enabled BOOLEAN DEFAULT FALSE,
    encryption_enabled BOOLEAN DEFAULT FALSE,
    antivirus_enabled BOOLEAN DEFAULT FALSE,
    firewall_enabled BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_uuid ON devices(device_uuid);
CREATE INDEX IF NOT EXISTS idx_devices_trusted ON devices(is_trusted);

-- ============================================================================
-- POLICIES TABLE
-- Zero Trust access policies
-- ============================================================================
CREATE TABLE IF NOT EXISTS policies (
    policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_name VARCHAR(255) NOT NULL,
    policy_type VARCHAR(50) NOT NULL, -- identity, device, location, time, behavior
    description TEXT,
    priority INTEGER DEFAULT 100,
    is_enabled BOOLEAN DEFAULT TRUE,
    conditions JSONB NOT NULL, -- Policy conditions in JSON format
    actions JSONB NOT NULL, -- Policy actions (grant/deny)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_policies_type ON policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_policies_enabled ON policies(is_enabled);

-- ============================================================================
-- ACCESS LOGS TABLE
-- Comprehensive audit logging
-- ============================================================================
CREATE TABLE IF NOT EXISTS access_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(user_id),
    username VARCHAR(100),
    device_id UUID REFERENCES devices(device_id),
    ip_address INET,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    result VARCHAR(20) NOT NULL, -- success, denied, error
    reason TEXT,
    policy_matched UUID REFERENCES policies(policy_id),
    risk_score INTEGER,
    tls_version VARCHAR(10),
    cipher_suite VARCHAR(50),
    pqc_algorithm VARCHAR(50)
);

-- ============================================================================
-- SEED DATA
-- ============================================================================
INSERT INTO users (username, email, password_hash, salt, role, is_active) 
VALUES ('admin', 'admin@ztna.local', 'pbkdf2:sha256:260000$admin_hash', 'salt123', 'admin', TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO devices (device_uuid, device_name, device_type, os_name, os_version, is_trusted, security_level)
VALUES ('DEV-UUID-001', 'Admin-Laptop', 'laptop', 'Ubuntu', '24.04', TRUE, 5)
ON CONFLICT DO NOTHING;

INSERT INTO policies (policy_name, policy_type, description, priority, conditions, actions) 
VALUES ('Admin Full Access', 'identity', 'Full access for admins', 1, '{"user_role": "admin", "device_trusted": true}', '{"access": "grant"}')
ON CONFLICT DO NOTHING;
