#!/bin/bash

echo "========================================="
echo "  Restarting Personal Ops Center"
echo "========================================="
echo ""

./stop.sh
sleep 2
./start.sh

