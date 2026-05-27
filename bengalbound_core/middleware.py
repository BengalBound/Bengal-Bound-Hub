class SubdomainRoutingMiddleware:
    """
    Middleware that inspects the Host header and dynamically changes the URL configuration
    based on the subdomain.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()

        if host == 'workspace.localhost':
            request.urlconf = 'bengalbound_core.workspace_urls'
        elif host == 'console.localhost':
            request.urlconf = 'bengalbound_core.console_urls'
        elif host == 'community.localhost':
            request.urlconf = 'bengalbound_core.community_urls'
        # If none map, Django will default to ROOT_URLCONF (bengalbound_core.urls),
        # which properly includes the admin, allauth endpoints, and public site at '/'.

        response = self.get_response(request)
        return response
