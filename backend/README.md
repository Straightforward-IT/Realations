# Realations Backend

A scalable, multi-tenant **contact / relation management** backend implementing the
architectural recommendations in [`../CRM Database System Recommendations.pdf`](../CRM%20Database%20System%20Recommendations.pdf).

The service is intentionally small enough to run on a single PostgreSQL node
today, while being structured so each subsystem can be swapped for the
purpose-built engines the blueprint recommends as the platform grows
(TimescaleDB / ClickHouse for telemetry, Typesense for search, pgvector /
Pinecone for semantic retrieval, Redis for caching, etc.).

---

## Feature summary

| Concern              | Implementation |
| -------------------- | -------------- |
| Web framework        | FastAPI (Pydantic v2, async-ready) |
| ORM / migrations     | SQLAlchemy 2 + Alembic |
| Primary store        | PostgreSQL (SQLite for tests) |
| Multi-tenancy        | Shared schema + **PostgreSQL Row-Level Security** + per-request `app.current_tenant` GUC |
| Custom fields        | JSONB `custom_attributes` column on every CRM entity ("Dynamic Attributes Pattern") |
| Identity             | JWT bearer tokens; tenant id baked into the token |
| Licensing            | `Plan` + `Subscription` tables, code-defined catalogue (`free` / `starter` / `business` / `enterprise`), enforced via FastAPI dependencies |
| Integrations         | Pluggable provider registry — Microsoft Graph, Asana, Pipedrive, Zapier (generic outbound webhooks) |
| Inbound webhooks     | Per-connection receiver dispatched to provider `handle_inbound` |
| Outbound webhooks    | HMAC-signed JSON envelopes delivered by the central `EventBus` |

---

## Mapping to the architectural blueprint

| PDF section | Where it lives in this codebase |
| ----------- | ------------------------------- |
| *Core Operational Data: Relational Foundation* | `app/models/{tenant,user,company,contact,deal,activity,ticket}.py` |
| *Multi-tenancy: Shared Schema + RLS* | `app/db/session.py::set_tenant_context`, `migrations/versions/0002_rls_policies.py` |
| *Dynamic Attributes Pattern (JSONB)* | `app/db/base.py::JSONB_`, every `custom_attributes` column |
| *Caching, Microservices & Real-Time Pipelines* | `app/integrations/base.py::EventBus` (extension point — swap for Kafka/Redis Streams in production) |
| *Data Integration, Synchronisation & Enrichment* | `app/integrations/` — provider plugins + outbound webhooks |
| *Polyglot persistence* | Activity / search / vector workloads are isolated in dedicated modules so they can move off PostgreSQL without touching the relational core |

---

## Running locally

### With Docker

```bash
cd backend
docker compose up --build
```

The API will be available on `http://localhost:8000` and migrations are
applied automatically on startup.

### Without Docker (SQLite, fastest path)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

The default `REALATIONS_DATABASE_URL` is SQLite. Switch to PostgreSQL by
setting `REALATIONS_DATABASE_URL` (see `.env.example`) — only PostgreSQL
enables Row-Level Security policies.

---

## API tour

All routes are mounted under `/api/v1`.

```
POST  /auth/register             # create tenant + first admin + assign plan
POST  /auth/login                # exchange (tenant_slug, email, password) for JWT
GET   /subscriptions/plans       # public plan catalogue
GET   /subscriptions/me          # currently active subscription
PUT   /subscriptions/me          # admin-only: change plan
GET   /companies                 # CRUD for the standard CRM entities
POST  /contacts                  # license-gated: capacity + custom_fields feature
POST  /deals
POST  /activities
POST  /tickets
GET   /integrations/providers    # available integration plugins
POST  /integrations/connections  # license-gated: feature flag + capacity
POST  /webhooks                  # outbound webhook subscription (Zapier-style)
POST  /webhooks/inbound/{id}     # generic inbound receiver per connection
```

`/healthz` exposes a basic liveness probe.

---

## Multi-tenant isolation

Every tenant-scoped table carries a `tenant_id` column. On PostgreSQL, the
Alembic migration `0002_rls_policies` enables `ROW LEVEL SECURITY` and a
`tenant_isolation` policy that filters using
`current_setting('app.current_tenant')`. The API dependency `get_current_user`
sets this GUC via `SET LOCAL` after validating the JWT, so any forgotten
`WHERE tenant_id = …` in application code remains harmless.

Tests run against SQLite (which has no RLS); tenant isolation there is
enforced exclusively by the `crud.*_for_tenant` helpers, which always filter
by `tenant_id` in addition to the primary key.

---

## Licensing & subscription tiers

Plans are seeded from `app/licensing/catalog.py` on first read of
`/subscriptions/plans`. The included tiers are illustrative — additional or
custom plans can be created directly in the database without code changes.

The `LicenseChecker` dependency provides:

* `require_feature("integration:microsoft_graph")` — gates routes by feature flag.
* `require_capacity_for_user / contact / integration()` — enforces resource caps.

These checks raise `LicenseError`, which the FastAPI handler converts to
HTTP 402 Payment Required.

---

## Adding a new integration provider

1. Create a subclass of `IntegrationProvider` in `app/integrations/providers/`.
2. Decorate it with `@register_provider`.
3. Set `slug`, `display_name`, `feature_key`, and `required_config_keys`.
4. Implement the hooks you need (`on_event`, `handle_inbound`, …).
5. Add a feature flag entry in `app/licensing/catalog.py` if needed.

That's it — the provider becomes available via `/integrations/providers`,
visible to the EventBus, and reachable through `/webhooks/inbound/{id}`.

---

## Tests

```bash
cd backend
pip install -e '.[dev]'
pytest
```

The suite covers tenant registration & login, tenant data isolation, plan
upgrades, licensing enforcement (feature flags + capacity), and the
integration event bus (provider dispatch + outbound webhook signatures).
