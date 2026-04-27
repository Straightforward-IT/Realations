"""Licensing & subscription enforcement.

Public surface area:

* :data:`PLAN_CATALOG` — canonical, code-defined seed plans.
* :class:`LicenseChecker` — a request-scoped helper used by FastAPI
  dependencies to gate features, resource counts, and API calls.
"""

from app.licensing.catalog import PLAN_CATALOG, PlanDefinition, seed_plans  # noqa: F401
from app.licensing.checker import LicenseChecker, get_license_checker  # noqa: F401
