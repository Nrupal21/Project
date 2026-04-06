"""
API utility functions and classes for consistent API behavior across the TravelGuide application.

This module provides shared utilities for Django REST Framework APIs, including
standardized response formats, error handling, pagination, filtering, and
authentication helpers. It ensures consistent API behavior across all apps.

Key Features:
- Standardized JSON response formats
- Comprehensive error handling with proper HTTP status codes
- Custom pagination classes for consistent API responses
- Authentication and permission utilities
- Request validation and sanitization helpers
- API versioning support utilities
"""

import logging
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.request import Request

# Configure logger for this module
logger = logging.getLogger(__name__)


class StandardAPIResponse:
    """
    Utility class for creating standardized API responses.
    
    This class provides methods for creating consistent JSON responses
    across all API endpoints, ensuring uniform structure and error handling.
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200, **kwargs) -> Response:
        """
        Create a standardized success response.
        
        This method generates a consistent success response format that includes
        status information, data payload, and optional metadata.
        
        Args:
            data (Any, optional): Response data payload
            message (str): Success message (default: "Success")
            status_code (int): HTTP status code (default: 200)
            **kwargs: Additional response metadata
            
        Returns:
            Response: DRF Response object with standardized format
            
        Example:
            >>> return StandardAPIResponse.success(
            ...     data=destinations,
            ...     message="Destinations retrieved successfully",
            ...     total_count=len(destinations)
            ... )
        """
        response_data = {
            'success': True,
            'status_code': status_code,
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'data': data
        }
        
        # Add any additional metadata
        response_data.update(kwargs)
        
        logger.debug(f"API Success Response: {message} (Status: {status_code})")
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message: str, status_code: int = 400, errors: Dict = None, **kwargs) -> Response:
        """
        Create a standardized error response.
        
        This method generates a consistent error response format that includes
        error details, validation errors, and debugging information.
        
        Args:
            message (str): Error message
            status_code (int): HTTP status code (default: 400)
            errors (Dict, optional): Detailed error information
            **kwargs: Additional error metadata
            
        Returns:
            Response: DRF Response object with standardized error format
            
        Example:
            >>> return StandardAPIResponse.error(
            ...     message="Invalid coordinates provided",
            ...     status_code=400,
            ...     errors={'latitude': ['This field is required']}
            ... )
        """
        response_data = {
            'success': False,
            'status_code': status_code,
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'errors': errors or {}
        }
        
        # Add any additional metadata
        response_data.update(kwargs)
        
        logger.warning(f"API Error Response: {message} (Status: {status_code})")
        return Response(response_data, status=status_code)
    
    @staticmethod
    def paginated(queryset: QuerySet, page: int, per_page: int = 10, serializer_class=None, **kwargs) -> Response:
        """
        Create a standardized paginated response.
        
        This method handles pagination logic and creates a consistent response
        format for paginated data with metadata about pagination state.
        
        Args:
            queryset (QuerySet): Django QuerySet to paginate
            page (int): Current page number
            per_page (int): Items per page (default: 10)
            serializer_class: DRF Serializer class for data serialization
            **kwargs: Additional response metadata
            
        Returns:
            Response: DRF Response object with paginated data
            
        Example:
            >>> return StandardAPIResponse.paginated(
            ...     queryset=destinations,
            ...     page=request.GET.get('page', 1),
            ...     serializer_class=DestinationSerializer
            ... )
        """
        try:
            # Validate page parameter
            try:
                page = int(page)
                if page < 1:
                    page = 1
            except (ValueError, TypeError):
                page = 1
            
            # Create paginator
            paginator = Paginator(queryset, per_page)
            
            try:
                paginated_data = paginator.page(page)
            except PageNotAnInteger:
                paginated_data = paginator.page(1)
                page = 1
            except EmptyPage:
                paginated_data = paginator.page(paginator.num_pages)
                page = paginator.num_pages
            
            # Serialize data if serializer provided
            if serializer_class:
                serializer = serializer_class(paginated_data.object_list, many=True)
                data = serializer.data
            else:
                data = list(paginated_data.object_list.values())
            
            # Build response with pagination metadata
            response_data = {
                'success': True,
                'status_code': 200,
                'message': f"Page {page} of {paginator.num_pages} retrieved successfully",
                'timestamp': timezone.now().isoformat(),
                'data': data,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'items_per_page': per_page,
                    'has_next': paginated_data.has_next(),
                    'has_previous': paginated_data.has_previous(),
                    'next_page': paginated_data.next_page_number() if paginated_data.has_next() else None,
                    'previous_page': paginated_data.previous_page_number() if paginated_data.has_previous() else None
                }
            }
            
            # Add any additional metadata
            response_data.update(kwargs)
            
            return Response(response_data, status=200)
            
        except Exception as e:
            logger.error(f"Error in paginated response: {e}")
            return StandardAPIResponse.error(
                message="Error processing paginated request",
                status_code=500,
                errors={'pagination': [str(e)]}
            )


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class with enhanced metadata and configuration.
    
    This pagination class extends DRF's PageNumberPagination to provide
    more detailed pagination information and consistent response formatting.
    """
    
    page_size = 10
    page_size_query_param = 'per_page'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """
        Return a paginated style Response object with enhanced metadata.
        
        This method overrides the default pagination response to include
        additional metadata and maintain consistency with StandardAPIResponse.
        
        Args:
            data: Serialized data for the current page
            
        Returns:
            Response: Enhanced paginated response with detailed metadata
        """
        return Response({
            'success': True,
            'status_code': 200,
            'message': f"Page {self.page.number} of {self.page.paginator.num_pages} retrieved successfully",
            'timestamp': timezone.now().isoformat(),
            'data': data,
            'pagination': {
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'total_items': self.page.paginator.count,
                'items_per_page': self.page_size,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'next_page': self.page.next_page_number() if self.page.has_next() else None,
                'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link()
                }
            }
        })


class APIValidationUtils:
    """
    Utility class for API request validation and sanitization.
    
    This class provides methods for validating common API parameters,
    sanitizing input data, and ensuring data consistency across endpoints.
    """
    
    @staticmethod
    def validate_coordinates(latitude: Any, longitude: Any) -> tuple[bool, Optional[str]]:
        """
        Validate latitude and longitude coordinates from API request.
        
        This method validates coordinate parameters commonly used in
        location-based API endpoints and returns validation results.
        
        Args:
            latitude (Any): Latitude value to validate
            longitude (Any): Longitude value to validate
            
        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
            
        Example:
            >>> is_valid, error = APIValidationUtils.validate_coordinates(40.7128, -74.0060)
            >>> if not is_valid:
            ...     return StandardAPIResponse.error(error, status_code=400)
        """
        try:
            # Convert to float
            lat = float(latitude)
            lng = float(longitude)
            
            # Validate ranges
            if not (-90 <= lat <= 90):
                return False, "Latitude must be between -90 and 90 degrees"
            
            if not (-180 <= lng <= 180):
                return False, "Longitude must be between -180 and 180 degrees"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, "Invalid coordinate format. Must be numeric values."
    
    @staticmethod
    def validate_pagination_params(page: Any, per_page: Any) -> tuple[int, int, Optional[str]]:
        """
        Validate and sanitize pagination parameters.
        
        This method ensures pagination parameters are within acceptable ranges
        and provides sensible defaults for invalid values.
        
        Args:
            page (Any): Page number parameter
            per_page (Any): Items per page parameter
            
        Returns:
            tuple[int, int, Optional[str]]: (page, per_page, error_message)
        """
        error_messages = []
        
        # Validate page parameter
        try:
            page = int(page) if page else 1
            if page < 1:
                page = 1
                error_messages.append("Page number must be positive, defaulting to 1")
        except (ValueError, TypeError):
            page = 1
            error_messages.append("Invalid page number, defaulting to 1")
        
        # Validate per_page parameter
        try:
            per_page = int(per_page) if per_page else 10
            if per_page < 1:
                per_page = 10
                error_messages.append("Items per page must be positive, defaulting to 10")
            elif per_page > 100:
                per_page = 100
                error_messages.append("Items per page limited to maximum of 100")
        except (ValueError, TypeError):
            per_page = 10
            error_messages.append("Invalid items per page, defaulting to 10")
        
        error_message = "; ".join(error_messages) if error_messages else None
        return page, per_page, error_message
    
    @staticmethod
    def validate_price_range(min_price: Any, max_price: Any) -> tuple[Optional[Decimal], Optional[Decimal], Optional[str]]:
        """
        Validate price range parameters for filtering.
        
        This method validates price range parameters commonly used in
        search and filtering endpoints.
        
        Args:
            min_price (Any): Minimum price parameter
            max_price (Any): Maximum price parameter
            
        Returns:
            tuple[Optional[Decimal], Optional[Decimal], Optional[str]]: (min_price, max_price, error_message)
        """
        error_messages = []
        validated_min = None
        validated_max = None
        
        # Validate minimum price
        if min_price is not None:
            try:
                validated_min = Decimal(str(min_price))
                if validated_min < 0:
                    error_messages.append("Minimum price cannot be negative")
                    validated_min = None
            except (ValueError, TypeError):
                error_messages.append("Invalid minimum price format")
        
        # Validate maximum price
        if max_price is not None:
            try:
                validated_max = Decimal(str(max_price))
                if validated_max < 0:
                    error_messages.append("Maximum price cannot be negative")
                    validated_max = None
            except (ValueError, TypeError):
                error_messages.append("Invalid maximum price format")
        
        # Validate price range logic
        if validated_min and validated_max and validated_min > validated_max:
            error_messages.append("Minimum price cannot be greater than maximum price")
            validated_min = validated_max = None
        
        error_message = "; ".join(error_messages) if error_messages else None
        return validated_min, validated_max, error_message


class APIPermissionUtils:
    """
    Utility class for API permission and authentication helpers.
    
    This class provides custom permission classes and authentication
    utilities for securing API endpoints appropriately.
    """
    
    class IsOwnerOrReadOnly(BasePermission):
        """
        Custom permission to only allow owners of an object to edit it.
        
        This permission class allows read access to any user but restricts
        write access to the owner of the object only.
        """
        
        def has_object_permission(self, request, view, obj):
            """
            Check if the user has permission to access the specific object.
            
            Args:
                request: HTTP request object
                view: API view handling the request
                obj: Object being accessed
                
            Returns:
                bool: True if permission granted, False otherwise
            """
            # Read permissions are allowed for any request
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                return True
            
            # Write permissions are only allowed to the owner of the object
            return hasattr(obj, 'created_by') and obj.created_by == request.user
    
    class IsManagerOrReadOnly(BasePermission):
        """
        Custom permission to only allow managers to edit content.
        
        This permission class allows read access to any user but restricts
        write access to users with manager or admin privileges.
        """
        
        def has_permission(self, request, view):
            """
            Check if the user has permission to access the view.
            
            Args:
                request: HTTP request object
                view: API view handling the request
                
            Returns:
                bool: True if permission granted, False otherwise
            """
            # Read permissions are allowed for any request
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                return True
            
            # Write permissions require authentication and manager role
            return (
                request.user and 
                request.user.is_authenticated and 
                (request.user.is_staff or 
                 hasattr(request.user, 'role') and 
                 request.user.role in ['manager', 'admin'])
            )


def api_exception_handler(exc, context):
    """
    Custom exception handler for consistent API error responses.
    
    This function handles exceptions raised in API views and converts them
    to standardized error responses using the StandardAPIResponse format.
    
    Args:
        exc: Exception instance
        context: Context information about the request
        
    Returns:
        Response: Standardized error response
    """
    logger.error(f"API Exception: {exc} in context: {context}")
    
    if isinstance(exc, ValidationError):
        return StandardAPIResponse.error(
            message="Validation error",
            status_code=400,
            errors=exc.detail if hasattr(exc, 'detail') else {'validation': [str(exc)]}
        )
    
    elif isinstance(exc, PermissionDenied):
        return StandardAPIResponse.error(
            message="Permission denied",
            status_code=403,
            errors={'permission': [str(exc)]}
        )
    
    elif isinstance(exc, NotFound):
        return StandardAPIResponse.error(
            message="Resource not found",
            status_code=404,
            errors={'not_found': [str(exc)]}
        )
    
    else:
        # Generic error handling
        return StandardAPIResponse.error(
            message="An error occurred processing your request",
            status_code=500,
            errors={'server': [str(exc)]}
        )


def require_api_key(view_func):
    """
    Decorator to require API key authentication for specific endpoints.
    
    This decorator can be applied to API views that require additional
    authentication beyond the standard user authentication.
    
    Args:
        view_func: View function to decorate
        
    Returns:
        function: Decorated view function with API key requirement
    """
    def wrapper(request, *args, **kwargs):
        api_key = request.META.get('HTTP_X_API_KEY') or request.GET.get('api_key')
        
        if not api_key:
            return StandardAPIResponse.error(
                message="API key required",
                status_code=401,
                errors={'authentication': ['API key must be provided']}
            )
        
        # Here you would validate the API key against your database
        # For now, we'll just check if it's not empty
        if not api_key.strip():
            return StandardAPIResponse.error(
                message="Invalid API key",
                status_code=401,
                errors={'authentication': ['Invalid API key provided']}
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# Convenience decorators for common API patterns
def standard_api_view(methods=['GET'], permission_classes_list=None, authentication_classes_list=None):
    """
    Decorator that combines common API view decorators with standardized settings.
    
    This decorator applies common API view settings including method restrictions,
    permissions, and authentication in a consistent manner.
    
    Args:
        methods (list): Allowed HTTP methods (default: ['GET'])
        permission_classes_list (list, optional): Permission classes to apply
        authentication_classes_list (list, optional): Authentication classes to apply
        
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        # Apply DRF decorators
        decorated_view = api_view(methods)(view_func)
        
        if permission_classes_list:
            decorated_view = permission_classes(permission_classes_list)(decorated_view)
        
        if authentication_classes_list:
            decorated_view = authentication_classes(authentication_classes_list)(decorated_view)
        
        return decorated_view
    
    return decorator
