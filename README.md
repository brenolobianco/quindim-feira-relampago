# Feira Relâmpago

API da feira relâmpago de livros: catálogo, reserva com expiração, confirmação com desconto e webhook de pagamento. Python 3.12, Flask, MongoDB (pymongo) e Pydantic.

## Como rodar

Precisa de Docker.

```
cp .env.example .env
docker compose up --build
```

A tela sobe em http://localhost:3000 e a API em http://localhost:8000, com o seed aplicado. Para conferir a API: `curl http://localhost:8000/healthz`.

## Frontend em modo de desenvolvimento

Com a API no ar, precisa de Node 22:

```
cd web
npm install
npm run dev
```

Abre em http://localhost:3000. A URL da API fica só no servidor do Nuxt (`NUXT_API_URL`, padrão `http://localhost:8000`).

## Como testar

Os testes rodam contra um MongoDB de verdade em `localhost:27017`. O jeito mais fácil é subir só o Mongo do Compose:

```
docker compose up -d mongo
cd api
uv run pytest
```

Os testes usam o banco `feira_teste` e apagam esse banco a cada teste. O teste de concorrência (`tests/test_concorrencia.py`) sobe processos de verdade disputando o mesmo estoque.

Lint: `uv run ruff check` e `uv run ruff format --check`, dentro de `api/`.
