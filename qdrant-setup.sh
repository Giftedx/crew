#!/bin/bash

# Ultimate Discord Intelligence Bot - Qdrant Setup Script
# This script helps set up Qdrant vector database for local development

set -e  # Exit on any error

echo "🔧 Qdrant Vector Database Setup"
echo "==============================="

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "💡 Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "💡 Please start Docker first"
    exit 1
fi

echo "✅ Docker is available and running"

# Check if Qdrant is already running
if docker ps | grep -q "qdrant"; then
    echo "⚠️  Qdrant container is already running"
    read -p "Do you want to stop and restart it? (y/N): " restart
    if [[ $restart =~ ^[Yy]$ ]]; then
        echo "🔄 Stopping existing Qdrant container..."
        docker stop qdrant || true
        docker rm qdrant || true
    else
        echo "ℹ️  Using existing Qdrant container"
        exit 0
    fi
fi

echo ""
echo "Choose your Qdrant setup option:"
echo ""
echo "1) Quick Start - Single Qdrant container (recommended)"
echo "2) Full Stack - Qdrant + Redis + PostgreSQL"
echo "3) Custom - Advanced configuration"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "🚀 Starting Qdrant with Docker Compose..."
        if [ ! -f "docker-compose.yml" ]; then
            echo "❌ docker-compose.yml not found"
            echo "💡 Please make sure you're in the project root directory"
            exit 1
        fi
        
        docker-compose up -d qdrant
        
        echo "⏳ Waiting for Qdrant to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:6333/ > /dev/null 2>&1; then
                echo "✅ Qdrant is ready!"
                break
            fi
            if [ $i -eq 30 ]; then
                echo "❌ Timeout waiting for Qdrant to start"
                echo "💡 Check logs with: docker-compose logs qdrant"
                exit 1
            fi
            sleep 2
        done
        ;;
        
    2)
        echo "🚀 Starting full stack (Qdrant + Redis + PostgreSQL)..."
        docker-compose --profile full up -d
        
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Check Qdrant
        if curl -s http://localhost:6333/ > /dev/null 2>&1; then
            echo "✅ Qdrant is ready!"
        else
            echo "⚠️  Qdrant may still be starting up"
        fi
        ;;
        
    3)
        echo "🔧 Custom setup selected"
        echo "💡 Edit docker-compose.yml and run manually:"
        echo "   docker-compose up -d qdrant"
        exit 0
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Qdrant setup complete!"
echo "======================="
echo ""
echo "📊 Service Status:"
echo "- Qdrant API: http://localhost:6333"
echo "- Qdrant Dashboard: http://localhost:6333/dashboard"

if [ "$choice" -eq 2 ]; then
    echo "- Redis: localhost:6379"
    echo "- PostgreSQL: localhost:5432"
fi

echo ""
echo "💡 Configuration for .env file:"
echo "QDRANT_URL=http://localhost:6333"
echo "# QDRANT_API_KEY=  # Leave empty for local setup"

echo ""
echo "🔧 Useful commands:"
echo "- View logs: docker-compose logs -f qdrant"
echo "- Stop services: docker-compose down"
echo "- Reset data: docker-compose down -v (WARNING: deletes all data)"

echo ""
echo "🧪 Test your setup:"
echo "python -c \"
from qdrant_client import QdrantClient
client = QdrantClient(url='http://localhost:6333')
print('✅ Successfully connected to Qdrant!')
print(f'📊 Collections: {len(list(client.get_collections().collections))}')
\""
