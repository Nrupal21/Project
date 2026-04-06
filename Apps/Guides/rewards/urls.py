"""
Rewards App URL Configuration.

This module defines URL patterns for the rewards app, mapping URL paths
to the appropriate views for the reward points system functionality.

The rewards app provides a comprehensive loyalty program where users can:
- View their current points balance and tier status
- See their point earning history and redemption history
- Redeem points for various rewards like discounts and travel credits
- View available reward tiers and associated benefits

All views in this app require user authentication via Django's LoginRequiredMixin.
The URL namespace 'rewards' is used for reverse URL lookups throughout the application.
"""

from django.urls import path
from . import views

# Define the application namespace for URL reversing
# This allows URLs to be referenced as 'rewards:view_name' in templates and views
app_name = 'rewards'

urlpatterns = [
    # Dashboard/home view showing points balance and recent activities
    # This is the main entry point for the rewards system
    # URL: /rewards/
    # View: RewardsHomeView (class-based view)
    # Template: rewards/rewards_home.html
    # Shows: Current points, tier progress, recent activities, and available rewards
    path('', views.RewardsHomeView.as_view(), name='dashboard'),
    
    # Detailed history of all point-earning activities with pagination
    # URL: /rewards/history/
    # View: PointsHistoryView (class-based view)
    # Template: rewards/points_history.html
    # Shows: Complete list of all point transactions with filters and sorting
    path('history/', views.PointsHistoryView.as_view(), name='points_history'),
    
    # History of all redemptions made by the user with pagination
    # URL: /rewards/redemptions/
    # View: RedemptionHistoryView (class-based view)
    # Template: rewards/redemption_history.html
    # Shows: All past redemptions with status tracking and details
    path('redemptions/', views.RedemptionHistoryView.as_view(), name='redemption_history'),
    
    # Form to redeem points for rewards
    # URL: /rewards/redeem/
    # View: RedeemPointsView (class-based view)
    # Template: rewards/redeem_points.html
    # Features: Point redemption form with preset options and custom redemption
    path('redeem/', views.RedeemPointsView.as_view(), name='redeem_points'),
    
    # Success page after redeeming points
    # URL: /rewards/redemption-success/
    # View: redemption_success (function-based view)
    # Template: rewards/redemption_success.html
    # Shows: Confirmation details and next steps after successful redemption
    path('redemption-success/', views.redemption_success, name='redemption_success'),
    
    # Detailed view of a specific redemption
    # URL: /rewards/redemption/<uuid>/
    # View: redemption_detail (function-based view)
    # Template: rewards/redemption_detail.html
    # Shows: Complete details of a single redemption including status and processing info
    # The UUID parameter ensures secure and unique identification of redemptions
    path('redemption/<uuid:redemption_id>/', views.redemption_detail, name='redemption_detail'),
    
    # View showing all reward tiers and their benefits
    # URL: /rewards/tiers/
    # View: TierBenefitsView (class-based view)
    # Template: rewards/tier_benefits.html
    # Shows: Comparison of all available tiers and their benefits
    # Highlights the user's current tier and progress to next tier
    path('tiers/', views.TierBenefitsView.as_view(), name='tier_benefits'),
]
