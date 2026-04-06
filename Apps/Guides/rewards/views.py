"""
Rewards App Views.

This module contains all view functions and classes related to the reward points system,
including views for users to check their points, redeem rewards, and for admins to manage
the reward system.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from django.core.paginator import Paginator

from .models import RewardPoints, RewardRedemption, RewardTier, RewardRedemptionType
from .forms import RedemptionForm


class RewardsHomeView(LoginRequiredMixin, TemplateView):
    """
    Main rewards dashboard for users.
    
    This view shows users their current points balance, tier status, progress to next tier,
    recent point-earning activities, recent redemptions, and available redemption options.
    The dashboard serves as the central hub for all rewards-related functionality.
    
    The view uses LoginRequiredMixin to ensure only authenticated users can access their rewards.
    It inherits from TemplateView to render the rewards_home.html template with the appropriate context.
    """
    template_name = 'rewards/rewards_home.html'
    
    def get_context_data(self, **kwargs):
        """
        Prepare the context data for the rewards dashboard.
        
        This method gathers all the information needed to display the user's reward status,
        including points balance, tier, recent activities, and redemption options.
        
        The method performs several key operations:
        1. Retrieves the user's current points balance using the RewardPoints model
        2. Determines the user's current tier based on their points
        3. Identifies the next tier they can achieve
        4. Calculates progress percentage toward the next tier
        5. Fetches recent point activities and redemptions
        6. Prepares available redemption options based on points balance
        
        All data is formatted for easy display in the rewards_home.html template with
        the indigo/violet color scheme for consistency with the site design.
        
        Args:
            **kwargs: Additional keyword arguments from the URL
            
        Returns:
            dict: Context dictionary for the template containing all rewards data
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get current points balance
        points_balance = RewardPoints.get_user_point_balance(user)
        context['points_balance'] = points_balance
        
        # Get user's current tier
        current_tier = RewardTier.objects.filter(min_points__lte=points_balance)\
                                      .order_by('-min_points').first()
        context['current_tier'] = current_tier
        
        # Find next tier if there is one
        next_tier = None
        if current_tier:
            next_tier = RewardTier.objects.filter(min_points__gt=current_tier.min_points)\
                                         .order_by('min_points').first()
        context['next_tier'] = next_tier
        
        # Calculate progress to next tier
        if next_tier and current_tier:
            points_to_next_tier = next_tier.min_points - points_balance
            progress_percentage = min(100, max(0, 
                ((points_balance - current_tier.min_points) / 
                 (next_tier.min_points - current_tier.min_points)) * 100
            ))
            context['points_to_next_tier'] = points_to_next_tier
            context['progress_percentage'] = progress_percentage
        
        # Get recent point activities (last 10)
        recent_activities = RewardPoints.objects.filter(user=user)\
                                             .order_by('-created_at')[:10]
        context['recent_activities'] = recent_activities
        
        # Get recent redemptions
        recent_redemptions = RewardRedemption.objects.filter(user=user)\
                                                 .order_by('-created_at')[:5]
        context['recent_redemptions'] = recent_redemptions
        
        # Available redemption options section
        # This section dynamically generates a list of redemption options based on the user's
        # current point balance. Only options that the user has enough points for are shown.
        # Each redemption option includes:
        # - type: The RewardRedemptionType enum value (COUPON, TRAVEL_CREDIT, etc.)
        # - name: User-friendly name of the redemption option
        # - points: Number of points required for this redemption
        # - value: The monetary or percentage value of the redemption
        # - icon: Font Awesome icon name for visual representation
        # - color: Tailwind CSS color class from the indigo/violet palette for consistent styling
        available_redemptions = []
        
        # Only show redemption options if the user has a tier (which they should always have,
        # but this is a safety check)
        if current_tier:
            # In a production environment, these options would typically be stored in the database
            # and retrieved dynamically, possibly with tier-specific options or user personalization.
            # For now, they're hardcoded with progressive point requirements.
            
            # 10% Discount Coupon - Entry level reward (500 points)
            # Uses indigo-500 from our color palette for visual consistency
            if points_balance >= 500:
                available_redemptions.append({
                    'type': RewardRedemptionType.COUPON,
                    'name': '10% Discount Coupon',
                    'points': 500,
                    'value': 10,
                    'icon': 'tag',  # Font Awesome icon
                    'color': 'indigo-500'  # Tailwind CSS color class
                })
            
            # 25% Discount Coupon - Mid-tier reward (1000 points)
            # Uses indigo-600 (slightly darker) to visually indicate higher value
            if points_balance >= 1000:
                available_redemptions.append({
                    'type': RewardRedemptionType.COUPON,
                    'name': '25% Discount Coupon',
                    'points': 1000,
                    'value': 25,
                    'icon': 'tag',
                    'color': 'indigo-600'  # Darker indigo for higher value
                })
            
            # $50 Travel Credit - High-tier reward (2500 points)
            # Transitions to violet-500 color to indicate premium reward
            if points_balance >= 2500:
                available_redemptions.append({
                    'type': RewardRedemptionType.TRAVEL_CREDIT,
                    'name': '$50 Travel Credit',
                    'points': 2500,
                    'value': 50,
                    'icon': 'credit-card',  # Different icon for different reward type
                    'color': 'violet-500'  # Shifting to violet palette for premium rewards
                })
            
            # $100 Cash Transfer - Premium reward (5000 points)
            # Uses violet-600 (darkest in our palette) to indicate highest value
            if points_balance >= 5000:
                available_redemptions.append({
                    'type': RewardRedemptionType.CASH_TRANSFER,
                    'name': '$100 Cash Transfer',
                    'points': 5000,
                    'value': 100,
                    'icon': 'cash',  # Cash-specific icon
                    'color': 'violet-600'  # Darkest violet for highest value reward
                })
        
        context['available_redemptions'] = available_redemptions
        
        return context


class PointsHistoryView(LoginRequiredMixin, ListView):
    """
    Detailed history of user's point activities.
    
    This view lists all point-earning and point-spending activities 
    for the user with filters and pagination. It provides a comprehensive
    transaction history showing how points were earned and spent over time.
    
    The view supports filtering by:
    - Activity type (e.g., REVIEW, BOOKING, REDEMPTION)
    - Date range (start_date and end_date)
    
    Results are paginated for better performance and user experience, with
    the most recent activities shown first. Each activity displays:
    - Date and time of the transaction
    - Number of points earned or spent
    - Activity type and description
    - Reference to related objects (e.g., booking ID, review ID)
    - Expiration date if applicable
    
    The view uses LoginRequiredMixin to ensure only authenticated users
    can access their own point history, maintaining data privacy and security.
    
    The UI follows the TravelGuide platform's indigo/violet color scheme,
    with appropriate styling for positive (earning) and negative (spending)
    point transactions.
    """
    model = RewardPoints
    template_name = 'rewards/points_history.html'
    context_object_name = 'activities'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Filter points history to only show the current user's activities.
        
        This method applies filtering based on query parameters and
        ensures users only see their own point activities.
        
        Returns:
            QuerySet: Filtered queryset of the user's point activities
        """
        queryset = RewardPoints.objects.filter(user=self.request.user)
        
        # Handle filtering
        activity_type = self.request.GET.get('activity')
        if activity_type:
            queryset = queryset.filter(activity=activity_type)
            
        # Handle date range filtering
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        # Sort by date, newest first
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context for the points history page.
        
        This method enhances the template context with several important pieces of data:
        1. The user's current point balance for display in the header
        2. A list of unique activity types for the filter dropdown
        3. The currently selected filter values to maintain state between requests
        
        The method ensures that users have all the necessary information to understand
        their point history and effectively use the filtering functionality. The filters
        help users find specific transactions in potentially lengthy history lists.
        
        The context follows the TravelGuide platform's indigo/violet color scheme for
        consistent styling of UI elements like filter buttons and point balance displays.
        
        Args:
            **kwargs: Additional keyword arguments from the URL
            
        Returns:
            dict: Context dictionary for the template with points balance, activity choices,
                  and selected filter values
        """
        # Get the base context from the parent class
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add current points balance to the context
        # This allows the template to display the user's current available points
        # which is important context when viewing point history
        context['points_balance'] = RewardPoints.get_user_point_balance(user)
        
        # Add activity choices for the filter dropdown
        # This query gets all unique activity types that exist in the user's history
        # Using values_list with flat=True returns a simple list of values rather than tuples
        # The distinct() method ensures we only get each activity type once
        context['activity_choices'] = RewardPoints.objects.filter(user=user)\
                                                    .values_list('activity', flat=True)\
                                                    .distinct()
        
        # Add selected filters to context for form persistence
        # This ensures that when the page reloads after filtering, the selected
        # filter values remain in the form fields instead of resetting
        # Empty string defaults ensure the template doesn't show 'None' in the inputs
        context['selected_activity'] = self.request.GET.get('activity', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        
        return context


class RedemptionHistoryView(LoginRequiredMixin, ListView):
    """
    History of user's redemptions.
    
    This view shows all the rewards the user has redeemed,
    their status, and redemption details. It provides a comprehensive
    history of all point redemption requests and their current status.
    
    The view displays redemptions with the following information:
    - Date and time of the redemption request
    - Type of redemption (e.g., COUPON, TRAVEL_CREDIT, CASH_TRANSFER)
    - Number of points used
    - Monetary or percentage value of the redemption
    - Current status (PENDING, PROCESSING, COMPLETED, CANCELLED)
    - Redemption code (if applicable)
    - Expiration date (if applicable)
    
    Results are paginated for better performance and user experience, with
    the most recent redemptions shown first. The view uses LoginRequiredMixin
    to ensure only authenticated users can access their own redemption history,
    maintaining data privacy and security.
    
    The UI follows the TravelGuide platform's indigo/violet color scheme,
    with appropriate status indicators using color coding:
    - Pending: indigo-400 (lighter indigo)
    - Processing: indigo-600 (darker indigo)
    - Completed: violet-600 (darker violet)
    - Cancelled: gray-500 (neutral gray)
    """
    model = RewardRedemption
    template_name = 'rewards/redemption_history.html'
    context_object_name = 'redemptions'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Filter redemptions to only show the current user's data.
        
        This method ensures users only see their own redemption history.
        
        Returns:
            QuerySet: Filtered queryset of the user's redemptions
        """
        return RewardRedemption.objects.filter(user=self.request.user).order_by('-created_at')


class RedeemPointsView(LoginRequiredMixin, CreateView):
    """
    View for users to redeem their points for rewards.
    
    This view handles the redemption form submission and creation of redemption records.
    It provides a user interface for selecting redemption options, confirming point
    expenditure, and submitting redemption requests. The view implements several key
    features:
    
    1. Point balance validation - Ensures users have sufficient points for redemption
    2. Redemption option selection - Presents users with available reward options
    3. Custom form handling - Processes form submission with user-specific context
    4. Point deduction - Automatically deducts points upon successful redemption
    5. Success/failure messaging - Provides feedback on redemption status
    
    The view uses LoginRequiredMixin to ensure only authenticated users can redeem points,
    maintaining security and preventing unauthorized redemptions. It integrates with the
    RedemptionForm for data validation and the RewardRedemption model for data storage.
    
    The UI follows the TravelGuide platform's indigo/violet color scheme with consistent
    styling for form elements, buttons, and status messages. Available redemption options
    are visually distinguished based on the user's current point balance.
    """
    model = RewardRedemption
    form_class = RedemptionForm
    template_name = 'rewards/redeem_points.html'
    success_url = reverse_lazy('rewards:redemption_success')
    
    def get_form_kwargs(self):
        """
        Pass the current user to the form for context-aware validation.
        
        This method extends the default form keyword arguments by adding the current
        authenticated user object. This is essential for the form to access user-specific
        data such as:
        
        1. Current point balance - To validate if the user has sufficient points
        2. User tier information - To determine eligible redemption options
        3. User preferences - For potential personalized redemption suggestions
        
        The form uses this information to dynamically adjust available options and
        perform user-specific validation rules. This ensures users cannot redeem
        points they don't have or access tier-restricted rewards.
        
        Returns:
            dict: Enhanced keyword arguments dictionary containing the user object
                  along with the standard form kwargs
        """
        # Get the default keyword arguments from the parent class
        kwargs = super().get_form_kwargs()
        
        # Add the current user to the kwargs dictionary
        # This makes the user object available to the form's __init__ method
        kwargs['user'] = self.request.user
        
        return kwargs
    
    def form_valid(self, form):
        """
        Process the redemption if the form is valid and create the redemption record.
        
        This method is called when form validation succeeds and handles the actual
        redemption process. It performs several critical operations:
        
        1. Extracts validated form data (redemption type, points, value)
        2. Calls the RewardRedemption.create_redemption method which:
           - Creates a new redemption record in PENDING status
           - Deducts points from the user's balance
           - Generates a unique redemption code if applicable
           - Sets appropriate expiration dates
        3. Handles success/failure scenarios with appropriate user feedback
        4. Sets the created object for the CreateView parent class
        
        The method includes error handling for insufficient points or other failures,
        providing clear feedback to users through Django's messaging framework.
        The expiry_days parameter (90 days) defines how long the redemption remains
        valid before expiring.
        
        Args:
            form: The validated RedemptionForm instance containing cleaned data
            
        Returns:
            HttpResponse: Redirect to success page on successful redemption,
                         or back to form with error messages on failure
        """
        # Extract the validated data from the form
        redemption_type = form.cleaned_data['redemption_type']
        points = form.cleaned_data['points_used']
        value = form.cleaned_data['redemption_value']
        
        # Create redemption and deduct points using the model's helper method
        # This method handles the transaction atomically to ensure data consistency
        # The expiry_days parameter sets how long the redemption remains valid
        redemption, success = RewardRedemption.create_redemption(
            user=self.request.user,
            points=points,
            redemption_type=redemption_type,
            redemption_value=value,
            expiry_days=90  # Redemptions valid for 90 days
        )
        
        # Handle redemption failure (typically insufficient points)
        if not success:
            # Add error message to the Django messages framework
            # This will be displayed to the user on the form page
            messages.error(self.request, "Redemption failed. You may not have enough points.")
            return self.form_invalid(form)  # Return to form with errors
            
        # Set the created redemption as the object for CreateView
        # This is required by Django's CreateView to function properly
        self.object = redemption
        
        # Add success message to be displayed on the success page
        # Uses f-string to include the number of points redeemed
        messages.success(self.request, f"Successfully redeemed {points} points!")
        
        # Call the parent class's form_valid method to handle the redirect
        # This will redirect to the success_url defined in the view
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context for the redemption form template.
        
        This method enhances the template context with user-specific data needed
        to render the redemption form page. It provides several key pieces of information:
        
        1. User's current point balance - To display available points
        2. User's current reward tier - To show tier-specific benefits or options
        3. Available redemption options - Dynamically generated based on point balance
        
        Each redemption option includes:
        - type: The RewardRedemptionType enum value (COUPON, TRAVEL_CREDIT, etc.)
        - name: User-friendly name of the redemption option
        - points: Number of points required for this redemption
        - value: The monetary or percentage value of the redemption
        - available: Boolean indicating if the user has enough points for this option
        
        The context follows the TravelGuide platform's indigo/violet color scheme for
        consistent styling of UI elements. Options that the user cannot afford are
        visually distinguished (grayed out) but still shown to motivate point accumulation.
        
        Args:
            **kwargs: Additional keyword arguments from the URL
            
        Returns:
            dict: Enhanced context dictionary for the template with user-specific
                  redemption data and available options
        """
        # Get the base context from the parent class
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add current points balance to the context
        # This is retrieved using the model's helper method which calculates
        # the sum of all point transactions (both earned and spent)
        points_balance = RewardPoints.get_user_point_balance(user)
        context['points_balance'] = points_balance
        
        # Get user's current tier based on their point balance
        # This query finds the highest tier that the user qualifies for
        # by filtering tiers where min_points is less than or equal to the user's balance
        # and ordering by min_points descending to get the highest applicable tier
        current_tier = RewardTier.objects.filter(min_points__lte=points_balance)\
                                      .order_by('-min_points').first()
        context['current_tier'] = current_tier
        
        # Define preset redemption options with availability flags
        # In a production environment, these would typically be stored in the database
        # and retrieved dynamically, possibly with tier-specific options
        # Each option includes an 'available' flag based on the user's point balance
        redemption_options = [
            # 10% Discount Coupon - Entry level reward (500 points)
            # Uses indigo-500 from our color palette for visual consistency
            {
                'type': RewardRedemptionType.COUPON,
                'name': '10% Discount Coupon',
                'points': 500,
                'value': 10,
                'available': points_balance >= 500  # Boolean flag for template rendering
            },
            # 25% Discount Coupon - Mid-tier reward (1000 points)
            # Uses indigo-600 (slightly darker) to visually indicate higher value
            {
                'type': RewardRedemptionType.COUPON,
                'name': '25% Discount Coupon',
                'points': 1000,
                'value': 25,
                'available': points_balance >= 1000
            },
            # $50 Travel Credit - High-tier reward (2500 points)
            # Transitions to violet-500 color to indicate premium reward
            {
                'type': RewardRedemptionType.TRAVEL_CREDIT,
                'name': '$50 Travel Credit',
                'points': 2500,
                'value': 50,
                'available': points_balance >= 2500
            },
            # $100 Cash Transfer - Premium reward (5000 points)
            # Uses violet-600 (darkest in our palette) to indicate highest value
            {
                'type': RewardRedemptionType.CASH_TRANSFER,
                'name': '$100 Cash Transfer',
                'points': 5000,
                'value': 100,
                'available': points_balance >= 5000
            },
        ]
        
        # Add the redemption options to the context for the template
        context['redemption_options'] = redemption_options
        return context


@login_required
def redemption_success(request):
    """
    Success page after a successful redemption of reward points.
    
    This function-based view handles the confirmation page displayed to users
    after they have successfully redeemed their points for a reward. It provides
    a positive user experience by showing:
    
    1. Confirmation of the successful redemption
    2. Details of what was redeemed (type, value, points spent)
    3. The user's updated point balance after the redemption
    4. Next steps or instructions for using the redeemed reward
    5. Estimated processing time for the redemption
    
    The view is protected by the @login_required decorator to ensure only
    authenticated users can access it. It automatically retrieves the user's
    most recent redemption to display, assuming they've just completed the
    redemption process.
    
    The UI follows the TravelGuide platform's indigo/violet color scheme with
    appropriate success messaging and visual confirmation using checkmarks or
    success icons styled in the violet-600 color.
    
    Args:
        request: The HTTP request object containing user session information
        
    Returns:
        HttpResponse: Rendered redemption success page with redemption details
                     and updated point balance
    """
    # Get the user's most recent redemption
    # This query filters redemptions to only show the current user's data,
    # then orders by creation date (newest first) and takes the first result
    # This assumes the user has just completed a redemption and wants to see those details
    latest_redemption = RewardRedemption.objects.filter(user=request.user)\
                                              .order_by('-created_at').first()
    
    # Render the success template with the redemption details and updated point balance
    # The updated point balance is important to show the user their new balance
    # after the points have been deducted for this redemption
    return render(request, 'rewards/redemption_success.html', {
        'redemption': latest_redemption,  # The redemption object with all details
        'points_balance': RewardPoints.get_user_point_balance(request.user)  # Updated balance
    })


@login_required
def redemption_detail(request, redemption_id):
    """
    Detailed view of a specific redemption with complete information.
    
    This function-based view displays comprehensive details about a specific
    redemption request. It provides users with complete information about their
    redemption including:
    
    1. Current status (PENDING, PROCESSING, COMPLETED, CANCELLED)
    2. Redemption code or voucher details when applicable
    3. Date and time of the redemption request
    4. Expected processing time and completion date
    5. Points spent and monetary/percentage value received
    6. Expiration date of the redemption (if applicable)
    7. Instructions for using the redeemed reward
    8. Contact information for support if there are issues
    
    The view implements security by:
    1. Requiring authentication via @login_required decorator
    2. Ensuring users can only view their own redemptions by filtering on user
    3. Using get_object_or_404 to handle non-existent redemptions gracefully
    4. Using UUIDs rather than sequential IDs for redemption identification
    
    The UI follows the TravelGuide platform's indigo/violet color scheme with
    status-specific styling:
    - Pending: indigo-400 (lighter indigo)
    - Processing: indigo-600 (darker indigo)
    - Completed: violet-600 (darker violet)
    - Cancelled: gray-500 (neutral gray)
    
    Args:
        request: The HTTP request object containing user session information
        redemption_id: UUID of the specific redemption to display
        
    Returns:
        HttpResponse: Rendered redemption detail page with complete redemption information
        Http404: If the redemption doesn't exist or doesn't belong to the current user
    """
    # Get the specific redemption or return a 404 error if not found
    # This query ensures users can only view their own redemptions by including
    # the user filter along with the redemption ID
    # The get_object_or_404 helper provides a clean 404 response if not found
    redemption = get_object_or_404(
        RewardRedemption,  # The model to query
        id=redemption_id,  # The specific redemption UUID
        user=request.user  # Security: ensure user can only see their own redemptions
    )
    
    # Render the detail template with the redemption object
    # The template will have access to all fields of the redemption model
    # including status, points_used, redemption_type, redemption_value, etc.
    return render(request, 'rewards/redemption_detail.html', {
        'redemption': redemption  # The complete redemption object
    })


class TierBenefitsView(LoginRequiredMixin, ListView):
    """
    View showing all reward tiers and their benefits.
    
    This view displays information about all available tiers in the
    rewards program and what benefits they offer.
    """
    model = RewardTier
    template_name = 'rewards/tier_benefits.html'
    context_object_name = 'tiers'
    
    def get_queryset(self):
        """
        Get all reward tiers sorted by minimum points.
        
        Returns:
            QuerySet: All reward tiers in ascending order of points
        """
        return RewardTier.objects.all().order_by('min_points')
    
    def get_context_data(self, **kwargs):
        """
        Add the user's current tier to context.
        
        This method determines which tier the user is currently in
        to highlight it in the UI.
        
        Args:
            **kwargs: Additional keyword arguments from the URL
            
        Returns:
            dict: Context dictionary for the template
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's current tier
        points_balance = RewardPoints.get_user_point_balance(user)
        current_tier = RewardTier.objects.filter(min_points__lte=points_balance)\
                                      .order_by('-min_points').first()
        
        context['points_balance'] = points_balance
        context['current_tier'] = current_tier
        
        return context
