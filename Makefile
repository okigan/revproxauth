# Makefile for SynAuthProxy - Multi-stack authentication proxy

.PHONY: all help up-synauthproxy up-nginx up-traefik up-caddy down-all clean-all logs serve-guide lint format lint-check install-hooks

# Default target
all: help

# Show help
help:
	@echo "🔐 SynAuthProxy - Multi-Stack Authentication Proxy"
	@echo ""
	@echo "Available Stacks:"
	@echo "  make up-synauthproxy    - Start SynAuthProxy stack (Python FastAPI)"
	@echo "  make up-nginx           - Start nginx stack (nginx + auth backend)"
	@echo "  make up-traefik         - Start Traefik stack (Traefik + ForwardAuth)"
	@echo "  make up-caddy           - Start Caddy stack (Caddy + forward_auth)"
	@echo "  make dev                - Start SynAuthProxy in development mode (live reload)"
	@echo ""
	@echo "Management:"
	@echo "  make down-all           - Stop all running stacks"
	@echo "  make clean-all          - Stop and remove all containers, images, volumes"
	@echo "  make logs-synauthproxy  - View SynAuthProxy logs"
	@echo "  make logs-nginx         - View nginx stack logs"
	@echo "  make logs-traefik       - View Traefik stack logs"
	@echo "  make logs-caddy         - View Caddy stack logs"
	@echo ""
	@echo "Development:"
	@echo "  make lint               - Run ruff linter and formatter"
	@echo "  make lint-check         - Check linting without changes"
	@echo "  make format             - Format code with ruff"
	@echo "  make install-hooks      - Install git pre-commit hooks"
	@echo ""
	@echo "Documentation:"
	@echo "  make serve-guide        - Serve setup guide locally"
	@echo "  make build-guide        - Build HTML setup guide"
	@echo ""
	@echo "Access URLs:"
	Access URLs:
	@echo "  SynAuthProxy:  http://localhost:9000 (RADIUS: 9001)"
	@echo "  nginx:         http://localhost:9010 (RADIUS: 9011)"
	@echo "  Traefik:       http://localhost:9020 (Dashboard: 9021, RADIUS: 9022)"
	@echo "  Caddy:         http://localhost:9030 (RADIUS: 9031)"

# Start SynAuthProxy stack
up-synauthproxy:
	@echo "🚀 Starting SynAuthProxy stack..."
	docker-compose -p synauthproxy -f docker-compose.synauthproxy.yml up -d --build

# Start SynAuthProxy in development mode (with live reload)
dev:
	@echo "🚀 Starting SynAuthProxy in development mode..."
	docker-compose -p synauthproxy -f docker-compose.dev.yml up --build

# Start nginx stack
up-nginx:
	@echo "🚀 Starting nginx stack..."
	docker-compose -p nginx -f docker-compose.nginx.yml up -d --build

# Start Traefik stack
up-traefik:
	@echo "🚀 Starting Traefik stack..."
	docker-compose -p traefik -f docker-compose.traefik.yml up -d --build

# Start Caddy stack
up-caddy:
	@echo "🚀 Starting Caddy stack..."
	docker-compose -p caddy -f docker-compose.caddy.yml up -d --build

# Stop all stacks
down-all:
	@echo "🛑 Stopping all stacks..."
	-docker-compose -p synauthproxy -f docker-compose.synauthproxy.yml down 2>/dev/null || true
	-docker-compose -p nginx -f docker-compose.nginx.yml down 2>/dev/null || true
	-docker-compose -p traefik -f docker-compose.traefik.yml down 2>/dev/null || true
	-docker-compose -p caddy -f docker-compose.caddy.yml down 2>/dev/null || true
	-docker-compose -p synauthproxy -f docker-compose.dev.yml down 2>/dev/null || true

# Clean up all stacks
clean-all:
	@echo "🧹 Cleaning up all stacks..."
	-docker-compose -p synauthproxy -f docker-compose.synauthproxy.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
	-docker-compose -p nginx -f docker-compose.nginx.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
	-docker-compose -p traefik -f docker-compose.traefik.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
	-docker-compose -p caddy -f docker-compose.caddy.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
	-docker-compose -p synauthproxy -f docker-compose.dev.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true

# View logs for specific stacks
logs-synauthproxy:
	docker-compose -p synauthproxy -f docker-compose.synauthproxy.yml logs -f

logs-nginx:
	docker-compose -p nginx -f docker-compose.nginx.yml logs -f

logs-traefik:
	docker-compose -p traefik -f docker-compose.traefik.yml logs -f

logs-caddy:
	docker-compose -p caddy -f docker-compose.caddy.yml logs -f

# Serve the setup guide locally for development
serve-guide:
	@echo "🚀 Starting local server for setup guide..."
	@echo "📖 Open http://localhost:8000/setup-guide.generated.html in your browser"
	@echo "Press Ctrl+C to stop"
	@cd docs && python3 -m http.server 8000

# Build the HTML setup guide from markdown
build-guide:
	@echo "🔧 Building setup-guide from markdown..."
	uv run tools/build_guide.py

# Run ruff linter and formatter
lint:
	@echo "🔍 Running ruff check..."
	cd apps/synauthproxy && uv run ruff check . --fix
	@echo "✨ Running ruff format..."
	cd apps/synauthproxy && uv run ruff format .
	@echo "🔬 Running pyright type checker..."
	cd apps/synauthproxy && uv run pyright

# Check linting without making changes
lint-check:
	@echo "🔍 Running ruff check..."
	cd apps/synauthproxy && uv run ruff check .
	@echo "✨ Running ruff format check..."
	cd apps/synauthproxy && uv run ruff format --check .
	@echo "🔬 Running pyright type checker..."
	cd apps/synauthproxy && uv run pyright

# Format code with ruff
format:
	@echo "✨ Formatting code with ruff..."
	cd apps/synauthproxy && uv run ruff format .

# Install git pre-commit hook
install-hooks:
	@echo "📦 Installing git pre-commit hook..."
	@mkdir -p .git/hooks
	@echo '#!/bin/sh' > .git/hooks/pre-commit
	@echo 'echo "🔍 Running ruff linter..."' >> .git/hooks/pre-commit
	@echo 'cd apps/synauthproxy && uv run ruff check . --fix' >> .git/hooks/pre-commit
	@echo 'if [ $$? -ne 0 ]; then' >> .git/hooks/pre-commit
	@echo '  echo "❌ Ruff check failed. Please fix the issues and try again."' >> .git/hooks/pre-commit
	@echo '  exit 1' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo 'echo "✨ Running ruff formatter..."' >> .git/hooks/pre-commit
	@echo 'cd apps/synauthproxy && uv run ruff format .' >> .git/hooks/pre-commit
	@echo 'if [ $$? -ne 0 ]; then' >> .git/hooks/pre-commit
	@echo '  echo "❌ Ruff format failed. Please fix the issues and try again."' >> .git/hooks/pre-commit
	@echo '  exit 1' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo 'echo "🔬 Running pyright type checker..."' >> .git/hooks/pre-commit
	@echo 'cd apps/synauthproxy && uv run pyright' >> .git/hooks/pre-commit
	@echo 'if [ $$? -ne 0 ]; then' >> .git/hooks/pre-commit
	@echo '  echo "❌ Type check failed. Please fix the issues and try again."' >> .git/hooks/pre-commit
	@echo '  exit 1' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo 'git add -u' >> .git/hooks/pre-commit
	@echo 'echo "✅ Linting passed!"' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed successfully!"