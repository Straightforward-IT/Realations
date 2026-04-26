"""Canonical plan catalogue.

These definitions are the *source of truth* for the platform's standard tiers.
``seed_plans`` upserts them into the ``plans`` table at startup so operators
get a sensible default catalogue without manual SQL.

Custom plans can still be created directly in the database (e.g. by a billing
service) and will be honoured by :class:`~app.licensing.checker.LicenseChecker`
exactly the same way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.models.subscription import Plan


@dataclass(frozen=True)
class PlanDefinition:
    code: str
    name: str
    max_users: int | None
    max_contacts: int | None
    max_integrations: int | None
    price_cents: int
    features: dict[str, Any] = field(default_factory=dict)
    currency: str = "USD"


# Capability flags consumed by LicenseChecker.require_feature().
# Keep the keys stable — they appear in API decorators / dependency calls.
F_CUSTOM_FIELDS = "custom_fields"
F_WEBHOOKS = "webhooks"
F_INTEGRATIONS_MS_GRAPH = "integration:microsoft_graph"
F_INTEGRATIONS_ASANA = "integration:asana"
F_INTEGRATIONS_PIPEDRIVE = "integration:pipedrive"
F_INTEGRATIONS_ZAPIER = "integration:zapier"
F_API_ACCESS = "api_access"
F_AUDIT_LOG = "audit_log"


PLAN_CATALOG: tuple[PlanDefinition, ...] = (
    PlanDefinition(
        code="free",
        name="Free",
        max_users=2,
        max_contacts=500,
        max_integrations=1,
        price_cents=0,
        features={
            F_CUSTOM_FIELDS: False,
            F_WEBHOOKS: False,
            F_INTEGRATIONS_MS_GRAPH: False,
            F_INTEGRATIONS_ASANA: False,
            F_INTEGRATIONS_PIPEDRIVE: False,
            F_INTEGRATIONS_ZAPIER: True,
            F_API_ACCESS: True,
            F_AUDIT_LOG: False,
        },
    ),
    PlanDefinition(
        code="starter",
        name="Starter",
        max_users=10,
        max_contacts=10_000,
        max_integrations=3,
        price_cents=2_900,
        features={
            F_CUSTOM_FIELDS: True,
            F_WEBHOOKS: True,
            F_INTEGRATIONS_MS_GRAPH: False,
            F_INTEGRATIONS_ASANA: True,
            F_INTEGRATIONS_PIPEDRIVE: True,
            F_INTEGRATIONS_ZAPIER: True,
            F_API_ACCESS: True,
            F_AUDIT_LOG: False,
        },
    ),
    PlanDefinition(
        code="business",
        name="Business",
        max_users=50,
        max_contacts=100_000,
        max_integrations=10,
        price_cents=9_900,
        features={
            F_CUSTOM_FIELDS: True,
            F_WEBHOOKS: True,
            F_INTEGRATIONS_MS_GRAPH: True,
            F_INTEGRATIONS_ASANA: True,
            F_INTEGRATIONS_PIPEDRIVE: True,
            F_INTEGRATIONS_ZAPIER: True,
            F_API_ACCESS: True,
            F_AUDIT_LOG: True,
        },
    ),
    PlanDefinition(
        code="enterprise",
        name="Enterprise",
        max_users=None,
        max_contacts=None,
        max_integrations=None,
        price_cents=49_900,
        features={
            F_CUSTOM_FIELDS: True,
            F_WEBHOOKS: True,
            F_INTEGRATIONS_MS_GRAPH: True,
            F_INTEGRATIONS_ASANA: True,
            F_INTEGRATIONS_PIPEDRIVE: True,
            F_INTEGRATIONS_ZAPIER: True,
            F_API_ACCESS: True,
            F_AUDIT_LOG: True,
        },
    ),
)


def seed_plans(session: Session) -> None:
    """Upsert the canonical plan catalogue into the database."""
    existing = {p.code: p for p in session.query(Plan).all()}
    for definition in PLAN_CATALOG:
        plan = existing.get(definition.code)
        if plan is None:
            plan = Plan(
                code=definition.code,
                name=definition.name,
                max_users=definition.max_users,
                max_contacts=definition.max_contacts,
                max_integrations=definition.max_integrations,
                features=dict(definition.features),
                price_cents=definition.price_cents,
                currency=definition.currency,
                is_active=True,
            )
            session.add(plan)
        else:
            plan.name = definition.name
            plan.max_users = definition.max_users
            plan.max_contacts = definition.max_contacts
            plan.max_integrations = definition.max_integrations
            plan.features = dict(definition.features)
            plan.price_cents = definition.price_cents
            plan.currency = definition.currency
            plan.is_active = True
    session.flush()
