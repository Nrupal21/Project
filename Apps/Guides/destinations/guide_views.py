"""
Guide-specific views for managing destinations and attractions.

This module contains views that are specifically designed for guides to manage
their destinations and attractions. These views include permission checks to
ensure only authenticated guides can access them.

Destination Submission Workflow:
1. Local guides submit destinations through PendingDestinationCreateView
2. Submissions are stored in PendingDestination table awaiting review
3. Admins/managers review and either approve or reject the submission
4. Approved destinations get transferred to the Destination table
5. Local guides earn reward points for approved destinations
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, UpdateView, DeleteView, ListView, DetailView, TemplateView
)
from django.views.generic.edit import FormMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone

# Import email utilities for notifications
from .utils.email_notifications import (
    send_destination_submission_notification,
    send_guide_submission_confirmation
)

from .models import (
    Destination, Attraction, DestinationImage, Region,
    PendingDestination, PendingDestinationImage
)
from .forms import (
    DestinationForm, AttractionForm, DestinationImageForm,
    PendingDestinationForm, PendingDestinationImageForm
)


class GuideRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure only guides can access the view."""
    permission_denied_message = "You must be a guide to access this page."
    
    def test_func(self):
        """Check if the user is a guide."""
        return hasattr(self.request.user, 'is_guide') and self.request.user.is_guide
    
    def handle_no_permission(self):
        """Redirect to the guide application page if user is not a guide."""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, self.permission_denied_message)
        return redirect('accounts:guide_application')


class GuideDashboardView(GuideRequiredMixin, TemplateView):
    """
    Dashboard view for guides to manage their content.
    
    This view presents guides with an overview of both their approved destinations
    and pending destination submissions. It shows the status of all content
    they've submitted and allows them to track the approval process.
    """
    template_name = 'destinations/guide_dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Add guide's destinations and pending submissions to the context.
        
        This method gathers all relevant destination data for the guide including:
        - Approved destinations in the main Destination table
        - Pending destination submissions awaiting review
        - Rejected destination submissions with feedback
        - Associated attractions for approved destinations
        
        Returns:
            dict: Context containing all guide's content with status information
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get approved destinations
        context['destinations'] = Destination.objects.filter(created_by=user)
        
        # Get pending destination submissions
        context['pending_destinations'] = PendingDestination.objects.filter(
            created_by=user,
            approval_status=PendingDestination.ApprovalStatus.PENDING
        )
        
        # Get rejected destination submissions
        context['rejected_destinations'] = PendingDestination.objects.filter(
            created_by=user,
            approval_status=PendingDestination.ApprovalStatus.REJECTED
        )
        
        # Get approved destination submissions
        context['approved_submissions'] = PendingDestination.objects.filter(
            created_by=user,
            approval_status=PendingDestination.ApprovalStatus.APPROVED
        )
        
        # Get attractions related to guide's destinations
        context['attractions'] = Attraction.objects.filter(destination__created_by=user)
        
        # Add submission statistics
        context['stats'] = {
            'total_submissions': PendingDestination.objects.filter(created_by=user).count(),
            'pending_count': context['pending_destinations'].count(),
            'approved_count': context['approved_submissions'].count(),
            'rejected_count': context['rejected_destinations'].count(),
            'total_destinations': context['destinations'].count(),
        }
        
        return context


class PendingDestinationCreateView(GuideRequiredMixin, CreateView):
    """
    View for local guides to submit new destination proposals for approval.
    
    This view creates entries in the PendingDestination table rather than directly
    creating destinations in the Destination table. All submissions go through
    an approval workflow where managers/admins review them before acceptance.
    
    Upon successful submission, the destination enters a pending state and awaits
    review from a manager or administrator. The user is redirected to a success page
    and email notifications are sent to both the guide and managers/admins.
    """
    model = PendingDestination
    form_class = PendingDestinationForm
    template_name = 'destinations/destination_form.html'
    
    def form_valid(self, form):
        """
        Save the form and set additional metadata before submission.
        
        This method adds the current user as the creator of the pending destination,
        sets the submission date, and initializes the approval status as pending.
        It also sends email notifications to both the guide and managers/admins.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponseRedirect: Redirect to success page with destination details
        """
        # Set the current user as the creator
        form.instance.created_by = self.request.user
        # Set submission date
        form.instance.submission_date = timezone.now()
        # Set approval status to pending
        form.instance.approval_status = PendingDestination.ApprovalStatus.PENDING
        
        response = super().form_valid(form)
        
        # Send email notification to managers and admins
        admin_notification_sent = send_destination_submission_notification(
            destination=self.object,
            submitter=self.request.user
        )
        
        # Send confirmation email to the guide
        guide_notification_sent = send_guide_submission_confirmation(
            pending_destination=self.object,
            submitter=self.request.user
        )
        
        # Log if notifications failed
        import logging
        logger = logging.getLogger(__name__)
        
        if not admin_notification_sent:
            logger.warning(
                f"Failed to send admin notification email for destination submission: {self.object.name}"
            )
        
        if not guide_notification_sent:
            logger.warning(
                f"Failed to send guide confirmation email for destination submission: {self.object.name}"
            )
        
        # Store destination in session for success page
        self.request.session['submitted_destination_id'] = self.object.id
        self.request.session['submission_date'] = timezone.now().strftime('%B %d, %Y')
        
        return response
        
    def get_success_url(self):
        """
        Return URL to the submission success page.
        
        Returns:
            str: URL to destination submission success page
        """
        return reverse_lazy('destinations:submission_success')
    
    def get_context_data(self, **kwargs):
        """
        Add page title and form description to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context with title and form description
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Submit New Destination'
        context['form_description'] = (
            'Submit a new destination for approval. '
            'Your submission will be reviewed by our team before being published. '
            'You will earn reward points if your destination is approved.'
        )
        return context


class SubmissionSuccessView(GuideRequiredMixin, TemplateView):
    """
    View to display a success page after a destination submission.
    
    This view shows confirmation details after a guide has successfully submitted
    a destination. It includes submission date, destination details, and next steps
    in the approval process.
    """
    template_name = 'destinations/destination_submission_success.html'
    
    def get_context_data(self, **kwargs):
        """
        Add destination and submission details to the context.
        
        Retrieves the submitted destination from the session to display
        its details on the success page.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context with destination and submission information
        """
        context = super().get_context_data(**kwargs)
        
        # Get submitted destination details from session
        destination_id = self.request.session.get('submitted_destination_id')
        submission_date = self.request.session.get('submission_date')
        
        # Clear session variables
        if 'submitted_destination_id' in self.request.session:
            del self.request.session['submitted_destination_id']
        
        if 'submission_date' in self.request.session:
            del self.request.session['submission_date']
            
        # Get destination object
        if destination_id:
            try:
                destination = PendingDestination.objects.get(id=destination_id)
                context['destination'] = destination
            except PendingDestination.DoesNotExist:
                pass
                
        context['submission_date'] = submission_date or timezone.now().strftime('%B %d, %Y')
        
        return context


class PendingDestinationUpdateView(GuideRequiredMixin, UpdateView):
    """
    View for guides to update their pending destination submissions.
    
    This view allows guides to edit their pending destination submissions
    before they are approved or if they have been rejected with feedback.
    Updates to already approved submissions are not permitted.
    """
    model = PendingDestination
    form_class = PendingDestinationForm
    template_name = 'destinations/destination_form.html'
    context_object_name = 'destination'
    
    def get_queryset(self):
        """
        Restrict queryset to the guide's own pending destinations.
        
        Only allows guides to edit their own pending submissions that
        haven't been approved yet.
        
        Returns:
            QuerySet: Filtered queryset of pending destinations by current user
        """
        return PendingDestination.objects.filter(
            created_by=self.request.user,
            approval_status__in=[
                PendingDestination.ApprovalStatus.PENDING,
                PendingDestination.ApprovalStatus.REJECTED
            ]
        )
    
    def form_valid(self, form):
        """
        Update submission and reset status if previously rejected.
        
        If a rejected submission is being updated, reset its status to pending
        and clear the rejection reason so it can be reviewed again.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponseRedirect: Redirect after successful form submission
        """
        # If submission was previously rejected, reset to pending
        if form.instance.approval_status == PendingDestination.ApprovalStatus.REJECTED:
            form.instance.approval_status = PendingDestination.ApprovalStatus.PENDING
            form.instance.rejection_reason = ''
        
        response = super().form_valid(form)
        messages.success(self.request, f'Destination "{self.object.name}" updated and resubmitted for approval.')
        return response
    
    def get_success_url(self):
        """
        Return to the guide dashboard after update.
        
        Returns:
            str: URL to guide dashboard
        """
        return reverse_lazy('destinations:guide_dashboard')
    
    def get_context_data(self, **kwargs):
        """
        Add page title and form context based on submission status.
        
        If the submission was rejected, include the rejection reason in the
        context to display to the user.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Enhanced context with title and status information
        """
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Destination Submission: {self.object.name}'
        
        # Add rejection information if applicable
        if self.object.approval_status == PendingDestination.ApprovalStatus.REJECTED:
            context['rejection_reason'] = self.object.rejection_reason
            context['form_description'] = (
                'Your submission was rejected. Please review the feedback below '
                'and make the necessary changes before resubmitting.'
            )
        else:
            context['form_description'] = 'Update your pending destination submission.'
            
        return context


class DestinationUpdateView(GuideRequiredMixin, UpdateView):
    """
    View for guides to update their approved destinations.
    
    This view allows guides to edit destinations that have already been approved
    and published. Only the destination owner can make these updates.
    """
    model = Destination
    form_class = DestinationForm
    template_name = 'destinations/destination_form.html'
    context_object_name = 'destination'
    
    def get_queryset(self):
        """
        Only allow guides to edit their own destinations.
        
        Restricts the queryset to only include destinations created by the
        current user for security and access control.
        
        Returns:
            QuerySet: Filtered destinations created by current user
        """
        return super().get_queryset().filter(created_by=self.request.user)
    
    def form_valid(self, form):
        """
        Show success message on successful update.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponseRedirect: Redirect after successful form submission
        """
        response = super().form_valid(form)
        messages.success(self.request, f'Destination "{self.object.name}" updated successfully!')
        return response
    
    def get_success_url(self):
        """
        Redirect to the destination detail page after update.
        
        Returns:
            str: URL to destination detail page
        """
        return reverse_lazy('destinations:destination_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        """
        Add page title to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context with title
        """
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        return context


class PendingDestinationImageCreateView(GuideRequiredMixin, CreateView):
    """
    View for guides to add images to pending destinations.
    
    This view handles image uploads to pending destination submissions.
    Images uploaded here will be transferred to the main DestinationImage table
    if the destination is approved by a manager or admin.
    """
    model = PendingDestinationImage
    form_class = PendingDestinationImageForm
    template_name = 'destinations/destination_image_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verify the pending destination exists and belongs to the guide.
        
        This check prevents guides from uploading images to pending destinations
        they don't own or that don't exist.
        
        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The dispatched response
        """
        self.pending_destination = get_object_or_404(
            PendingDestination, 
            pk=self.kwargs.get('pk'),
            created_by=self.request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Save the image and associate it with the pending destination.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponseRedirect: Redirect after successful form submission
        """
        form.instance.pending_destination = self.pending_destination
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Image added to pending destination "{self.pending_destination.name}"'
        )
        return response
    
    def get_success_url(self):
        """
        Return to the image management page for this pending destination.
        
        Returns:
            str: URL to pending destination images page
        """
        return reverse_lazy(
            'destinations:pending_destination_images',
            kwargs={'pk': self.pending_destination.pk}
        )
    
    def get_context_data(self, **kwargs):
        """
        Add pending destination and page title to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context with title and pending destination
        """
        context = super().get_context_data(**kwargs)
        context['pending_destination'] = self.pending_destination
        context['title'] = f'Add Image to {self.pending_destination.name}'
        return context


class PendingDestinationImageListView(GuideRequiredMixin, ListView):
    """
    View for guides to manage images for their pending destinations.
    
    This view displays all images associated with a specific pending destination
    and allows guides to add, edit, or delete them before the destination is
    submitted for approval or while it's in the pending state.
    """
    model = PendingDestinationImage
    template_name = 'destinations/destination_images.html'
    context_object_name = 'images'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verify the pending destination exists and belongs to the guide.
        
        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The dispatched response
        """
        self.pending_destination = get_object_or_404(
            PendingDestination, 
            pk=self.kwargs.get('pk'),
            created_by=self.request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Get images associated with this pending destination.
        
        Returns:
            QuerySet: Images for this pending destination
        """
        return PendingDestinationImage.objects.filter(
            pending_destination=self.pending_destination
        )
    
    def get_context_data(self, **kwargs):
        """
        Add pending destination and page title to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context with title, pending destination, and form
        """
        context = super().get_context_data(**kwargs)
        context['pending_destination'] = self.pending_destination
        context['title'] = f'Images for {self.pending_destination.name}'
        context['form'] = PendingDestinationImageForm()
        
        # Add status information
        context['status_label'] = self.pending_destination.get_approval_status_display()
        context['status_class'] = {
            PendingDestination.ApprovalStatus.PENDING: 'text-yellow-500',
            PendingDestination.ApprovalStatus.APPROVED: 'text-green-500',
            PendingDestination.ApprovalStatus.REJECTED: 'text-red-500'
        }.get(self.pending_destination.approval_status, 'text-gray-500')
        
        return context


class PendingDestinationListView(GuideRequiredMixin, ListView):
    """
    View for guides to see all their pending destination submissions.
    
    This view lists all pending, approved, and rejected destination submissions
    made by the guide, allowing them to track the status of their submissions.
    """
    model = PendingDestination
    template_name = 'destinations/pending_destinations.html'
    context_object_name = 'pending_destinations'
    
    def get_queryset(self):
        """
        Get all pending destinations created by the current user.
        
        Returns:
            QuerySet: All pending destinations by current user
        """
        return PendingDestination.objects.filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        """
        Add filtered lists by status and statistics to the context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context with categorized lists and statistics
        """
        context = super().get_context_data(**kwargs)
        
        # Get pending destinations by status
        user = self.request.user
        context['pending_review'] = PendingDestination.objects.filter(
            created_by=user,
            approval_status=PendingDestination.ApprovalStatus.PENDING
        )
        context['approved'] = PendingDestination.objects.filter(
            created_by=user,
            approval_status=PendingDestination.ApprovalStatus.APPROVED
        )
        context['rejected'] = PendingDestination.objects.filter(
            created_by=user,
            approval_status=PendingDestination.ApprovalStatus.REJECTED
        )
        
        # Calculate statistics
        context['stats'] = {
            'total': context['pending_destinations'].count(),
            'pending_count': context['pending_review'].count(),
            'approved_count': context['approved'].count(),
            'rejected_count': context['rejected'].count(),
        }
        
        context['title'] = 'My Destination Submissions'
        return context


class DestinationDeleteView(GuideRequiredMixin, DeleteView):
    """
    View for guides to delete their own destinations.
    
    This view allows guides to delete destinations they have created that have
    been approved. The view includes confirmation to prevent accidental deletion.
    """
    model = Destination
    template_name = 'destinations/destination_confirm_delete.html'
    success_url = reverse_lazy('destinations:guide_dashboard')
    
    def get_queryset(self):
        """
        Only allow guides to delete their own destinations.
        
        This ensures guides can only delete destinations they have created
        for security and proper access control.
        
        Returns:
            QuerySet: Filtered destinations created by current user
        """
        return super().get_queryset().filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """
        Show success message after deletion.
        
        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        destination = self.get_object()
        messages.success(request, f'Destination "{destination.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


class PendingDestinationDeleteView(GuideRequiredMixin, DeleteView):
    """
    View for guides to delete their pending destination submissions.
    
    This view allows guides to withdraw or delete their pending destination
    submissions that haven't been approved yet.
    """
    model = PendingDestination
    template_name = 'destinations/pending_destination_confirm_delete.html'
    success_url = reverse_lazy('destinations:guide_dashboard')
    
    def get_queryset(self):
        """
        Only allow guides to delete their own pending destinations.
        
        Additionally, restrict deletion to only pending or rejected destinations.
        Already approved destinations cannot be deleted through this view.
        
        Returns:
            QuerySet: Filtered pending destinations by current user and status
        """
        return PendingDestination.objects.filter(
            created_by=self.request.user,
            approval_status__in=[
                PendingDestination.ApprovalStatus.PENDING,
                PendingDestination.ApprovalStatus.REJECTED
            ]
        )
    
    def delete(self, request, *args, **kwargs):
        """
        Show appropriate message after deletion based on submission status.
        
        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        pending_destination = self.get_object()
        
        if pending_destination.approval_status == PendingDestination.ApprovalStatus.PENDING:
            message = f'Pending destination "{pending_destination.name}" withdrawn successfully!'
        else:
            message = f'Rejected destination "{pending_destination.name}" removed successfully!'
            
        messages.success(request, message)
        return super().delete(request, *args, **kwargs)


class AttractionCreateView(GuideRequiredMixin, CreateView):
    """View for guides to create new attractions."""
    model = Attraction
    form_class = AttractionForm
    template_name = 'destinations/attraction_form.html'
    
    def get_form_kwargs(self):
        """Filter destinations to only those owned by the current guide."""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_form_kwargs().get('instance')
        if 'data' in kwargs:
            data = kwargs['data'].copy()
            kwargs['data'] = data
        return kwargs
    
    def get_form(self, form_class=None):
        """Filter the destination queryset to only show the guide's destinations."""
        form = super().get_form(form_class)
        form.fields['destination'].queryset = Destination.objects.filter(guide=self.request.user)
        return form
    
    def form_valid(self, form):
        """Set the current user as the guide for the new attraction."""
        response = super().form_valid(form)
        messages.success(self.request, f'Attraction "{self.object.name}" created successfully!')
        return response
    
    def get_success_url(self):
        """Redirect to the attraction detail page after creation."""
        return reverse_lazy('destinations:attraction_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        """Add page title to the context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Attraction'
        return context


class AttractionUpdateView(GuideRequiredMixin, UpdateView):
    """View for guides to update their attractions."""
    model = Attraction
    form_class = AttractionForm
    template_name = 'destinations/attraction_form.html'
    context_object_name = 'attraction'
    
    def get_queryset(self):
        """Only allow guides to edit their own attractions."""
        return super().get_queryset().filter(destination__guide=self.request.user)
    
    def get_form(self, form_class=None):
        """Filter the destination queryset to only show the guide's destinations."""
        form = super().get_form(form_class)
        form.fields['destination'].queryset = Destination.objects.filter(guide=self.request.user)
        return form
    
    def form_valid(self, form):
        """Show success message on successful update."""
        response = super().form_valid(form)
        messages.success(self.request, f'Attraction "{self.object.name}" updated successfully!')
        return response
    
    def get_success_url(self):
        """Redirect to the attraction detail page after update."""
        return reverse_lazy('destinations:attraction_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        """Add page title to the context."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        return context


class AttractionDeleteView(GuideRequiredMixin, DeleteView):
    """View for guides to delete their attractions."""
    model = Attraction
    template_name = 'destinations/attraction_confirm_delete.html'
    context_object_name = 'attraction'
    
    def get_queryset(self):
        """Only allow guides to delete their own attractions."""
        return super().get_queryset().filter(destination__guide=self.request.user)
    
    def get_success_url(self):
        """Redirect to the destination detail page after deletion."""
        return reverse_lazy('destinations:destination_detail', 
                          kwargs={'slug': self.object.destination.slug})
    
    def delete(self, request, *args, **kwargs):
        """Show success message on successful deletion."""
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Attraction deleted successfully!')
        return response


@login_required
@require_http_methods(["POST"])
def upload_destination_image(request, destination_id):
    """View for guides to upload images for their destinations."""
    destination = get_object_or_404(Destination, id=destination_id, guide=request.user)
    
    if request.method == 'POST':
        form = DestinationImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.destination = destination
            image.save()
            messages.success(request, 'Image uploaded successfully!')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('destinations:destination_update', pk=destination_id)


@login_required
@require_http_methods(["POST"])
def delete_destination_image(request, image_id):
    """View for guides to delete destination images."""
    image = get_object_or_404(DestinationImage, id=image_id, destination__guide=request.user)
    destination_id = image.destination.id
    image.delete()
    messages.success(request, 'Image deleted successfully!')
    return redirect('destinations:destination_update', pk=destination_id)
