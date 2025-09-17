#!/bin/bash

# Distributor Monitor Deployment Script

set -e

echo "🚀 Distributor Monitor Deployment Script"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Function to use docker-compose or docker compose
docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    else
        docker compose "$@"
    fi
}

# Parse command line arguments
MODE="production"
REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            MODE="development"
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dev] [--rebuild] [--help]"
            echo ""
            echo "Options:"
            echo "  --dev      Run in development mode with hot reload"
            echo "  --rebuild  Force rebuild of Docker images"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. API keys will not be available."
    echo "   Create .env file with ANKR_API_KEY and ETHERSCAN_API_KEY for better performance."
fi

# Build options
BUILD_ARGS=""
if [ "$REBUILD" = true ]; then
    BUILD_ARGS="--build --force-recreate"
    echo "🔨 Rebuilding Docker images..."
fi

# Deploy based on mode
if [ "$MODE" = "development" ]; then
    echo "🛠️  Starting in development mode..."
    echo "   - Hot reload enabled"
    echo "   - Debug logging enabled"
    echo "   - Available at http://localhost:8502"
    
    docker_compose_cmd --profile dev up $BUILD_ARGS distributor-monitor-dev
else
    echo "🏭 Starting in production mode..."
    echo "   - Available at http://localhost:8501"
    
    docker_compose_cmd up $BUILD_ARGS -d distributor-monitor
    
    echo "✅ Distributor Monitor is running!"
    echo ""
    echo "📊 Access the application:"
    echo "   🌐 Web Interface: http://localhost:8501"
    echo ""
    echo "🔧 Management commands:"
    echo "   📋 View logs:    docker-compose logs -f distributor-monitor"
    echo "   🛑 Stop:         docker-compose down"
    echo "   🔄 Restart:      docker-compose restart distributor-monitor"
    echo "   📊 Status:       docker-compose ps"
fi
