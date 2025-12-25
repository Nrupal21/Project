"""
Health Check View for Food Ordering System
Provides endpoint for monitoring application health and readiness
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint for monitoring and load balancers
    
    Checks:
    - Database connectivity
    - Application responsiveness
    
    Returns:
        JsonResponse: Health status with HTTP 200 (healthy) or 503 (unhealthy)
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
        logger.error(f"Health check database error: {str(e)}")
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check endpoint for Kubernetes/container orchestration
    
    Indicates if the application is ready to accept traffic
    
    Returns:
        JsonResponse: Readiness status
    """
    return JsonResponse({
        'status': 'ready',
        'message': 'Application is ready to accept requests'
    })


def liveness_check(request):
    """
    Liveness check endpoint for Kubernetes/container orchestration
    
    Indicates if the application is alive and running
    
    Returns:
        JsonResponse: Liveness status
    """
    return JsonResponse({
        'status': 'alive',
        'message': 'Application is running'
    })
