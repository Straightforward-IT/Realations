"""Concrete provider implementations.

Each provider is a thin scaffold demonstrating how the third party should be
wired into the integration framework. Real OAuth flows / SDK calls belong here
but the surface area (slug, feature key, hooks) is what the rest of the
platform depends on.
"""

from app.integrations.providers.asana import AsanaProvider  # noqa: F401
from app.integrations.providers.microsoft_graph import MicrosoftGraphProvider  # noqa: F401
from app.integrations.providers.pipedrive import PipedriveProvider  # noqa: F401
from app.integrations.providers.zapier import ZapierProvider  # noqa: F401
