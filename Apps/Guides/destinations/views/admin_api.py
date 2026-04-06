"""
AJAX API endpoints for destination management.

This module provides JSON API endpoints for destination approval and rejection operations,
designed to work with AJAX requests from the manager dashboard. These endpoints return
proper JSON responses instead of redirects, making them suitable for use with fetch/AJAX calls.

All endpoints require authentication and appropriate manager/admin permissions.
"""

import json
import logging
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

# Import models and utility functions
from destinations.models import Destination
from destinations.views.admin import send_destination_approval_notification, send_destination_rejection_notification

# Set up logger
logger = logging.getLogger('destinations.api')


def staff_required(view_func):
    """
    Decorator to check if user is authenticated and has manager or admin role.
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        function: Wrapped function with authentication check
    """
    def wrapped_view(request, *args, **kwargs):
        # Check authentication and permissions
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated user attempted to access {view_func.__name__}")
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        
        if not (request.user.is_manager or request.user.is_admin):
            logger.warning(f"Unauthorized user {request.user.username} attempted to access {view_func.__name__}")
            return JsonResponse({'success': False, 'message': 'You do not have permission to perform this action'}, status=403)
        
        # Call the view function if authentication passes
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


@require_http_methods(["POST"])
@staff_required
def api_approve_destination(request, pk):
    """
    API endpoint to approve a destination via AJAX.
    
    This view handles the destination approval process and returns a JSON response
    suitable for AJAX requests. It performs the same functionality as the standard
    approve_destination view but with proper JSON responses.
    
    Args:
        request: The HTTP request
        pk: Primary key of the destination to approve
        
    Returns:
        JsonResponse: JSON response with success status and message
    """
    logger.info(f"Processing destination approval request for destination ID {pk} by {request.user.username}")
    
    try:
        # Get destination object
        destination = get_object_or_404(Destination, pk=pk)
        
        # Process approval with transaction to ensure atomicity
        with transaction.atomic():
            if destination.approve(request.user):
                # Send notification to destination creator
                notification_sent = send_destination_approval_notification(destination)
                
                # Prepare success message
                message = f'Destination "{destination.name}" has been approved and is now visible on the site.'
                if notification_sent and destination.created_by:
                    message += f' Notification sent to {destination.created_by.username}.'
                
                # Log success
                logger.info(f"Destination '{destination.name}' (ID: {pk}) approved by {request.user.username}")
                
                # Return success response
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'destination_id': pk,
                    'destination_name': destination.name,
                    'notification_sent': notification_sent
                })
            else:
                # Log failure
                logger.warning(f"Failed to approve destination '{destination.name}' (ID: {pk}). It may already be approved.")
                
                # Return error response
                return JsonResponse({
                    'success': False,
                    'message': f'Could not approve destination "{destination.name}". It may already be approved.'
                }, status=400)
    
    except Exception as e:
        # Log error
        logger.error(f"Error approving destination {pk}: {str(e)}", exc_info=True)
        
        # Return error response
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request'
        }, status=500)


@require_http_methods(["POST"])
@staff_required
def api_reject_destination(request, pk):
    """
    API endpoint to reject a destination via AJAX.
    
    This view handles the destination rejection process and returns a JSON response
    suitable for AJAX requests. It performs the same functionality as the standard
    reject_destination view but with proper JSON responses.
    
    Args:
        request: The HTTP request containing JSON with rejection reason
        pk: Primary key of the destination to reject
        
    Returns:
        JsonResponse: JSON response with success status and message
    """
    logger.info(f"Processing destination rejection request for destination ID {pk} by {request.user.username}")
    
    try:
        # Get destination object
        destination = get_object_or_404(Destination, pk=pk)
        
        # Parse JSON request body
        try:
            data = json.loads(request.body)
            rejection_reason = data.get('rejection_reason')
            
            # Log the received data for debugging
            logger.debug(f"Received rejection request: {data}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in rejection request for destination {pk}")
            return JsonResponse({
                'success': False, 
                'message': 'Invalid JSON data in request'
            }, status=400)
        
        # Validate rejection reason
        if not rejection_reason:
            logger.warning(f"Rejection attempt for destination {pk} without providing a reason")
            return JsonResponse({
                'success': False,
                'message': 'Please provide a reason for rejecting the destination.'
            }, status=400)
        
        # Process rejection with transaction to ensure atomicity
        with transaction.atomic():
            if destination.reject(request.user, rejection_reason):
                # Send notification to destination creator
                notification_sent = send_destination_rejection_notification(destination)
                
                # Prepare success message
                message = f'Destination "{destination.name}" has been rejected.'
                if notification_sent and destination.created_by:
                    message += f' Notification sent to {destination.created_by.username}.'
                
                # Log success
                logger.info(f"Destination '{destination.name}' (ID: {pk}) rejected by {request.user.username} with reason: {rejection_reason}")
                
                # Return success response
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'destination_id': pk,
                    'destination_name': destination.name,
                    'notification_sent': notification_sent
                })
            else:
                # Log failure
                logger.warning(f"Failed to reject destination '{destination.name}' (ID: {pk}). It may have already been processed.")
                
                # Return error response
                return JsonResponse({
                    'success': False,
                    'message': f'Could not reject destination "{destination.name}". It may have already been processed.'
                }, status=400)
                
    except Exception as e:
        # Log error
        logger.error(f"Error rejecting destination {pk}: {str(e)}", exc_info=True)
        
        # Return error response
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request'
        }, status=500)
