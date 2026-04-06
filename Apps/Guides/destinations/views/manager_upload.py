"""
Manager Destination Upload View

This module provides functionality for managers to directly upload destinations
to the main destinations table without going through the approval workflow.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test

# Local imports
from destinations.forms import DestinationForm
from destinations.models import Destination, DestinationImage
from destinations.views.admin import StaffRequiredMixin

class ManagerDestinationUploadView(StaffRequiredMixin, FormView):
    """
    View for managers to directly upload destinations to the main table.
    
    This view allows staff users to bypass the approval workflow and directly
    add destinations to the main destinations table.
    """
    template_name = 'destinations/admin/manager_destination_upload.html'
    form_class = DestinationForm
    success_url = reverse_lazy('destinations:admin_manager_dashboard')
    
    def form_valid(self, form):
        """
        Process the form and create a new destination in the main table.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponseRedirect: Redirects to success_url on success
        """
        # Save the destination with the current user as the creator
        destination = form.save(commit=False)
        destination.created_by = self.request.user
        destination.approval_status = Destination.ApprovalStatus.APPROVED  # Auto-approve
        destination.save()
        
        # Handle multiple images if provided
        images = self.request.FILES.getlist('images')
        for i, image in enumerate(images):
            DestinationImage.objects.create(
                destination=destination,
                image=image,
                is_primary=(i == 0)  # First image is primary
            )
        
        messages.success(
            self.request,
            f'Successfully created destination: {destination.name}'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data to the template.
        
        Returns:
            dict: Context data for the template
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload New Destination'
        return context
