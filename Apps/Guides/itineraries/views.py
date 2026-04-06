"""
Views for the itineraries application.

This file contains all the view functions and classes that handle
HTTP requests for creating, viewing, updating, and deleting itineraries.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import Itinerary, ItineraryDay, Activity
from destinations.models import Destination
from tours.models import Tour


class ItineraryListView(ListView):
    """
    Display a list of public itineraries and the user's own itineraries.
    
    This view shows public itineraries created by all users and
    private itineraries created by the current user.
    """
    model = Itinerary
    template_name = 'itineraries/itinerary_list.html'
    context_object_name = 'itineraries'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the queryset of itineraries to display.
        
        Returns:
            QuerySet: Filtered queryset of Itinerary objects
        """
        # Base queryset - either public itineraries or those owned by the current user
        queryset = Itinerary.objects.select_related('user', 'tour')
        
        if self.request.user.is_authenticated:
            # If user is logged in, show public itineraries and their own
            queryset = queryset.filter(
                is_public=True
            ) | Itinerary.objects.filter(
                user=self.request.user
            )
        else:
            # If user is not logged in, only show public itineraries
            queryset = queryset.filter(is_public=True)
            
        # Apply sorting
        sort_by = self.request.GET.get('sort', 'start_date')
        if sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'created':
            queryset = queryset.order_by('-created_at')
        else:  # Default to start_date
            queryset = queryset.order_by('start_date')
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort', 'start_date')
        return context


class MyItinerariesView(LoginRequiredMixin, ListView):
    """
    Display a list of itineraries created by the current user.
    
    This view requires authentication and only shows itineraries
    owned by the current user.
    """
    model = Itinerary
    template_name = 'itineraries/my_itineraries.html'
    context_object_name = 'itineraries'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the queryset of the current user's itineraries.
        
        Returns:
            QuerySet: Filtered queryset of the user's Itinerary objects
        """
        return Itinerary.objects.filter(user=self.request.user).order_by('-start_date')


class ItineraryDetailView(DetailView):
    """
    Display detailed information about a single itinerary.
    
    This view shows the itinerary details, including days and activities.
    Users can only view public itineraries or their own private ones.
    """
    model = Itinerary
    template_name = 'itineraries/itinerary_detail.html'
    context_object_name = 'itinerary'
    
    def get_queryset(self):
        """
        Get the queryset of itineraries accessible to the current user.
        
        Returns:
            QuerySet: Filtered queryset of accessible Itinerary objects
        """
        queryset = Itinerary.objects.all()
        
        if self.request.user.is_authenticated:
            # If user is logged in, they can view public itineraries and their own
            return queryset.filter(
                is_public=True
            ) | queryset.filter(
                user=self.request.user
            )
        else:
            # If user is not logged in, they can only view public itineraries
            return queryset.filter(is_public=True)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        
        Adds days and activities to the context for display.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Context dictionary with added data
        """
        context = super().get_context_data(**kwargs)
        itinerary = self.get_object()
        
        # Get days with activities, optimized to minimize database queries
        days = (
            ItineraryDay.objects
            .filter(itinerary=itinerary)
            .select_related('destination')
            .prefetch_related('activities')
            .order_by('day_number')
        )
        
        context['days'] = days
        context['can_edit'] = self.request.user == itinerary.user
        
        return context


class ItineraryCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new itinerary.
    
    This view requires authentication and allows users to create
    a new itinerary with initial days based on start and end dates.
    """
    model = Itinerary
    template_name = 'itineraries/itinerary_form.html'
    fields = ['title', 'description', 'tour', 'start_date', 'end_date', 'is_public']
    success_url = reverse_lazy('itineraries:my_itineraries')
    
    def form_valid(self, form):
        """
        Process the valid form data.
        
        Sets the current user as the owner of the itinerary and
        creates initial itinerary days based on the date range.
        
        Args:
            form: The form object with validated data
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        # Set the current user as the owner
        form.instance.user = self.request.user
        
        # Save the itinerary
        response = super().form_valid(form)
        itinerary = self.object
        
        # Generate days for the itinerary
        start_date = itinerary.start_date
        end_date = itinerary.end_date
        day_number = 1
        
        current_date = start_date
        while current_date <= end_date:
            ItineraryDay.objects.create(
                itinerary=itinerary,
                day_number=day_number,
                date=current_date
            )
            current_date += timedelta(days=1)
            day_number += 1
        
        messages.success(self.request, _("Itinerary created successfully! Now you can add activities to each day."))
        return response
    
    def get_form(self, form_class=None):
        """
        Get and customize the form instance.
        
        Adds default values and customizes form widgets.
        
        Args:
            form_class: The form class to use
            
        Returns:
            Form: Customized form instance
        """
        form = super().get_form(form_class)
        
        # Set default dates if not provided
        if not form.initial.get('start_date'):
            form.initial['start_date'] = timezone.now().date() + timedelta(days=30)
        if not form.initial.get('end_date'):
            form.initial['end_date'] = timezone.now().date() + timedelta(days=37)  # Default to a week-long trip
            
        # If a tour ID is in the request, pre-select it
        tour_id = self.request.GET.get('tour')
        if tour_id:
            try:
                form.initial['tour'] = Tour.objects.get(pk=tour_id)
            except Tour.DoesNotExist:
                pass
        
        return form


class ItineraryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing itinerary.
    
    This view requires authentication and ensures that only the owner
    can update the itinerary.
    """
    model = Itinerary
    template_name = 'itineraries/itinerary_form.html'
    fields = ['title', 'description', 'tour', 'is_public']
    
    def test_func(self):
        """
        Test if the current user has permission to update the itinerary.
        
        Returns:
            bool: True if the user is the owner, False otherwise
        """
        itinerary = self.get_object()
        return self.request.user == itinerary.user
    
    def get_success_url(self):
        """
        Get the URL to redirect to after a successful update.
        
        Returns:
            str: URL to the itinerary detail page
        """
        return reverse_lazy('itineraries:itinerary_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """
        Process the valid form data.
        
        Updates the itinerary and shows a success message.
        
        Args:
            form: The form object with validated data
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        messages.success(self.request, _("Itinerary updated successfully!"))
        return response


class ItineraryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete an existing itinerary.
    
    This view requires authentication and ensures that only the owner
    can delete the itinerary.
    """
    model = Itinerary
    template_name = 'itineraries/itinerary_confirm_delete.html'
    success_url = reverse_lazy('itineraries:my_itineraries')
    
    def test_func(self):
        """
        Test if the current user has permission to delete the itinerary.
        
        Returns:
            bool: True if the user is the owner, False otherwise
        """
        itinerary = self.get_object()
        return self.request.user == itinerary.user
    
    def delete(self, request, *args, **kwargs):
        """
        Delete the itinerary and show a success message.
        
        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        messages.success(request, _("Itinerary deleted successfully!"))
        return super().delete(request, *args, **kwargs)


@login_required
def add_activity(request, day_id):
    """
    Add a new activity to an itinerary day.
    
    This view requires authentication and handles both the GET request
    (displaying the form) and the POST request (saving the activity).
    
    Args:
        request: The HTTP request object
        day_id: The ID of the ItineraryDay to add the activity to
        
    Returns:
        HttpResponse: Rendered template or redirect
    """
    day = get_object_or_404(ItineraryDay, pk=day_id)
    
    # Check if the user is the owner of the itinerary
    if request.user != day.itinerary.user:
        messages.error(request, _("You don't have permission to add activities to this itinerary."))
        return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)
    
    if request.method == 'POST':
        # Process the form data
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location', '')
        cost = request.POST.get('cost') or None
        booking_reference = request.POST.get('booking_reference', '')
        
        # Create the activity
        Activity.objects.create(
            itinerary_day=day,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            cost=cost,
            booking_reference=booking_reference
        )
        
        messages.success(request, _("Activity added successfully!"))
        return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)
    
    # Render the form for GET request
    return render(request, 'itineraries/add_activity.html', {'day': day})


@login_required
def edit_activity(request, activity_id):
    """
    Edit an existing activity.
    
    This view requires authentication and handles both the GET request
    (displaying the form with current data) and the POST request (updating the activity).
    
    Args:
        request: The HTTP request object
        activity_id: The ID of the Activity to edit
        
    Returns:
        HttpResponse: Rendered template or redirect
    """
    activity = get_object_or_404(Activity, pk=activity_id)
    day = activity.itinerary_day
    
    # Check if the user is the owner of the itinerary
    if request.user != day.itinerary.user:
        messages.error(request, _("You don't have permission to edit activities in this itinerary."))
        return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)
    
    if request.method == 'POST':
        # Process the form data
        activity.title = request.POST.get('title')
        activity.description = request.POST.get('description', '')
        activity.start_time = request.POST.get('start_time')
        activity.end_time = request.POST.get('end_time')
        activity.location = request.POST.get('location', '')
        activity.cost = request.POST.get('cost') or None
        activity.booking_reference = request.POST.get('booking_reference', '')
        activity.save()
        
        messages.success(request, _("Activity updated successfully!"))
        return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)
    
    # Render the form for GET request with current data
    return render(request, 'itineraries/edit_activity.html', {'activity': activity})


@login_required
def delete_activity(request, activity_id):
    """
    Delete an existing activity.
    
    This view requires authentication and ensures only the owner
    can delete activities from their itineraries.
    
    Args:
        request: The HTTP request object
        activity_id: The ID of the Activity to delete
        
    Returns:
        HttpResponse: Redirect response
    """
    activity = get_object_or_404(Activity, pk=activity_id)
    day = activity.itinerary_day
    
    # Check if the user is the owner of the itinerary
    if request.user != day.itinerary.user:
        messages.error(request, _("You don't have permission to delete activities from this itinerary."))
    else:
        activity.delete()
        messages.success(request, _("Activity deleted successfully!"))
    
    return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)


@login_required
def edit_itinerary_day(request, day_id):
    """
    Edit an itinerary day's details.
    
    This view requires authentication and handles both the GET request
    (displaying the form) and the POST request (updating the day).
    
    Args:
        request: The HTTP request object
        day_id: The ID of the ItineraryDay to edit
        
    Returns:
        HttpResponse: Rendered template or redirect
    """
    day = get_object_or_404(ItineraryDay, pk=day_id)
    
    # Check if the user is the owner of the itinerary
    if request.user != day.itinerary.user:
        messages.error(request, _("You don't have permission to edit this itinerary."))
        return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)
    
    if request.method == 'POST':
        # Process the form data
        destination_id = request.POST.get('destination')
        if destination_id:
            try:
                day.destination = Destination.objects.get(pk=destination_id)
            except Destination.DoesNotExist:
                day.destination = None
        else:
            day.destination = None
            
        day.accommodation_details = request.POST.get('accommodation_details', '')
        day.notes = request.POST.get('notes', '')
        day.save()
        
        messages.success(request, _("Day details updated successfully!"))
        return redirect('itineraries:itinerary_detail', pk=day.itinerary.pk)
    
    # Get all destinations for the form
    destinations = Destination.objects.all()
    
    # Render the form for GET request
    return render(request, 'itineraries/edit_day.html', {
        'day': day,
        'destinations': destinations
    })


def itinerary_share(request, pk):
    """
    Share an itinerary with others.
    
    This view generates a shareable link for an itinerary.
    
    Args:
        request: The HTTP request object
        pk: The primary key of the Itinerary to share
        
    Returns:
        HttpResponse: Rendered template
    """
    itinerary = get_object_or_404(Itinerary, pk=pk)
    
    # If not public and not the owner, don't allow sharing
    if not itinerary.is_public and (not request.user.is_authenticated or request.user != itinerary.user):
        messages.error(request, _("This itinerary is not available for sharing."))
        return redirect('itineraries:itinerary_list')
    
    # Generate the sharing URL (absolute URL)
    share_url = request.build_absolute_uri(
        reverse_lazy('itineraries:itinerary_detail', kwargs={'pk': pk})
    )
    
    return render(request, 'itineraries/share_itinerary.html', {
        'itinerary': itinerary,
        'share_url': share_url
    })


# AI Itinerary Generation Views

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
import json

from .ai_services import ItineraryAIService


@login_required
def ai_itinerary_form(request):
    """
    Display form for AI itinerary generation.
    
    This view shows the form for users to input their preferences for 
    AI-generated travel itineraries.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with destinations list
    """
    # Get all active destinations for the form and order by city name
    destinations = Destination.objects.filter(is_active=True).order_by('city', 'name')
    # Annotate each destination with a display name that shows city name
    for dest in destinations:
        dest.display_name = dest.city or dest.name
    
    # Common interests for the form
    interests = [
        'History', 'Art', 'Culture', 'Food', 'Shopping', 
        'Nature', 'Adventure', 'Relaxation', 'Architecture', 
        'Nightlife', 'Family-friendly', 'Photography'
    ]
    
    # Budget levels
    budget_levels = ['budget', 'medium', 'luxury']
    
    # Travel pace options
    travel_paces = ['relaxed', 'moderate', 'intensive']
    
    # Default start date (30 days from now)
    default_start_date = timezone.now().date() + timedelta(days=30)
    
    # Default end date (7 days after start date)
    default_end_date = default_start_date + timedelta(days=7)
    
    context = {
        'destinations': destinations,
        'interests': interests,
        'budget_levels': budget_levels,
        'travel_paces': travel_paces,
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'itineraries/ai_itinerary_form.html', context)


@login_required
@require_POST
def ai_generate_itinerary(request):
    """
    Process the AI itinerary generation form and create a new itinerary.
    
    This view handles the form submission, calls the AI service to generate
    an itinerary, and creates the corresponding database records.
    
    Args:
        request: The HTTP request object with form data
        
    Returns:
        HttpResponse: Redirect to the created itinerary or back to the form with errors
    """
    try:
        # Extract form data
        destination_id = request.POST.get('destination')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        interests = request.POST.getlist('interests')
        budget_level = request.POST.get('budget_level', 'medium')
        travel_pace = request.POST.get('travel_pace', 'moderate')
        accessibility_needs = request.POST.getlist('accessibility_needs')
        is_public = request.POST.get('is_public') == 'on'
        
        # Validate required fields
        if not all([destination_id, start_date_str, end_date_str, title, interests]):
            messages.error(request, _('Please fill in all required fields.'))
            return redirect('itineraries:ai_itinerary_form')
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Validate date range
            if start_date > end_date:
                messages.error(request, _('End date must be after start date.'))
                return redirect('itineraries:ai_itinerary_form')
                
            if (end_date - start_date).days > 14:
                messages.error(request, _('Maximum trip duration is 14 days.'))
                return redirect('itineraries:ai_itinerary_form')
        except ValueError:
            messages.error(request, _('Invalid date format.'))
            return redirect('itineraries:ai_itinerary_form')
        
        # Get destination
        try:
            destination = Destination.objects.get(pk=destination_id)
        except Destination.DoesNotExist:
            messages.error(request, _('Selected destination not found.'))
            return redirect('itineraries:ai_itinerary_form')
        
        # Show processing message
        messages.info(request, _('Generating your itinerary. This may take a minute...'))
        
        # Call AI service to generate itinerary
        ai_service = ItineraryAIService()
        itinerary_data = ai_service.generate_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            budget_level=budget_level,
            travel_pace=travel_pace,
            accessibility_needs=accessibility_needs
        )
        
        # Check for errors in AI response
        if 'error' in itinerary_data:
            messages.error(request, _(f"AI Error: {itinerary_data['error']}"))
            return redirect('itineraries:ai_itinerary_form')
        
        # Create new itinerary record
        itinerary = Itinerary.objects.create(
            title=title or itinerary_data.get('itinerary_title', f"{destination.name} Itinerary"),
            description=description or itinerary_data.get('overview', ''),
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            is_public=is_public
        )
        
        # Create days and activities from AI data
        for day_data in itinerary_data.get('days', []):
            # Create day
            day_number = day_data.get('day_number', 1)
            day_date = start_date + timedelta(days=day_number - 1)
            
            day = ItineraryDay.objects.create(
                itinerary=itinerary,
                day_number=day_number,
                date=day_date,
                destination=destination,  # Using the main destination for now
                accommodation_details=day_data.get('accommodation', ''),
                notes=day_data.get('notes', '')
            )
            
            # Create activities
            for activity_data in day_data.get('activities', []):
                try:
                    # Parse times
                    start_time = datetime.strptime(activity_data.get('start_time', '09:00'), '%H:%M').time()
                    end_time = datetime.strptime(activity_data.get('end_time', '10:00'), '%H:%M').time()
                    
                    Activity.objects.create(
                        day=day,
                        title=activity_data.get('title', 'Activity'),
                        description=activity_data.get('description', ''),
                        start_time=start_time,
                        end_time=end_time,
                        location=activity_data.get('location', ''),
                        cost=None  # Cost is a string in the API response, can't convert directly
                    )
                except ValueError as e:
                    # If there's an issue with a specific activity, log it but continue
                    print(f"Error creating activity: {str(e)}")
        
        messages.success(request, _('AI-generated itinerary created successfully!'))
        return redirect('itineraries:itinerary_detail', pk=itinerary.pk)
        
    except Exception as e:
        messages.error(request, _(f'Error generating itinerary: {str(e)}'))
        return redirect('itineraries:ai_itinerary_form')


@login_required
def ai_activity_recommendations(request, destination_id):
    """
    Get AI-generated activity recommendations for a specific destination.
    
    This view returns JSON data with activity recommendations that can be
    used by JavaScript to dynamically update the UI.
    
    Args:
        request: The HTTP request object
        destination_id: ID of the destination to get recommendations for
        
    Returns:
        JsonResponse: Activity recommendations data
    """
    try:
        # Get destination
        destination = get_object_or_404(Destination, pk=destination_id)
        
        # Get interests from query params
        interests = request.GET.getlist('interests', [])
        if not interests:
            interests = ['Culture', 'Sightseeing']  # Default interests
            
        # Number of recommendations to generate
        count = min(int(request.GET.get('count', 5)), 10)  # Cap at 10 max
        
        # Call AI service
        ai_service = ItineraryAIService()
        recommendations = ai_service.generate_activity_recommendations(
            destination=destination,
            interests=interests,
            count=count
        )
        
        return JsonResponse({'recommendations': recommendations})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def ai_enhance_day(request, itinerary_id, day_id):
    """
    Enhance a specific day of an itinerary with AI suggestions.
    
    This view allows users to get AI recommendations for a specific day
    in their itinerary and optionally add them to the day.
    
    Args:
        request: The HTTP request object
        itinerary_id: ID of the itinerary
        day_id: ID of the day to enhance
        
    Returns:
        HttpResponse: Rendered template or redirect
    """
    # Get the itinerary and day
    itinerary = get_object_or_404(Itinerary, pk=itinerary_id, user=request.user)
    day = get_object_or_404(ItineraryDay, pk=day_id, itinerary=itinerary)
    
    if request.method == 'POST':
        # Process AI enhancement request
        interests = request.POST.getlist('interests', [])
        if not interests:
            messages.error(request, _('Please select at least one interest.'))
            return redirect('itineraries:ai_enhance_day', itinerary_id=itinerary_id, day_id=day_id)
        
        # Call AI service for recommendations
        ai_service = ItineraryAIService()
        recommendations = ai_service.generate_activity_recommendations(
            destination=day.destination or itinerary.destination,
            interests=interests,
            count=5
        )
        
        # Check which activities to add
        selected_activities = request.POST.getlist('selected_activities', [])
        for i, activity_idx in enumerate(selected_activities):
            try:
                idx = int(activity_idx)
                if 0 <= idx < len(recommendations):
                    activity_data = recommendations[idx]
                    
                    # Create a new activity
                    # Start times are staggered by 2 hours starting at 9:00 AM
                    start_hour = 9 + (i * 2)
                    if start_hour > 21:  # Don't schedule past 9 PM
                        start_hour = 21
                    
                    start_time = datetime.strptime(f"{start_hour}:00", '%H:%M').time()
                    end_time = datetime.strptime(f"{start_hour + 1}:30", '%H:%M').time()
                    
                    Activity.objects.create(
                        day=day,
                        title=activity_data.get('title', 'AI Recommended Activity'),
                        description=activity_data.get('description', ''),
                        start_time=start_time,
                        end_time=end_time,
                        location=activity_data.get('location', ''),
                        cost=None
                    )
                    
            except (ValueError, IndexError):
                continue
        
        messages.success(request, _('Day enhanced with AI recommendations!'))
        return redirect('itineraries:itinerary_detail', pk=itinerary_id)
    
    # For GET request, show enhancement form
    # Common interests for the form
    interests = [
        'History', 'Art', 'Culture', 'Food', 'Shopping', 
        'Nature', 'Adventure', 'Relaxation', 'Architecture', 
        'Nightlife', 'Family-friendly', 'Photography'
    ]
    
    context = {
        'itinerary': itinerary,
        'day': day,
        'interests': interests,
    }
    
    return render(request, 'itineraries/ai_enhance_day.html', context)
