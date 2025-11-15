#!/bin/bash
# Run this manually: sudo ./create_tables.sh

sudo -u postgres psql ops_center << 'SQL'
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    location_city VARCHAR(100),
    location_country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS connected_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    account_email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    raw_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_provider VARCHAR(50) NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    external_id VARCHAR(255),
    title TEXT,
    body_full TEXT,
    body_preview TEXT,
    sender VARCHAR(255),
    received_at TIMESTAMP,
    start_datetime TIMESTAMP,
    end_datetime TIMESTAMP,
    due_datetime TIMESTAMP,
    importance VARCHAR(20),
    category VARCHAR(50),
    suggested_action VARCHAR(100),
    ingestion_status VARCHAR(20) DEFAULT 'pending',
    labels TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT 'Database tables created successfully!' as status;
SQL

echo ""
echo "[OK] Tables created in ops_center database!"
