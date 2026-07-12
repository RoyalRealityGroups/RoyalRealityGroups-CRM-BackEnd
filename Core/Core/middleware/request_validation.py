import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class RequestValidationMiddleware(MiddlewareMixin):
    """Middleware to validate incoming API requests"""
    
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    
    def process_request(self, request):
        # Skip validation for non-API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Validate request size
        if request.META.get('CONTENT_LENGTH'):
            content_length = int(request.META['CONTENT_LENGTH'])
            if content_length > self.MAX_REQUEST_SIZE:
                return JsonResponse({
                    'error': f'Request too large, Maximum request size is {self.MAX_REQUEST_SIZE / (1024*1024)}MB',
                    'detail': f'Maximum request size is {self.MAX_REQUEST_SIZE / (1024*1024)}MB'
                }, status=413)
        
        # Validate JSON for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            
            if 'application/json' in content_type:
                try:
                    if request.body:
                        json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'error': 'Invalid JSON',
                        'detail': 'Request body must be valid JSON'
                    }, status=400)
        
        return None
