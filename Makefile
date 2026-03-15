# GitHub Doctor - comandos via Make
# Uso: make [target]. Default: make help

.PHONY: help install install-backend install-front run run-api run-front \
	up down build-docker logs clean clean-all verify doctor

# Default target
help:
	@echo "GitHub Doctor - comandos disponíveis:"
	@echo ""
	@echo "  make install        Instala dependências (backend + frontend)"
	@echo "  make install-backend Instala apenas dependências Python"
	@echo "  make install-front  Instala apenas dependências do frontend"
	@echo ""
	@echo "  make run-api        Sobe a API (uvicorn) na porta 8000"
	@echo "  make run-front      Sobe o frontend (Vite) na porta 5173"
	@echo "  make run            Sobe API e frontend (dois processos)"
	@echo ""
	@echo "  make up             Docker Compose up --build"
	@echo "  make down           Docker Compose down"
	@echo "  make build-docker   Build das imagens (api + web)"
	@echo "  make logs           Docker Compose logs -f"
	@echo ""
	@echo "  make doctor REPO=owner/repo  CLI: analisa repositório (ex: make doctor REPO=octocat/Hello-World)"
	@echo "  make verify         Roda script de verificação do pipeline (mock)"
	@echo ""
	@echo "  make clean          Remove __pycache__, .pyc, frontend/node_modules, frontend/dist"
	@echo "  make clean-all      clean + .venv (se existir)"
	@echo ""

# --- Instalação ---
install: install-backend install-front

install-backend:
	pip install -r requirements.txt
	@echo "Backend: dependências instaladas. Opcional: pip install -e . (para CLI)"

install-front:
	cd frontend && npm install
	@echo "Frontend: dependências instaladas"

# --- Execução local ---
run-api:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-front:
	cd frontend && npm run dev

run:
	@echo "Para rodar localmente, use dois terminais:"
	@echo "  Terminal 1: make run-api"
	@echo "  Terminal 2: make run-front"
	@echo "Ou em um só ambiente: make up  (Docker Compose)"

# --- Docker ---
up:
	docker compose up --build

down:
	docker compose down

build-docker:
	docker compose build

logs:
	docker compose logs -f

# --- CLI e verificação ---
doctor:
	@if [ -z "$(REPO)" ]; then echo "Uso: make doctor REPO=owner/repo"; exit 1; fi
	python -m back.interface.cli analyze $(REPO)

verify:
	python scripts/verify_flow.py

# --- Limpeza ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/node_modules frontend/dist
	@echo "Limpeza concluída"

clean-all: clean
	rm -rf .venv venv
	@echo "Limpeza total concluída"
