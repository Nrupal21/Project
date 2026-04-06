"""
API Logging Middleware

This middleware logs all API requests and responses for monitoring and debugging purposes.
It captures request method, path, query parameters, and response status code.
"""
import json
import time
from django.utils.deprecation import MiddlewareMixin
import logging

# Get an instance of a logger
logger = logging.getLogger('api')

class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses.
    
    This middleware captures:
    - Request method and path
    - Query parameters
    - Request body (for non-file uploads)
    - Response status code
    - Processing time
    """
    
    def process_request(self, request):
        """
        Process the request and log the details.
        """
        # Skip logging for static and media files
        if self._should_skip_logging(request):
            return None
            
        # Store the start time for calculating request duration
        request.start_time = time.time()
        
        # Log the request details
        log_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
        }
        
        # Include request body for non-file uploads
        if request.body and not self._is_multipart(request):
            try:
                body = json.loads(request.body.decode('utf-8'))
                log_data['request_body'] = body
            except (UnicodeDecodeError, json.JSONDecodeError):
                log_data['request_body'] = 'Binary or non-JSON data'
        
        logger.info(f"API Request: {json.dumps(log_data, indent=2)}")
        return None
    
    def process_response(self, request, response):
        """
        Process the response and log the details.
        """
        # Skip logging for static and media files
        if self._should_skip_logging(request):
            return response
            
        # Calculate request duration
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # Log the response details
        log_data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_seconds': round(duration, 4),
        }
        
        # Include response content for error status codes
        if 400 <= response.status_code < 600:
            try:
                content = response.content.decode('utf-8')
                log_data['response_content'] = content
            except UnicodeDecodeError:
                log_data['response_content'] = 'Binary or non-text response'
        
        logger.info(f"API Response: {json.dumps(log_data, indent=2)}")
        return response
    
    def _should_skip_logging(self, request):
        """
        Determine if logging should be skipped for the given request.
        """
        # Skip logging for static and media files
        skip_paths = ['/static/', '/media/', '/favicon.ico']
        return any(path in request.path for path in skip_paths)
    
    def _is_multipart(self, request):
        """
        Check if the request is a multipart form data request.
        """
        content_type = request.content_type or ''
        return 'multipart/form-data' in content_type.lower()
