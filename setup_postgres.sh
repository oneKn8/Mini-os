#!/bin/bash

echo "========================================="
echo "  PostgreSQL Native Setup"
echo "========================================="
echo ""

# Install PostgreSQL if not already installed
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
fi

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
echo ""
echo "Creating database and user..."
sudo -u postgres psql << PSQL
-- Drop if exists
DROP DATABASE IF EXISTS ops_center;
DROP USER IF EXISTS ops_user;

-- Create user
CREATE USER ops_user WITH PASSWORD 'ops_password';

-- Create database
CREATE DATABASE ops_center OWNER ops_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ops_center TO ops_user;

\q
PSQL

echo ""
echo "[OK] PostgreSQL setup complete!"
echo ""
echo "Database: ops_center"
echo "User: ops_user"
echo "Password: ops_password"
echo "Host: localhost"
echo "Port: 5432"
echo ""
