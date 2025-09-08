# Backend PDV3 (FastAPI)

Backend para o PDV3 híbrido (offline/online), oferecendo API para autenticação, sincronização e consulta.

## Requisitos
- Python 3.10+
- PostgreSQL

## Instalação
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
```

## Variáveis de Ambiente
Crie um arquivo `.env` (ou configure no provedor) com:
```
DATABASE_URL=postgresql+asyncpg://postgres:senha@host:5432/railway
JWT_SECRET=troque_este_segredo
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

No Railway, use as variáveis fornecidas (DATABASE_URL, POSTGRES_*). Para ambientes públicos, prefira `DATABASE_PUBLIC_URL` com SSL.

## Executando
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints
- GET `/healthz`
- POST `/auth/login`
- POST `/sync/push`
- POST `/sync/pull`

## Notas
- O backend usa SQLAlchemy 2.x (async) com `asyncpg`.
- JWT para autenticação.
- Esquema de dados com IDs UUID e campos de auditoria (created_at/updated_at/deleted_at).
