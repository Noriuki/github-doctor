# GitHub Doctor

Ferramenta que analisa repositórios GitHub e gera **relatório de saúde**. **Full-stack:** API FastAPI + **interface web** React.

**Stack:** Python 3.10+, FastAPI, React 18, Vite, Docker Compose.

---

## Frontend (web app)

A aplicação em `frontend/` permite informar um repositório (`owner/repo`), clicar em **Analisar** e ver em tempo real:

- **Health score** (0–100%)
- **Documentação** (nota 0–10, README, badges, instalação, uso)
- **Testes** (pastas detectadas, quantidade de arquivos)
- **CI/CD** (GitHub Actions e workflows)
- **Dependências** (arquivos, total, desatualizadas)

A UI consome a API (`GET /analyze/{owner}/{repo}`), exibe erros com `request_id` quando a API retorna erro estruturado.

**Como rodar o front:** `cd frontend` → `npm install` → `npm run dev` → http://localhost:5173

---

## Features

- **Analyze repository metadata** via GitHub REST API
- **Documentation quality**: detect README presence and quality (size, badges, installation/usage sections)
- **Test detection**: detect test directories (`tests/`, `test/`, `spec/`, etc.)
- **CI/CD detection**: detect GitHub Actions workflows (`.github/workflows/`)
- **Dependency health**: detect dependency files and estimate outdated counts (heuristic)
- **Health score**: weighted overall score (0–100%) from documentation, tests, CI/CD, and dependencies
- **Optional**: CLI, Markdown report export, badge URL for READMEs

### Production-ready extras (observability & ops)

- **Report cache**: in-memory TTL cache (configurable, default 5 min) to reduce GitHub API calls and latency
- **Request ID**: every response includes `X-Request-ID` for tracing; pass it in requests to correlate logs
- **Structured logging**: JSON logs with `request_id`, `method`, `path`, `status_code`, `duration_ms`
- **Health check**: `GET /health` for load balancers and Kubernetes (e.g. liveness/readiness)
- **Metrics**: `GET /metrics` (JSON) and Prometheus exposition format (`Accept: text/plain`) — request counts, cache hit ratio, errors
- **Docker**: multi-stage `Dockerfile` with `HEALTHCHECK` for container orchestration

## Repository Health Metrics

| Metric | Description | How it's scored |
|--------|-------------|-----------------|
| **Documentation** | README presence and quality | 0–10: README exists (2), size >500 bytes (+2), >1500 (+1), has badges (+1), installation section (+2), usage/examples (+2). Capped at 10. |
| **Tests** | Test directories and files | Present = 100%, Missing = 0%, Unknown = 50%. Looks for `tests/`, `test/`, `spec/`, `__tests__/`, etc. |
| **CI/CD** | Automated pipelines | GitHub Actions detected = 100%, none = 0%. Looks for `.github/workflows/*.yml`. |
| **Dependencies** | Dependency files and freshness | Counts deps in `requirements.txt`, `pyproject.toml`, `package.json`, etc. Outdated count is a heuristic (no external API). Score = (1 - outdated/total) × 100. |

**Overall health score** = 25% × (documentation score) + 25% × (tests score) + 25% × (CI/CD score) + 25% × (dependencies score), normalized to 0–100%.

## Estrutura

```
github-doctor/
├── Makefile            # Comandos: make help, make up, make run-api, make run-front, etc.
├── docker-compose.yml   # api (8000) + web (5173)
├── Dockerfile          # Backend (FastAPI)
├── back/                # Backend – Clean Architecture
├── frontend/            # React + Vite
│   ├── src/
│   │   ├── api/         # Cliente HTTP da API
│   │   ├── components/  # Layout, Header, Footer
│   │   ├── pages/       # HomePage (form + resultado)
│   │   └── styles/
│   ├── index.html
│   └── vite.config.js
├── main.py
└── README.md
```

## Architecture Overview (backend)

The backend follows **Clean Architecture** with clear layers:

```
back/
├── domain/           # Entities and value objects (no external deps)
│   └── models.py     # RepositoryHealthReport, DocumentationScore, TestStatus, etc.
├── application/      # Use cases and ports (interfaces)
│   ├── ports.py      # GitHubRepositoryPort (abstract)
│   ├── analyze_repository_use_case.py
│   └── repository_analysis/
│       ├── analyze_repository.py   # Orchestrates analysis steps
│       ├── scoring.py               # Health score computation
│       └── report_formatter.py      # Markdown and badge formatting
├── infrastructure/   # Adapters and cross-cutting concerns
│   ├── github_client.py   # GitHub REST API client (implements GitHubRepositoryPort)
│   ├── cache.py           # In-memory TTL cache for reports
│   └── metrics.py         # Request/cache/error metrics (Prometheus-friendly)
├── interface/        # Entry points (API and CLI)
│   ├── api/          # FastAPI app, routes, middleware
│   │   ├── app.py    # App factory, /health, /metrics
│   │   ├── routes.py # /analyze/{owner}/{repo}
│   │   └── middleware.py  # Request ID, structured logging, metrics timing
│   └── cli.py        # Typer CLI
└── config.py         # Settings (token, cache TTL, etc.)
```

- **Domain**: Pydantic models only; no I/O.
- **Application**: Use cases depend on **ports** (e.g. `GitHubRepositoryPort`); analysis and scoring live in `repository_analysis/`.
- **Infrastructure**: `GitHubClient` implements the port and talks to GitHub REST API.
- **Interface**: FastAPI routes and Typer CLI call the use case and return responses.

## Setup

### Requirements

- Python 3.10+
- (Optional) A [GitHub personal access token](https://github.com/settings/tokens) for higher rate limits (60 vs 5000 req/h unauthenticated)

### Install

```bash
cd github-doctor
pip install -r requirements.txt
```

Optional: install in editable mode with CLI entry point:

```bash
pip install -e .
```

### Environment (optional)

Create a `.env` file or set:

```bash
export GITHUB_DOCTOR_GITHUB_TOKEN=ghp_xxxx   # optional; higher rate limits
export GITHUB_DOCTOR_CACHE_TTL_SECONDS=300   # optional; report cache TTL (default 300)
```

## Como rodar

Os comandos estão centralizados no **Makefile**. Ver todos: `make help`.

**Docker (recomendado):**

```bash
cp .env.example .env   # opcional: configure GITHUB_DOCTOR_GITHUB_TOKEN
make up
```

→ **Web app** http://localhost:5173 · **API** http://localhost:8000 · **Docs** http://localhost:8000/docs

**Local – backend:**

```bash
make install-backend    # uma vez
make run-api           # sobe a API na porta 8000
```

**Local – frontend:**

```bash
make install-front     # uma vez
make run-front        # sobe o front na porta 5173 (proxy para a API)
```

**CLI (analisar repositório):**

```bash
make install-backend   # ou: pip install -e .
make doctor REPO=octocat/Hello-World
```

**Verificação do pipeline (mock):**

```bash
make verify
```

**Limpeza:**

```bash
make clean      # __pycache__, node_modules, frontend/dist
make clean-all  # + remove .venv
```

### Docker (só API, sem Make)

```bash
docker build -t github-doctor .
docker run -p 8000:8000 -e GITHUB_DOCTOR_GITHUB_TOKEN=ghp_xxx github-doctor
```

## Example API Requests

### Health & metrics

```bash
curl -s http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}

curl -s http://localhost:8000/metrics
# {"requests_total":42,"cache_hits":10,"cache_misses":5,"cache_hit_ratio":0.67,...}

curl -s -H "Accept: text/plain" http://localhost:8000/metrics
# Prometheus exposition format for scraping
```

### GET /analyze/{owner}/{repo}

Returns the repository health report as JSON.

```bash
curl -s "http://localhost:8000/analyze/octocat/Hello-World" | jq
```

Example response (structure):

```json
{
  "repository": "octocat/Hello-World",
  "documentation": {
    "score": 8,
    "has_readme": true,
    "readme_size_bytes": 1234,
    "has_badges": false,
    "has_installation": true,
    "has_usage": true,
    "message": "README found (1234 bytes), score 8/10"
  },
  "tests": {
    "present": "missing",
    "test_dirs": [],
    "test_files_count": 0,
    "message": "Missing"
  },
  "cicd": {
    "detected": false,
    "type": "none",
    "workflow_files": [],
    "message": "No CI/CD detected"
  },
  "dependencies": {
    "total_dependencies": 0,
    "outdated_count": 0,
    "dependency_files": [],
    "message": "No dependency files found"
  },
  "health_score": 72.0
}
```

### GET /analyze/{owner}/{repo}/report.md

Returns the same report as **Markdown** (plain text).

```bash
curl -s "http://localhost:8000/analyze/octocat/Hello-World/report.md"
```

### GET /analyze/{owner}/{repo}/badge

Returns a badge URL and Markdown snippet for the health score (e.g. for shields.io-style badges).

```bash
curl -s "http://localhost:8000/analyze/octocat/Hello-World/badge" | jq
```

## Example Report Output (text)

```
# Repository Health Report

**Repository:** user/project

## Summary

- **Documentation:** 8/10
- **Tests:** Missing
- **CI/CD:** GitHub Actions detected
- **Dependencies:** 3 outdated

## Health Score: 72%

---

### Documentation
- README: Yes
- Size: 2048 bytes
- Badges: Yes
- Installation section: Yes
- Usage section: Yes

### Tests
- Status: missing
- Directories: None
- Test files (sample): 0

### CI/CD
- Detected: True
- Type: github_actions
- Workflows: ci.yml, deploy.yml

### Dependencies
- Files: requirements.txt
- Total dependencies: 12
- Outdated: 3
```

## CLI (optional)

If installed with `pip install -e .`:

```bash
github-doctor analyze owner/repo
github-doctor analyze owner/repo --markdown
github-doctor analyze owner/repo --markdown --output report.md
```

Or run the module:

```bash
python -m back.interface.cli analyze owner/repo
python -m back.interface.cli analyze owner/repo -m -o report.md
```

## GitHub Repo Badges

Use the `/analyze/{owner}/{repo}/badge` endpoint to get a `markdown` field you can paste into your README. The badge reflects the current health score (e.g. 72%) with a color (green/yellow/red) based on the score.

## Goal of the Project

- **API integration**: GitHub REST API for repo metadata, file contents, and directory listing.
- **Backend architecture**: Clean Architecture with domain, application, infrastructure, and interface layers.
- **Developer tooling**: Health metrics, scoring, optional CLI, Markdown export, and badges for use in READMEs.

## License

MIT
