# Plataforma de Análise de Comentários e Detecção de Bots no YouTube

Sistema de coleta, limpeza, anotação e análise de comentários do YouTube para detecção de bots, desenvolvido no **DaVint Lab (Data Visualization and Interaction) / PUCRS** como projeto de Iniciação Científica financiado pelo **CNPq**.

## Visão geral

A plataforma permite que pesquisadores:
1. Coletem comentários de vídeos do YouTube via API
2. Filtrem usuários suspeitos com critérios estatísticos e comportamentais
3. Anotem comentários colaborativamente como `bot` ou `humano`
4. Resolvam conflitos de classificação via painel do administrador
5. Gerenciem todos os dados da plataforma num catálogo centralizado
6. Visualizem métricas e gráficos sobre os dados anotados

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy · Alembic |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS v3 · Plotly.js |
| Banco | PostgreSQL (Neon serverless em produção, Docker Compose em dev) |
| Auth | JWT (PyJWT) · bcrypt (passlib) · Rate limiting (slowapi) |
| Deploy | Vercel Pro (dois projetos separados: frontend e backend) |
| CI/CD | GitHub Actions · Dependabot |
| Qualidade | Ruff · Bandit · pip-audit · ESLint · Prettier |

## Estrutura do repositório

```
plataformaYouTubeBots/
├── backend/
│   ├── main.py               # entrypoint Vercel (@vercel/python)
│   ├── vercel.json
│   ├── requirements.txt
│   ├── routers/              # endpoints por User Story
│   │   ├── auth.py           # US-01 — autenticação
│   │   ├── collect.py        # US-02 — coleta
│   │   ├── clean.py          # US-03 — limpeza e seleção
│   │   ├── annotate.py       # US-04 — anotação
│   │   ├── review.py         # US-05 — revisão de conflitos
│   │   └── data.py           # US-07 — catálogo de dados
│   ├── services/             # lógica de negócio
│   ├── models/               # modelos SQLAlchemy
│   ├── schemas/              # modelos Pydantic (entrada/saída)
│   ├── core/                 # configurações compartilhadas (rate limiting)
│   └── tests/                # testes Pytest
├── frontend/
│   └── src/
│       ├── pages/            # telas por US
│       │   ├── Auth/         # login
│       │   ├── Home/         # página inicial com cards do pipeline
│       │   ├── Collect/      # US-02
│       │   ├── Clean/        # US-03
│       │   ├── Annotate/     # US-04
│       │   ├── Review/       # US-05
│       │   ├── Data/         # US-07 — catálogo de dados
│       │   └── Users/        # gestão de usuários (admin)
│       ├── components/       # componentes reutilizáveis (PageHeader, StatusBadge, etc.)
│       ├── hooks/            # lógica isolada (useCollect, useClean, useData, etc.)
│       ├── contexts/         # AuthContext (token, user, role)
│       └── api/              # chamadas ao backend (DIP — componentes nunca fazem fetch)
├── .claude/                  # contexto para agentes de IA
│   ├── backend.md            # padrões de backend
│   ├── frontend.md           # padrões de frontend
│   ├── ux-ui.md              # heurísticas de UX/UI
│   └── skills/               # specs de implementação por US
├── .github/
│   ├── workflows/ci.yml      # pipeline de CI/CD
│   ├── dependabot.yml        # atualizações automáticas de segurança
│   └── CONTRIBUTING.md       # guia de contribuição (Gitflow, Conventional Commits)
├── AGENTS.md                 # instruções para agentes de IA
├── CLAUDE.md                 # convenções do projeto
└── docker-compose.yml        # PostgreSQL local para desenvolvimento
```

## User Stories

| US | Descrição | Rota backend | Status |
|---|---|---|---|
| US-00 | Infraestrutura, CI/CD e segurança | — | Concluída |
| US-01 | Autenticação e gestão de usuários | `/auth`, `/users` | Concluída |
| US-02 | Coleta de comentários do YouTube | `/collect` | Concluída |
| US-03 | Limpeza e seleção de dataset | `/clean` | Concluída |
| US-04 | Anotação de comentários | `/annotate` | Concluída |
| US-05 | Desempate de conflitos (admin) | `/review` | Concluída |
| US-06 | Dashboard de análise | `/dashboard` | Pendente |
| US-07 | Catálogo centralizado de dados | `/data` | Concluída |

## Desenvolvimento local

### Pré-requisitos

- Python 3.11+
- Node.js 22+ (LTS)
- Docker (para o banco local)

### Backend

```bash
docker compose up -d                     # sobe PostgreSQL local

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env                     # preencher SECRET_KEY

# Aplicar migrations e rodar
DATABASE_URL=postgresql://davint:davint@localhost:5432/davint alembic upgrade head
DATABASE_URL=postgresql://davint:davint@localhost:5432/davint uvicorn main:app --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local               # preencher VITE_API_URL=http://localhost:8000
npm run dev                              # http://localhost:3000
```

### Testes

```bash
cd backend
DATABASE_URL=postgresql://davint:davint@localhost:5432/davint pytest
```

O banco de testes (`davint_test`) é criado automaticamente pelo conftest. Cobertura mínima exigida: 80%.

## Variáveis de ambiente

| Variável | Onde | Descrição |
|---|---|---|
| `DATABASE_URL` | Backend | URL do PostgreSQL (Neon em produção, Docker em dev) |
| `SECRET_KEY` | Backend | Chave de assinatura dos JWTs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Expiração do access token (padrão: 60) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Backend | Expiração do refresh token (padrão: 7) |
| `CORS_ORIGINS` | Backend | Origens permitidas (padrão: http://localhost:3000) |
| `VITE_API_URL` | Frontend | URL do backend em produção |

Em produção, `DATABASE_URL` é injetada automaticamente pela integração Vercel + Neon.
As demais são configuradas em **Vercel Dashboard > Environment Variables**.

## Branches (Gitflow)

```
main         produção — releases estáveis
dev          integração — alvo de todo PR de feature
feature/*    desenvolvimento de US ou tarefa
fix/*        correção de bug
hotfix/*     correção urgente em produção
chore/*      infra, CI, dependências
docs/*       documentação
```

Ver [CONTRIBUTING.md](.github/CONTRIBUTING.md) para o fluxo completo.

## Qualidade e segurança

O CI executa automaticamente em todo push e PR:

- **Backend:** Ruff (lint + format) · Bandit (análise estática) · pip-audit (vulnerabilidades) · Pytest (cobertura >= 80%)
- **Frontend:** ESLint · Prettier · tsc --noEmit · npm audit

Dependabot monitora dependências de `pip` e `npm` semanalmente com PRs automáticos para atualizações de segurança.

## Financiamento

Este projeto é financiado pelo **CNPq** (Conselho Nacional de Desenvolvimento Científico e Tecnológico) como bolsa de Iniciação Científica, vinculada ao **DaVint Lab (Data Visualization and Interaction) — PUCRS**.

Desenvolvido com auxílio da ferramenta de IA **Claude** (Anthropic).

## Licença

Projeto acadêmico — DaVint Lab / PUCRS. Uso restrito à pesquisa científica.
