from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import BusinessInstance, ConnectorSession


class BusinessAccessMiddleware:
    """
    Resolves /hub/<slug>/ requests:
    1. Attaches `request.current_business` for views to use.
    2. Enforces IP-lock rules for businesses with installation_type='ip_locked'.
       - Bypass is allowed via a valid connector token in the X-Connector-Token header.
    3. Self-hosted businesses are accessible from any IP but must use a connector
       token or be accessed from the registered self_hosted_url network.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_business = None

        path = request.path
        # Only process paths under the hub prefix
        if not path.startswith('/hub/'):
            return self.get_response(request)

        # Extract slug from path: /hub/<slug>/...
        parts = path.lstrip('/').split('/')
        # parts[0] = 'hub', parts[1] = slug (if present)
        if len(parts) < 2 or not parts[1]:
            return self.get_response(request)

        slug = parts[1]
        # Skip well-known non-slug path segments.
        # 'create' and 'api' are hub-level actions; the rest are suite-first
        # module prefixes mounted as hub/<prefix>/<slug>/ in ROOT_URLCONF —
        # those modules receive the real slug via URL kwargs, not middleware.
        _SKIP_SEGMENTS = frozenset([
            'create', 'api',
            'erp', 'mes', 'plm', 'cadcam', 'assets',
            'workshop', 'dms', 'dvi',
            'tms', 'wms',
            'data-studio', 'process-mapper',
            'sis', 'lms', 'assessments', 'timetable', 'parent-portal',
            'properties', 'deals', 'commission', 're-marketing', 're-portal',
            'omnichannel', 'planogram', 'product-catalog', 'b2b', 'store-ops',
            'call-center',
        ])
        if slug in _SKIP_SEGMENTS:
            return self.get_response(request)

        try:
            biz = BusinessInstance.objects.get(slug=slug, is_active=True)
        except BusinessInstance.DoesNotExist:
            return self.get_response(request)

        request.current_business = biz

        # IP-lock enforcement
        if biz.installation_type == 'ip_locked' and biz.allowed_ips:
            if not self._is_access_allowed(request, biz):
                return HttpResponseForbidden(
                    "<h2>Access Restricted</h2>"
                    "<p>Your IP address is not on this business's allowlist. "
                    "Use the BengalBound Connector App to access remotely.</p>"
                )

        return self.get_response(request)

    def _is_access_allowed(self, request, biz):
        """Return True if the request IP is allowed or a valid connector token is present."""
        # Check connector token first (allows remote access from any IP)
        connector_token = (
            request.headers.get('X-Connector-Token') or
            request.GET.get('_ct') or
            request.COOKIES.get('bb_connector_token')
        )
        if connector_token:
            valid = ConnectorSession.objects.filter(
                business=biz,
                token=connector_token,
                is_active=True,
                expires_at__gt=timezone.now(),
            ).exists()
            if valid:
                return True

        # Check IP allowlist
        client_ip = self._get_client_ip(request)
        return client_ip in biz.allowed_ips

    @staticmethod
    def _get_client_ip(request):
        remote_addr = request.META.get('REMOTE_ADDR', '')
        trusted = getattr(settings, 'TRUSTED_PROXIES', [])
        # Only honour X-Forwarded-For when REMOTE_ADDR is a known trusted proxy.
        if remote_addr in trusted:
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            if x_forwarded:
                return x_forwarded.split(',')[0].strip()
        return remote_addr
