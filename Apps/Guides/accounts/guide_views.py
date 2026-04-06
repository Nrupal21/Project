"""
Views for managing guide applications and profiles in the admin interface.

This module contains views for reviewing, approving, and rejecting guide applications,
as well as displaying guide profiles for administrators and users.
"""
import json
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, UpdateView, View
from django.views.generic.edit import FormMixin

from accounts.models import GuideApplication, User
from accounts.forms import GuideApplicationForm

logger = logging.getLogger(__name__)

class GuideApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing all guide applications with filtering and pagination.
    
    This view allows administrators to view and filter guide applications
    by status (pending, approved, rejected) and provides search functionality.
    """
    model = GuideApplication
    template_name = 'accounts/admin/guide_application_list.html'
    context_object_name = 'applications'
    paginate_by = 10
    
    def test_func(self):
        """Ensure only staff users can access this view."""
        return self.request.user.is_staff
    
    def get_queryset(self):
        """
        Return filtered queryset based on status and search query.
        
        Returns:
            QuerySet: Filtered applications based on status and search query
        """
        queryset = GuideApplication.objects.select_related('user', 'reviewed_by')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status in dict(GuideApplication.Status.choices):
            queryset = queryset.filter(status=status)
        
        # Search by username, email, or ID
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                models.Q(user__username__icontains=search_query) |
                models.Q(user__email__icontains=search_query) |
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(id_type__icontains=search_query)
            )
            
        return queryset.order_by('-application_date')
    
    def get_context_data(self, **kwargs):
        """Add additional context data to the template."""
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['status_choices'] = GuideApplication.Status.choices
        
        # Add counts for each status
        context['pending_count'] = GuideApplication.objects.filter(
            status=GuideApplication.Status.PENDING
        ).count()
        context['under_review_count'] = GuideApplication.objects.filter(
            status=GuideApplication.Status.UNDER_REVIEW
        ).count()
        context['approved_count'] = GuideApplication.objects.filter(
            status=GuideApplication.Status.APPROVED
        ).count()
        context['rejected_count'] = GuideApplication.objects.filter(
            status=GuideApplication.Status.REJECTED
        ).count()
        
        return context


class GuideApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView, FormMixin):
    """
    View for displaying and reviewing a single guide application.
    
    This view shows detailed information about a guide application
    and provides forms for approving or rejecting the application.
    """
    model = GuideApplication
    template_name = 'accounts/admin/guide_application_detail.html'
    context_object_name = 'application'
    form_class = GuideApplicationForm
    
    def test_func(self):
        """Ensure only staff users can access this view."""
        return self.request.user.is_staff
    
    def get_success_url(self):
        """Return the URL to redirect to after successful form submission."""
        return reverse_lazy('accounts:review_guide_application', 
                          kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """Add additional context data to the template."""
        context = super().get_context_data(**kwargs)
        application = self.get_object()
        
        # Add form for updating application status
        context['form'] = self.get_form()
        
        # Add user's previous applications
        context['previous_applications'] = GuideApplication.objects.filter(
            user=application.user
        ).exclude(pk=application.pk).order_by('-application_date')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle form submission for updating application status."""
        if not request.user.is_staff:
            raise PermissionDenied
            
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        """Process the form data and update the application status."""
        application = self.object
        action = self.request.POST.get('action')
        
        try:
            with transaction.atomic():
                if action == 'approve':
                    # Approve the application
                    notes = form.cleaned_data.get('review_notes', '')
                    if application.approve_application(self.request.user, notes=notes):
                        messages.success(
                            self.request,
                            'Guide application has been approved successfully.'
                        )
                    else:
                        messages.error(
                            self.request,
                            'Failed to approve the guide application.'
                        )
                        
                elif action == 'reject':
                    # Reject the application
                    reason = form.cleaned_data.get('rejection_reason', '')
                    notes = form.cleaned_data.get('review_notes', '')
                    
                    if not reason:
                        form.add_error('rejection_reason', 'Please provide a reason for rejection.')
                        return self.form_invalid(form)
                        
                    if application.reject_application(self.request.user, reason, notes=notes):
                        messages.success(
                            self.request,
                            'Guide application has been rejected.'
                        )
                    else:
                        messages.error(
                            self.request,
                            'Failed to reject the guide application.'
                        )
                
                elif action == 'save':
                    # Just save the notes/verification status
                    application.review_notes = form.cleaned_data.get('review_notes', '')
                    application.id_verification_status = form.cleaned_data.get('id_verification_status', False)
                    application.background_check_status = form.cleaned_data.get('background_check_status', False)
                    
                    # If both verifications are complete, update status to UNDER_REVIEW if still PENDING
                    if (application.id_verification_status and 
                        application.background_check_status and
                        application.status == GuideApplication.Status.PENDING):
                        application.status = GuideApplication.Status.UNDER_REVIEW
                        application.save()
                        messages.success(
                            self.request,
                            'Verification completed. Application is now under review.'
                        )
                    else:
                        application.save()
                        messages.success(
                            self.request,
                            'Application details have been updated.'
                        )
                
                return redirect(self.get_success_url())
                
        except Exception as e:
            logger.error(f"Error processing guide application {application.id}: {str(e)}", 
                        exc_info=True)
            messages.error(
                self.request,
                'An error occurred while processing the application.'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(
            self.request,
            'Please correct the errors below.'
        )
        return super().form_invalid(form)


class AddApplicationNoteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View for adding notes to a guide application.
    
    This view handles POST requests to add administrative notes to a guide application.
    Notes are appended to the existing notes with a timestamp and author information.
    """
    http_method_names = ['post']
    
    def test_func(self):
        """Ensure only staff users can access this view."""
        return self.request.user.is_staff
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a note to an application.
        
        Args:
            request: The HTTP request object
            pk: The primary key of the guide application
            
        Returns:
            HttpResponseRedirect: Redirect back to the application detail page
        """
        application_id = kwargs.get('pk')
        note = request.POST.get('note', '').strip()
        
        if not note:
            messages.error(request, 'Note cannot be empty.')
            return HttpResponseRedirect(reverse_lazy('accounts:guide_application_detail', kwargs={'pk': application_id}))
        
        try:
            application = get_object_or_404(GuideApplication, pk=application_id)
            
            # Format the note with timestamp and author
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            author = request.user.get_full_name() or request.user.username
            formatted_note = f"[{timestamp} by {author}]\n{note}\n\n"
            
            # Append the new note to existing notes
            if application.notes:
                application.notes += formatted_note
            else:
                application.notes = formatted_note
            
            application.save(update_fields=['notes'])
            messages.success(request, 'Note added successfully.')
            
        except Exception as e:
            logger.error(f"Error adding note to application {application_id}: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred while adding the note.')
        
        # Redirect back to the application detail page
        return HttpResponseRedirect(reverse_lazy('accounts:review_guide_application', kwargs={'pk': application_id}))


class UpdateGuideApplicationStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    API endpoint for updating guide application status via AJAX.
    
    This view provides a RESTful interface for updating the status
    of a guide application without reloading the page.
    """
    http_method_names = ['post']
    
    def test_func(self):
        """Ensure only staff users can access this view."""
        return self.request.user.is_staff
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to update application status.
        
        Expected request format:
        {
            "application_id": <id>,
            "status": "approve" or "reject",
            "reason": "reason for rejection" (only required for reject)
        }
        """
        # Log the request content type and data for debugging
        logger.debug(f"Content-Type: {request.content_type}")
        logger.debug(f"Request body: {request.body.decode('utf-8', errors='replace')}")
        
        try:
            logger.info(f"Processing guide application status update for application ID: {kwargs.get('pk', 'Unknown')}")            
            
            # Check if request body is empty
            if not request.body:
                logger.warning(f"Empty request body received from {request.META.get('REMOTE_ADDR')}") 
                return JsonResponse(
                    {'success': False, 'error': 'Empty request body. JSON data required.'},
                    status=400
                )
                
            # Parse JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {str(e)}. Request body: {request.body[:100]}...")
                return JsonResponse(
                    {'success': False, 'error': f'Invalid JSON data: {str(e)}'},
                    status=400
                )
            
            # Get application ID from URL if not in request body
            application_id = data.get('application_id', kwargs.get('pk'))
            status = data.get('status')
            reason = data.get('reason', '')
            
            # Validate required parameters
            if not application_id:
                return JsonResponse(
                    {'success': False, 'error': 'Missing application_id parameter'},
                    status=400
                )
                
            if not status:
                return JsonResponse(
                    {'success': False, 'error': 'Missing status parameter'},
                    status=400
                )
            
            # Get the application object
            try:
                application = get_object_or_404(GuideApplication, pk=application_id)
            except Exception as e:
                return JsonResponse(
                    {'success': False, 'error': f'Application not found: {str(e)}'},
                    status=404
                )
            
            # Process the update within a transaction
            with transaction.atomic():
                # Handle verification status updates from the checkbox UI
                if 'action' in data and data['action'] == 'update_verification_status':
                    field = data.get('field')
                    status_value = data.get('status')
                    
                    if not field:
                        return JsonResponse({'success': False, 'error': 'Missing field parameter'}, status=400)
                        
                    # Update the appropriate field
                    if field == 'id_verification':
                        application.id_verification_status = status_value
                        application.save(update_fields=['id_verification_status'])
                        return JsonResponse({
                            'success': True,
                            'message': 'ID verification status updated',
                            'field': field,
                            'status': status_value
                        })
                    elif field == 'background_check':
                        application.background_check_status = status_value
                        application.save(update_fields=['background_check_status'])
                        return JsonResponse({
                            'success': True,
                            'message': 'Background check status updated',
                            'field': field,
                            'status': status_value
                        })
                    else:
                        return JsonResponse({'success': False, 'error': f'Invalid field: {field}'}, status=400)
                
                # Handle standard approve/reject status updates
                if status == 'approve':
                    if application.approve_application(request.user):
                        return JsonResponse({
                            'success': True,
                            'message': 'Application approved successfully',
                            'new_status': application.get_status_display(),
                            'status_class': application.get_status_badge_class()
                        })
                    else:
                        return JsonResponse(
                            {'success': False, 'error': 'Failed to approve application'},
                            status=400
                        )
                        
                elif status == 'reject':
                    if not reason:
                        return JsonResponse(
                            {'success': False, 'error': 'Rejection reason is required'},
                            status=400
                        )
                        
                    if application.reject_application(request.user, reason):
                        return JsonResponse({
                            'success': True,
                            'message': 'Application rejected',
                            'new_status': application.get_status_display(),
                            'status_class': application.get_status_badge_class()
                        })
                    else:
                        return JsonResponse(
                            {'success': False, 'error': 'Failed to reject application'},
                            status=400
                        )
                
                else:
                    return JsonResponse(
                        {'success': False, 'error': 'Invalid status'},
                        status=400
                    )
                    
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'error': 'Invalid JSON data'},
                status=400
            )
        except Exception as e:
            logger.error(f"Error updating guide application status: {str(e)}", exc_info=True)
            return JsonResponse(
                {'success': False, 'error': 'An error occurred'},
                status=500
            )


from django.shortcuts import render
from accounts.models import UserProfile
from django.contrib.auth.decorators import login_required
from reviews.models import Review
from django.db.models import Avg


def guide_profile_view(request, user_id):
    """
    View function to display a guide's profile by user ID.
    
    This view shows detailed information about a guide including their profile,
    experience, languages, ratings, and reviews.
    
    Args:
        request: The HTTP request
        user_id: The ID of the user whose guide profile to display
        
    Returns:
        HttpResponse: Rendered guide profile template
    """
    # Get the user and their profile
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if the user is actually a guide
    if not profile.is_guide:
        messages.error(request, "This user is not a guide.")
        return redirect('accounts:user_profile', user_id=user_id)
    
    # Get guide application for additional information
    try:
        guide_application = GuideApplication.objects.filter(user=user, status='APPROVED').first()
    except GuideApplication.DoesNotExist:
        guide_application = None
    
    # Get guide's reviews and ratings
    reviews = Review.objects.filter(content_type__model='userprofile', object_id=profile.id)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'guide': user,
        'profile': profile,
        'guide_application': guide_application,
        'reviews': reviews[:5],  # Show only the 5 most recent reviews
        'review_count': reviews.count(),
        'avg_rating': avg_rating,
    }
    
    return render(request, 'accounts/guide_profile.html', context)
