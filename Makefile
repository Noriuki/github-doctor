# GitHub Doctor - comandos via Make
# Uso: make [target]. Default: make help
#
# O backend usa venv em .venv (evita PEP 668 / externally-managed-environment no Linux).

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

.PHONY: help venv install install-backend install-front run run-api run-front \
	up down build-docker logs clean clean-all verify

# Default target
help:
	@echo "GitHub Doctor - comandos disponíveis:"
	@echo ""
	@echo "  make venv           Cria .venv (python3 -m venv) — use antes do install-backend"
	@echo "  make install        Instala dependências (backend + frontend)"
	@echo "  make install-backend Instala deps Python em .venv (cria o venv se não existir)"
	@echo "  make install-front  Instala apenas dependências do frontend"
	@echo ""
	@echo "  make run-api        Sobe a API (uvicorn) na porta 8000 (usa .venv)"
	@echo "  make run-front      Sobe o frontend (Vite) na porta 5173"
	@echo "  make run            Sobe API e frontend (dois processos)"
	@echo ""
	@echo "  make up             Docker Compose up --build"
	@echo "  make down           Docker Compose down"
	@echo "  make build-docker   Build das imagens (api + web)"
	@echo "  make logs           Docker Compose logs -f"
	@echo ""
	@echo "  make verify         Roda script de verificação do pipeline (mock)"
	@echo ""
	@echo "  make clean          Remove __pycache__, .pyc, frontend/node_modules, frontend/dist"
	@echo "  make clean-all      clean + .venv (se existir)"
	@echo ""

# --- venv (PEP 668: não use pip no Python do sistema) ---
venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

# --- Instalação ---
install: install-backend install-front

install-backend: venv
	$(PIP) install -r requirements.txt
	@echo "Backend: dependências instaladas em $(VENV)/"

install-front:
	cd frontend && npm install
	@echo "Frontend: dependências instaladas"

# --- Execução local ---
run-api:
	@test -f $(VENV)/bin/uvicorn || (echo "Execute antes: make install-backend" && exit 1)
	cd "$(CURDIR)" && $(VENV)/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

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

# --- Verificação ---
verify:
	@test -f $(PY) || python3 -m venv $(VENV)
	@test -f $(VENV)/bin/uvicorn || $(PIP) install -r requirements.txt
	$(PY) scripts/verify_flow.py

# --- Limpeza ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/node_modules frontend/dist
	@echo "Limpeza concluída"

clean-all: clean
	rm -rf .venv venv
	@echo "Limpeza total concluída"
