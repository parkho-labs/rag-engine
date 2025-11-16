# RAG Engine Docker Makefile
# Convenient shortcuts for Docker operations

.PHONY: help setup env build up down logs restart clean backup

# Default target
help:
	@echo "RAG Engine Docker Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup & Configuration:"
	@echo "  make setup          - Interactive setup (runs docker-start.sh)"
	@echo "  make env            - Create .env file from template"
	@echo ""
	@echo "Service Management:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View all logs"
	@echo "  make restart        - Restart all services"
	@echo "  make build          - Rebuild and start all services"
	@echo ""
	@echo "Individual Services:"
	@echo "  make up-postgres    - Start PostgreSQL only"
	@echo "  make up-minio       - Start MinIO only"
	@echo "  make up-qdrant      - Start Qdrant only"
	@echo "  make up-rag         - Start RAG Engine only (+ dependencies)"
	@echo ""
	@echo "Service-Specific Logs:"
	@echo "  make logs-postgres  - View PostgreSQL logs"
	@echo "  make logs-minio     - View MinIO logs"
	@echo "  make logs-qdrant    - View Qdrant logs"
	@echo "  make logs-rag       - View RAG Engine logs"
	@echo ""
	@echo "Database Operations:"
	@echo "  make db-connect     - Connect to PostgreSQL"
	@echo "  make db-schema      - Initialize database schema"
	@echo ""
	@echo "Maintenance:"
	@echo "  make status         - Show service status"
	@echo "  make health         - Check service health"
	@echo "  make backup         - Backup volumes"
	@echo "  make clean          - Remove containers (keeps volumes)"
	@echo "  make clean-all      - Remove containers and volumes (⚠️  deletes data)"
	@echo ""
	@echo "Other:"
	@echo "  make ps             - List all containers"
	@echo "  make shell          - Open shell in RAG Engine container"

# Setup
setup:
	@./docker-start.sh

env:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Created .env file from template"; \
		echo "⚠️  Please edit .env with your API keys"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# All Services
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

build:
	docker compose up -d --build

# Individual Services
up-postgres:
	docker compose up -d postgres

up-minio:
	docker compose up -d minio

up-qdrant:
	docker compose up -d qdrant

up-rag:
	docker compose up -d rag-engine

# Service-specific logs
logs-postgres:
	docker compose logs -f postgres

logs-minio:
	docker compose logs -f minio

logs-qdrant:
	docker compose logs -f qdrant

logs-rag:
	docker compose logs -f rag-engine

# Database operations
db-connect:
	docker compose exec postgres psql -U postgres -d rag_engine

db-schema:
	docker compose exec -T postgres psql -U postgres -d rag_engine < src/database/schema.sql
	@echo "✅ Database schema initialized"

# Maintenance
status:
	docker compose ps

health:
	@echo "Checking RAG Engine..."
	@curl -sf http://localhost:8000/health | jq . || echo "❌ RAG Engine not responding"
	@echo ""
	@echo "Checking Qdrant..."
	@curl -sf http://localhost:6333/healthz || echo "❌ Qdrant not responding"
	@echo ""
	@echo "Checking MinIO..."
	@curl -sf http://localhost:9000/minio/health/live || echo "❌ MinIO not responding"

backup:
	@mkdir -p backups
	@DATE=$$(date +%Y%m%d-%H%M%S); \
	echo "Creating backup at backups/rag-backup-$$DATE.tar.gz"; \
	docker run --rm \
		-v rag-qdrant-data:/qdrant \
		-v rag-postgres-data:/postgres \
		-v $$(pwd)/backups:/backup \
		alpine tar czf /backup/rag-backup-$$DATE.tar.gz /qdrant /postgres
	@echo "✅ Backup complete"

clean:
	docker compose down
	@echo "✅ Containers removed (volumes preserved)"

clean-all:
	@echo "⚠️  WARNING: This will delete all data!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	docker compose down -v
	@echo "✅ Containers and volumes removed"

# Other utilities
ps:
	docker compose ps

shell:
	docker compose exec rag-engine bash
