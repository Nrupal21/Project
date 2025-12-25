"""
Orders app views.
Handles order-related functionality and promo code management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import PromoCode, PromoCodeUsage, SeasonalPromotion
from .forms import PromoCodeForm, SeasonalPromotionForm, ApplyPromoCodeForm
from customer.cart import Cart


@login_required
def promo_code_list(request):
    """
    Display list of promo codes for the restaurant owner.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered promo code list page
    """
    # Get restaurant for the logged-in user
    restaurant = request.user.restaurants.first()
    if not restaurant:
        messages.error(request, 'You must be a restaurant owner to access this page.')
        return redirect('customer:home')
    
    # Get promo codes for this restaurant (plus global codes)
    promo_codes = PromoCode.objects.filter(
        Q(restaurant=restaurant) | Q(restaurant__isnull=True)
    ).order_by('-created_at')
    
    # Add usage statistics
    for promo in promo_codes:
        promo.usage_stats = {
            'total_used': promo.times_used,
            'remaining': promo.usage_limit - promo.times_used if promo.usage_limit else None,
            'is_expired': promo.end_date < timezone.now(),
            'is_active': promo.is_active and promo.start_date <= timezone.now() <= promo.end_date
        }
    
    context = {
        'promo_codes': promo_codes,
        'restaurant': restaurant,
        'page_title': 'Promo Codes'
    }
    
    return render(request, 'orders/promo_code_list.html', context)


@login_required
def create_promo_code(request):
    """
    Create a new promo code for the restaurant.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered promo code creation page
    """
    # Get restaurant for the logged-in user
    restaurant = request.user.restaurants.first()
    if not restaurant:
        messages.error(request, 'You must be a restaurant owner to access this page.')
        return redirect('customer:home')
    
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            promo_code = form.save(commit=False)
            promo_code.restaurant = restaurant
            promo_code.save()
            
            messages.success(request, f'Promo code "{promo_code.code}" created successfully!')
            return redirect('orders:promo_code_list')
    else:
        form = PromoCodeForm()
    
    context = {
        'form': form,
        'restaurant': restaurant,
        'page_title': 'Create Promo Code',
        'action': 'Create'
    }
    
    return render(request, 'orders/promo_code_form.html', context)


@login_required
def edit_promo_code(request, promo_code_id):
    """
    Edit an existing promo code.
    
    Args:
        request: Django HTTP request object
        promo_code_id: UUID of the promo code to edit
    
    Returns:
        HttpResponse: Rendered promo code edit page
    """
    # Get restaurant for the logged-in user
    restaurant = request.user.restaurants.first()
    if not restaurant:
        messages.error(request, 'You must be a restaurant owner to access this page.')
        return redirect('customer:home')
    
    promo_code = get_object_or_404(PromoCode, id=promo_code_id)
    
    # Check if user owns this promo code or it's global
    if promo_code.restaurant and promo_code.restaurant != restaurant:
        messages.error(request, 'You can only edit your own promo codes.')
        return redirect('orders:promo_code_list')
    
    if request.method == 'POST':
        form = PromoCodeForm(request.POST, instance=promo_code)
        if form.is_valid():
            form.save()
            messages.success(request, f'Promo code "{promo_code.code}" updated successfully!')
            return redirect('orders:promo_code_list')
    else:
        form = PromoCodeForm(instance=promo_code)
    
    context = {
        'form': form,
        'promo_code': promo_code,
        'restaurant': restaurant,
        'page_title': 'Edit Promo Code',
        'action': 'Edit'
    }
    
    return render(request, 'orders/promo_code_form.html', context)


@login_required
def delete_promo_code(request, promo_code_id):
    """
    Delete a promo code.
    
    Args:
        request: Django HTTP request object
        promo_code_id: UUID of the promo code to delete
    
    Returns:
        HttpResponse: Redirect to promo code list
    """
    # Get restaurant for the logged-in user
    restaurant = request.user.restaurants.first()
    if not restaurant:
        messages.error(request, 'You must be a restaurant owner to access this page.')
        return redirect('customer:home')
    
    promo_code = get_object_or_404(PromoCode, id=promo_code_id)
    
    # Check if user owns this promo code or it's global
    if promo_code.restaurant and promo_code.restaurant != restaurant:
        messages.error(request, 'You can only delete your own promo codes.')
        return redirect('orders:promo_code_list')
    
    # Don't allow deletion of promo codes that have been used
    if promo_code.times_used > 0:
        messages.error(request, 'Cannot delete promo codes that have been used.')
        return redirect('orders:promo_code_list')
    
    promo_code.delete()
    messages.success(request, f'Promo code "{promo_code.code}" deleted successfully!')
    
    return redirect('orders:promo_code_list')


@require_POST
def apply_promo_code(request):
    """
    Apply a promo code to the cart via AJAX.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        JsonResponse: Success/error response with updated cart totals
    """
    form = ApplyPromoCodeForm(request.POST)
    cart = Cart(request)
    
    if form.is_valid():
        code = form.cleaned_data['code']
        user = request.user if request.user.is_authenticated else None
        
        success, message = cart.apply_promo_code(code, user)
        
        if success:
            # Get updated cart totals
            breakdown = cart.get_discount_breakdown()
            
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_breakdown': {
                    'subtotal': str(breakdown['subtotal']),
                    'discount_amount': str(breakdown['discount_amount']),
                    'delivery_charge': str(breakdown['delivery_charge']),
                    'final_total': str(breakdown['final_total']),
                    'free_delivery': breakdown['free_delivery'],
                    'applied_promo_code': {
                        'code': breakdown['applied_promo_code'].code,
                        'name': breakdown['applied_promo_code'].name,
                        'discount_type': breakdown['applied_promo_code'].discount_type,
                        'discount_value': str(breakdown['applied_promo_code'].discount_value)
                    } if breakdown['applied_promo_code'] else None
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid promo code format.'
        })


@require_POST
def remove_promo_code(request):
    """
    Remove applied promo code from cart via AJAX.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        JsonResponse: Success response with updated cart totals
    """
    cart = Cart(request)
    cart.remove_promo_code()
    
    # Get updated cart totals
    breakdown = cart.get_discount_breakdown()
    
    return JsonResponse({
        'success': True,
        'message': 'Promo code removed successfully.',
        'cart_breakdown': {
            'subtotal': str(breakdown['subtotal']),
            'discount_amount': str(breakdown['discount_amount']),
            'delivery_charge': str(breakdown['delivery_charge']),
            'final_total': str(breakdown['final_total']),
            'free_delivery': breakdown['free_delivery'],
            'applied_promo_code': None
        }
    })


@login_required
def seasonal_promotion_list(request):
    """
    Display list of seasonal promotions for admin users or restaurant owners.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered seasonal promotion list page
    """
    # Check if user is admin or restaurant owner
    if request.user.is_staff:
        # Admin can see all promotions
        promotions = SeasonalPromotion.objects.all().order_by('-created_at')
    else:
        # Restaurant owner can only see their own promotions
        try:
            from restaurant.models import Restaurant
            user_restaurant = Restaurant.objects.get(owner=request.user)
            promotions = SeasonalPromotion.objects.filter(
                restaurants=user_restaurant
            ).order_by('-created_at')
        except Restaurant.DoesNotExist:
            messages.error(request, 'You are not associated with any restaurant.')
            return redirect('customer:home')
    
    # Add status information
    now = timezone.now()
    active_campaigns = 0
    upcoming_campaigns = 0
    total_codes_generated = 0
    
    for promotion in promotions:
        promotion.is_current = promotion.start_date <= now <= promotion.end_date
        promotion.days_until_start = (promotion.start_date - now).days if promotion.start_date > now else None
        promotion.days_until_end = (promotion.end_date - now).days if promotion.end_date > now else None
        
        if promotion.is_current:
            active_campaigns += 1
        elif promotion.start_date > now:
            upcoming_campaigns += 1
            
        # Count generated promo codes for this promotion
        total_codes_generated += PromoCode.objects.filter(
            code__startswith=promotion.code_prefix
        ).count()
    
    context = {
        'promotions': promotions,
        'active_campaigns': active_campaigns,
        'upcoming_campaigns': upcoming_campaigns,
        'total_codes_generated': total_codes_generated,
        'page_title': 'Seasonal Promotions'
    }
    
    return render(request, 'orders/seasonal_promotion_list.html', context)


@login_required
def create_seasonal_promotion(request):
    """
    Create a new seasonal promotion (for admin users or restaurant owners).
    
    Args:
        request: Django HTTP request object
    
    Returns:
        HttpResponse: Rendered seasonal promotion creation page
    """
    # Check if user is admin or restaurant owner
    if not request.user.is_staff:
        # Restaurant owner validation
        try:
            from restaurant.models import Restaurant
            user_restaurant = Restaurant.objects.get(owner=request.user)
        except Restaurant.DoesNotExist:
            messages.error(request, 'You are not associated with any restaurant.')
            return redirect('customer:home')
    
    if request.method == 'POST':
        form = SeasonalPromotionForm(request.POST, user=request.user)
        if form.is_valid():
            promotion = form.save()
            
            # For restaurant owners, ensure the promotion is associated with their restaurant
            if not request.user.is_staff:
                promotion.restaurants.add(user_restaurant)
            
            # Generate promo codes if auto_generate is enabled
            if hasattr(promotion, 'auto_generate_codes'):
                codes = promotion.generate_promo_codes()
                messages.success(request, f'Seasonal promotion created with {len(codes)} promo codes!')
            else:
                messages.success(request, 'Seasonal promotion created successfully!')
            
            return redirect('orders:seasonal_promotion_list')
    else:
        form = SeasonalPromotionForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Create Seasonal Promotion',
        'action': 'Create'
    }
    
    return render(request, 'orders/seasonal_promotion_form.html', context)
