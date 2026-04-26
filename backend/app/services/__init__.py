"""Service-layer helpers shared by the API routes.

These intentionally stay thin — they encapsulate tenant scoping and event
publishing so individual route handlers don't repeat boilerplate.
"""

from app.services.crud import (  # noqa: F401
    create_with_tenant,
    delete_for_tenant,
    get_for_tenant,
    list_for_tenant,
    update_for_tenant,
)
from app.services.events import publish_event  # noqa: F401
