"""Health check endpoint"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import datetime

def health_check(request):
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'checks': {}
    }
    
    try:
        connection.ensure_connection()
        health_status['checks']['database'] = 'connected'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    try:
        cache.set('health_check', 'ok', 10)
        health_status['checks']['cache'] = 'working' if cache.get('health_check') == 'ok' else 'error'
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'
    
    return JsonResponse(health_status, status=200 if health_status['status'] == 'healthy' else 500)
