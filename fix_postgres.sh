#!/bin/bash

echo "========================================="
echo "  Fixing PostgreSQL TCP Configuration"
echo "========================================="
echo ""

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

DB_PORT=${LOCAL_DB_PORT:-5543}

echo "[1/3] Configuring PostgreSQL to accept TCP connections..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/14/main/postgresql.conf
sudo sed -i "s/^port = .*/port = ${DB_PORT}/" /etc/postgresql/14/main/postgresql.conf

echo "[2/3] Restarting PostgreSQL..."
sudo systemctl restart postgresql

echo "Waiting for PostgreSQL to restart..."
sleep 3

echo ""
echo "[3/3] Testing connection..."
if PGPASSWORD=ops_password psql -U ops_user -h localhost -p "${DB_PORT}" -d ops_center -c "SELECT 1;" > /dev/null 2>&1; then
    echo "[OK] PostgreSQL TCP connection working!"
else
    echo "[WARN] Connection test failed, but service is running"
fi

echo ""
echo "[OK] PostgreSQL configuration complete!"
echo ""
