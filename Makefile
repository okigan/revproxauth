# Makefile for Synology authentication proxy Docker operations

.PHONY: all up down build logs restart clean serve-guide lint format lint-check install-hooks

all: build up

# Start the service in detached mode
up:
	docker-compose up -d --build

# Stop and remove the service
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Restart the service
restart:
	docker-compose restart

# Clean up: stop and remove containers, images, and volumes
clean:
	docker-compose down --rmi all --volumes --remove-orphans

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
	uv run ruff check . --fix
	@echo "✨ Running ruff format..."
	uv run ruff format .
	@echo "🔬 Running pyright type checker..."
	uv run pyright

# Check linting without making changes
lint-check:
	@echo "🔍 Running ruff check..."
	uv run ruff check .
	@echo "✨ Running ruff format check..."
	uv run ruff format --check .
	@echo "🔬 Running pyright type checker..."
	uv run pyright

# Format code with ruff
format:
	@echo "✨ Formatting code with ruff..."
	uv run ruff format .

# Install git pre-commit hook
install-hooks:
	@echo "📦 Installing git pre-commit hook..."
	@mkdir -p .git/hooks
	@echo '#!/bin/sh' > .git/hooks/pre-commit
	@echo 'echo "🔍 Running ruff linter..."' >> .git/hooks/pre-commit
	@echo 'uv run ruff check . --fix' >> .git/hooks/pre-commit
	@echo 'if [ $$? -ne 0 ]; then' >> .git/hooks/pre-commit
	@echo '  echo "❌ Ruff check failed. Please fix the issues and try again."' >> .git/hooks/pre-commit
	@echo '  exit 1' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo 'echo "✨ Running ruff formatter..."' >> .git/hooks/pre-commit
	@echo 'uv run ruff format .' >> .git/hooks/pre-commit
	@echo 'if [ $$? -ne 0 ]; then' >> .git/hooks/pre-commit
	@echo '  echo "❌ Ruff format failed. Please fix the issues and try again."' >> .git/hooks/pre-commit
	@echo '  exit 1' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo 'echo "🔬 Running pyright type checker..."' >> .git/hooks/pre-commit
	@echo 'uv run pyright' >> .git/hooks/pre-commit
	@echo 'if [ $$? -ne 0 ]; then' >> .git/hooks/pre-commit
	@echo '  echo "❌ Type check failed. Please fix the issues and try again."' >> .git/hooks/pre-commit
	@echo '  exit 1' >> .git/hooks/pre-commit
	@echo 'fi' >> .git/hooks/pre-commit
	@echo 'git add -u' >> .git/hooks/pre-commit
	@echo 'echo "✅ Linting passed!"' >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed successfully!"