from django.utils.deprecation import MiddlewareMixin

class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    """
    Disable CSRF validation for API endpoints (URLs starting with /api/)
    """
    def process_request(self, request):
        # List of API prefixes that should be CSRF exempt
        api_prefixes = ['/api/users/', '/api/masters/', '/api/system/', '/api/general/', '/users/', '/masters/', '/system/', '/general/']
        
        # Check if the request path starts with any API prefix
        if any(request.path.startswith(prefix) for prefix in api_prefixes):
            setattr(request, '_dont_enforce_csrf_checks', True)
