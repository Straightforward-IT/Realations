# AGENTS

## Project Scope

- This workspace currently contains a FastAPI backend in [backend/README.md](backend/README.md). Start there for setup, API surface, and the mapping to the architectural blueprint in [CRM Database System Recommendations.pdf](CRM%20Database%20System%20Recommendations.pdf).
- Prefer linking to existing repo documentation instead of duplicating it in code comments or generated docs.

## Working Directory And Commands

- Run backend commands from `backend/`.
- Install dev dependencies with `pip install -e '.[dev]'`.
- Run tests with `pytest`.
- Run lint with `ruff check .`.
- Apply migrations with `alembic upgrade head`.
- Start local development with `uvicorn app.main:app --reload`.
- Use `docker compose up --build` for the PostgreSQL-backed local stack.

## Code Layout

- `backend/app/api/`: FastAPI dependencies and route modules.
- `backend/app/models/`: SQLAlchemy models for tenant, auth, CRM entities, integrations, and subscriptions.
- `backend/app/schemas/`: Pydantic request/response models.
- `backend/app/services/`: tenant-aware CRUD helpers and event publishing.
- `backend/app/db/`: engine/session setup, shared model mixins, and tenant context helpers.
- `backend/app/licensing/`: plan catalogue and runtime license enforcement.
- `backend/app/integrations/`: provider registry, provider implementations, and webhook/event integration points.
- `backend/tests/`: FastAPI integration-style tests, fixtures, and helper factories.

## Repo-Specific Conventions

- Preserve tenant isolation. Tenant-scoped access should continue to flow through [backend/app/api/deps.py](backend/app/api/deps.py), [backend/app/db/session.py](backend/app/db/session.py), and [backend/app/services/crud.py](backend/app/services/crud.py).
- Treat PostgreSQL RLS as the production isolation layer, but remember tests and the default fast local setup use SQLite, where isolation is enforced in application code rather than the database.
- For tenant-scoped CRUD, reuse the helpers in [backend/app/services/crud.py](backend/app/services/crud.py) instead of open-coding tenant filters.
- Keep license enforcement at the route or request boundary with [backend/app/licensing/checker.py](backend/app/licensing/checker.py) before performing writes or exposing gated features.
- CRM entities use `custom_attributes` for dynamic fields. If a route accepts or mutates those fields, enforce the relevant feature flag as existing routes do.
- Integration providers are registered by import side effect. New providers belong under `backend/app/integrations/providers/`, should follow the existing provider pattern, and may also need plan feature entries in [backend/app/licensing/catalog.py](backend/app/licensing/catalog.py).

## Testing Guidance

- Tests use the fixtures in [backend/tests/conftest.py](backend/tests/conftest.py), which patch the app to an in-memory SQLite database and seed plans per test.
- Reuse helpers in [backend/tests/factories.py](backend/tests/factories.py) for tenant registration, login, and common setup before adding bespoke test wiring.
- Because SQLite does not enforce PostgreSQL RLS, add or keep explicit tenant-isolation assertions when touching multi-tenant behavior.

## Change Guidance For Agents

- Make focused changes inside `backend/`; there is no frontend in this workspace today.
- Prefer updating existing route, schema, model, and test patterns instead of introducing new abstractions.
- Do not edit old Alembic revisions unless the task is specifically about migration repair. Add a new migration for schema changes.
- When changing auth, tenant context, or licensing behavior, run the relevant tests in `backend/tests/` before broadening scope.
- If you need details that are already documented, link to [backend/README.md](backend/README.md) or [backend/pyproject.toml](backend/pyproject.toml) instead of copying large sections.
