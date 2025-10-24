#!/bin/bash
# Monitoring Setup Script for Ultimate Discord Intelligence Bot

set -e

echo "🚀 Setting up monitoring stack..."

# Create necessary directories
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/alertmanager

# Start monitoring stack
echo "🐳 Starting Docker containers..."
docker-compose -f monitoring/grafana/docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose -f monitoring/grafana/docker-compose.yml ps

# Import dashboards
echo "📈 Importing Grafana dashboards..."
# Add dashboard import commands here

echo "✅ Monitoring stack setup complete!"
echo "📊 Grafana: http://localhost:3000 (admin/admin)"
echo "📈 Prometheus: http://localhost:9090"
echo "🚨 Alertmanager: http://localhost:9093"
