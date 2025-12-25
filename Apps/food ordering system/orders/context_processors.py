"""
Context processors for orders app.
Provides global context for flash sales and seasonal promotions.
"""
from django.utils import timezone
from .models import SeasonalPromotion


def flash_sales_context(request):
    """
    Add active flash sales and seasonal promotions to global context.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        dict: Context dictionary with active campaigns
    """
    now = timezone.now()
    
    # Get currently active campaigns with optimized queries
    active_campaigns = SeasonalPromotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).prefetch_related('promo_codes', 'restaurants').order_by('-created_at')
    
    # Filter campaigns that should show as flash sales
    flash_sales = active_campaigns.filter(
        promotion_type__in=['flash_sale', 'seasonal']
    )
    
    # Add time remaining for each campaign
    for campaign in flash_sales:
        campaign.time_remaining = campaign.end_date - now
        campaign.hours_remaining = int(campaign.time_remaining.total_seconds() / 3600)
        campaign.minutes_remaining = int((campaign.time_remaining.total_seconds() % 3600) / 60)
        campaign.seconds_remaining = int(campaign.time_remaining.total_seconds() % 60)
    
    return {
        'active_flash_sales': flash_sales,
        'has_flash_sales': flash_sales.exists(),
    }
