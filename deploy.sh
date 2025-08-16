#!/bin/bash
# deploy.sh - Deployment script for AI Behar Platform
# This script helps switch between development and production configurations

# Define colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Navigate to the script directory
cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

# Usage information
show_usage() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║               ${GREEN}AI BEHAR PLATFORM DEPLOYMENT${BLUE}              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  $0 [options]"
    echo
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  ${CYAN}-e, --env${NC} ENVIRONMENT    Set environment (development, production)"
    echo -e "  ${CYAN}-p, --port${NC} PORT          Set API port number"
    echo -e "  ${CYAN}-h, --host${NC} HOST          Set API host"
    echo -e "  ${CYAN}-s, --setup${NC}              Run initial setup (database, Ollama)"
    echo -e "  ${CYAN}-d, --docker${NC}             Deploy using Docker"
    echo -e "  ${CYAN}--help${NC}                   Show this help message"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 --env development --port 8000"
    echo -e "  $0 --env production --host 0.0.0.0 --port 8001"
    echo -e "  $0 --env production --docker"
    echo
}

# Default values
ENVIRONMENT="development"
API_PORT="8000"
API_HOST="127.0.0.1"
RUN_SETUP=false
USE_DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--port)
            API_PORT="$2"
            shift 2
            ;;
        -h|--host)
            API_HOST="$2"
            shift 2
            ;;
        -s|--setup)
            RUN_SETUP=true
            shift
            ;;
        -d|--docker)
            USE_DOCKER=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    echo -e "${RED}Error: Environment must be either 'development' or 'production'${NC}"
    exit 1
fi

# Set environment files
ENV_SOURCE="$PROJECT_ROOT/.env.$ENVIRONMENT"
ENV_TARGET="$PROJECT_ROOT/.env"

# Check if environment file exists
if [ ! -f "$ENV_SOURCE" ]; then
    echo -e "${RED}Error: Environment file $ENV_SOURCE not found${NC}"
    exit 1
fi

# Banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║             ${GREEN}AI BEHAR PLATFORM DEPLOYMENT${BLUE}                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  ${CYAN}Environment:${NC} $ENVIRONMENT"
echo -e "  ${CYAN}API Host:${NC} $API_HOST"
echo -e "  ${CYAN}API Port:${NC} $API_PORT"
echo -e "  ${CYAN}Docker:${NC} $(if [ "$USE_DOCKER" = true ]; then echo "Yes"; else echo "No"; fi)"
echo -e "  ${CYAN}Setup:${NC} $(if [ "$RUN_SETUP" = true ]; then echo "Yes"; else echo "No"; fi)"
echo

# Setup environment file
echo -e "${YELLOW}Setting up environment configuration...${NC}"
cp "$ENV_SOURCE" "$ENV_TARGET"

# Update API host and port in .env file
sed -i "s/API_HOST=.*/API_HOST=$API_HOST/" "$ENV_TARGET"
sed -i "s/API_PORT=.*/API_PORT=$API_PORT/" "$ENV_TARGET"

echo -e "${GREEN}✓ Environment configuration set to $ENVIRONMENT${NC}"

# Create logs directory
echo -e "${YELLOW}Creating logs directory...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
echo -e "${GREEN}✓ Logs directory created${NC}"

# Run setup if requested
if [ "$RUN_SETUP" = true ]; then
    echo -e "${YELLOW}Running initial setup...${NC}"

    # Run Ollama setup
    if [ -f "$PROJECT_ROOT/ollama_setup.sh" ]; then
        echo -e "${YELLOW}Setting up Ollama...${NC}"
        bash "$PROJECT_ROOT/ollama_setup.sh"
    else
        echo -e "${RED}⚠️ Ollama setup script not found${NC}"
    fi

    # Initialize databases
    if [ -f "$PROJECT_ROOT/initialize_databases.sh" ]; then
        echo -e "${YELLOW}Initializing databases...${NC}"
        bash "$PROJECT_ROOT/initialize_databases.sh"
    else
        echo -e "${RED}⚠️ Database initialization script not found${NC}"
    fi

    echo -e "${GREEN}✓ Initial setup completed${NC}"
fi

# Deploy using Docker if requested
if [ "$USE_DOCKER" = true ]; then
    echo -e "${YELLOW}Deploying with Docker...${NC}"

    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        # Stop any running containers
        docker compose down

        # Start containers
        docker compose up -d

        echo -e "${GREEN}✓ Docker deployment completed${NC}"
        echo -e "${YELLOW}The platform is now available at:${NC}"
        echo -e "  ${CYAN}Main interface:${NC} http://$API_HOST:$API_PORT"
        echo -e "  ${CYAN}OpenWebUI:${NC} http://$API_HOST:8080"
    else
        echo -e "${RED}⚠️ docker-compose.yml not found${NC}"
        echo -e "${YELLOW}Creating Docker Compose configuration...${NC}"

        # Create Docker Compose file
        cat > "$PROJECT_ROOT/docker-compose.yml" << EOL
version: '3.8'

services:
  # FastAPI backend
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-behar-api
    ports:
      - "${API_PORT}:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - DATABASE_URL=sqlite:///app/databases/runtime/platform.db
      - OLLAMA_BASE_URL=http://ollama:11434
      - REDIS_HOST=redis
    volumes:
      - ./databases:/app/databases
      - ./logs:/app/logs
    depends_on:
      - redis
      - ollama
    restart: unless-stopped
    networks:
      - ai-behar-network

  # Redis for caching
  redis:
    image: redis:7-alpine
    container_name: ai-behar-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - ai-behar-network

  # Ollama LLM service
  ollama:
    image: ollama/ollama:latest
    container_name: ai-behar-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped
    networks:
      - ai-behar-network

  # OpenWebUI
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: ai-behar-openwebui
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - openwebui-data:/app/backend/data
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - ai-behar-network

volumes:
  redis-data:
  ollama-data:
  openwebui-data:

networks:
  ai-behar-network:
    driver: bridge
EOL

        # Create Dockerfile
        cat > "$PROJECT_ROOT/Dockerfile" << EOL
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_core.txt .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements_core.txt
RUN pip install --no-cache-dir -r requirements.txt || echo "Some packages could not be installed"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/databases/runtime /app/logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "core.enhanced_platform:app", "--host", "0.0.0.0", "--port", "8000"]
EOL

        echo -e "${GREEN}✓ Docker configuration created${NC}"
        echo -e "${YELLOW}Starting Docker deployment...${NC}"

        # Start containers
        docker compose up -d

        echo -e "${GREEN}✓ Docker deployment completed${NC}"
        echo -e "${YELLOW}The platform is now available at:${NC}"
        echo -e "  ${CYAN}Main interface:${NC} http://$API_HOST:$API_PORT"
        echo -e "  ${CYAN}OpenWebUI:${NC} http://$API_HOST:8080"
    fi
else
    # Run in venv
    echo -e "${YELLOW}Running platform in virtual environment...${NC}"

    # Ensure venv exists
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi

    # Activate venv
    source "$PROJECT_ROOT/venv/bin/activate"

    # Run the platform
    echo -e "${GREEN}✓ Starting AI Behar Platform...${NC}"
    echo -e "${YELLOW}The platform will be available at:${NC}"
    echo -e "  ${CYAN}Main interface:${NC} http://$API_HOST:$API_PORT"

    # Change to project root
    cd "$PROJECT_ROOT"

    # Run the platform
    python -m uvicorn core.enhanced_platform:app --host "$API_HOST" --port "$API_PORT" --reload
fi
