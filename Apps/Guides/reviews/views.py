"""
Views for the reviews application.

This module defines view functions and classes for handling
review-related HTTP requests, including creating, updating,
viewing, and moderating reviews.

Includes both class-based views and function-based views
with proper authentication and permission handling.

All templates use the indigo/violet color scheme and are
fully responsive for mobile and desktop viewing.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.edit import FormMixin
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from .models import Review, ReviewImage, ReviewComment, ReviewHelpful
from .forms import ReviewForm, ReviewImageFormSet, ReviewCommentForm, ReviewFilterForm
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class ReviewListView(ListView):
    """
    Display a list of approved reviews.
    
    Shows paginated reviews that have been approved by moderators,
    with optional filtering by entity type and ID.
    
    Attributes:
        model: The model to list
        template_name: The template to render
        context_object_name: The name of the context variable containing the reviews
        paginate_by: Number of reviews per page
    """
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the list of approved reviews with optional filtering.
        
        Filters by content type and object ID if provided in the request.
        Applies additional filters based on the filter form.
        
        Returns:
            QuerySet: Filtered queryset of reviews
        """
        # Start with all approved reviews
        queryset = Review.objects.filter(status='approved')
        
        # Filter by content type and object ID if provided
        content_type_id = self.request.GET.get('content_type_id')
        object_id = self.request.GET.get('object_id')
        
        if content_type_id and object_id:
            queryset = queryset.filter(
                content_type_id=content_type_id,
                object_id=object_id
            )
        
        # Apply filters from filter form if provided
        filter_form = ReviewFilterForm(self.request.GET)
        if filter_form.is_valid():
            # Filter by rating
            ratings = filter_form.cleaned_data.get('rating')
            if ratings:
                queryset = queryset.filter(rating__in=ratings)
            
            # Filter by date range
            date_range = filter_form.cleaned_data.get('date_range')
            if date_range:
                today = timezone.now().date()
                if date_range == 'week':
                    start_date = today - timedelta(days=7)
                elif date_range == 'month':
                    start_date = today - timedelta(days=30)
                elif date_range == 'year':
                    start_date = today - timedelta(days=365)
                
                queryset = queryset.filter(created_at__date__gte=start_date)
            
            # Apply sorting
            sort_by = filter_form.cleaned_data.get('sort_by')
            if sort_by == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort_by == 'oldest':
                queryset = queryset.order_by('created_at')
            elif sort_by == 'highest':
                queryset = queryset.order_by('-rating')
            elif sort_by == 'lowest':
                queryset = queryset.order_by('rating')
            elif sort_by == 'helpful':
                queryset = queryset.annotate(
                    helpful_count=Count('helpful_votes')
                ).order_by('-helpful_count')
        else:
            # Default sorting by created_at
            queryset = queryset.order_by('-created_at')
            
        return queryset.select_related('user', 'content_type')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds filter form and content object details to context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added review data
        """
        context = super().get_context_data(**kwargs)
        
        # Add filter form to context
        context['filter_form'] = ReviewFilterForm(self.request.GET)
        
        # Add content object details if filtering by content type and object ID
        content_type_id = self.request.GET.get('content_type_id')
        object_id = self.request.GET.get('object_id')
        
        if content_type_id and object_id:
            try:
                content_type = ContentType.objects.get(id=content_type_id)
                context['content_object'] = content_type.get_object_for_this_type(id=object_id)
                context['content_type'] = content_type
            except (ContentType.DoesNotExist, AttributeError):
                pass
                
        # Add review stats
        if context.get('content_object'):
            reviews = self.get_queryset()
            context['avg_rating'] = reviews.aggregate(Avg('rating'))['rating__avg']
            context['review_count'] = reviews.count()
            context['rating_counts'] = {
                rating: reviews.filter(rating=rating).count()
                for rating in range(1, 6)
            }
            
        return context


class ReviewDetailView(DetailView):
    """
    Display details of a single review.
    
    Shows the full review content, images, and comments.
    
    Attributes:
        model: The model to display
        template_name: The template to render
        context_object_name: The name of the context variable containing the review
        pk_url_kwarg: The name of the URL keyword argument containing the review ID
    """
    model = Review
    template_name = 'reviews/review_detail.html'
    context_object_name = 'review'
    pk_url_kwarg = 'review_id'
    
    def get_queryset(self):
        """
        Get the review queryset.
        
        For non-staff users, only approved reviews or their own reviews
        are visible.
        
        Returns:
            QuerySet: Filtered queryset of reviews
        """
        queryset = Review.objects.select_related('user', 'content_type')
        
        # For non-staff users, only show approved reviews or their own reviews
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='approved') | Q(user=self.request.user)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds comments, helpful votes, and comment form to context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added review data
        """
        context = super().get_context_data(**kwargs)
        review = self.get_object()
        
        # Add comments to context
        comments = review.comments.select_related('user').order_by('created_at')
        context['comments'] = comments
        
        # Check if user has already voted this review as helpful
        if self.request.user.is_authenticated:
            context['user_voted_helpful'] = review.helpful_records.filter(
                user=self.request.user
            ).exists()
            
        # Add comment form to context
        context['comment_form'] = ReviewCommentForm(user=self.request.user)
        
        return context


@login_required
def create_review(request, content_type_id=None, object_id=None):
    """
    Handle the creation of a new review.
    
    Displays a form for creating a review and processes
    form submission. Handles both the review text/rating
    and any uploaded images.
    
    Args:
        request: The HTTP request object
        content_type_id: ID of the content type being reviewed
        object_id: ID of the specific object being reviewed
        
    Returns:
        HttpResponse: Rendered form or redirect after submission
    """
    # Get content type and object being reviewed
    content_type = get_object_or_404(ContentType, id=content_type_id)
    content_object = get_object_or_404(
        content_type.model_class(), 
        id=object_id
    )
    
    # Check if user has already reviewed this object
    existing_review = Review.objects.filter(
        user=request.user,
        content_type=content_type,
        object_id=object_id
    ).first()
    
    if existing_review:
        messages.warning(
            request, 
            _('You have already reviewed this. You can edit your existing review.')
        )
        return redirect('reviews_new:edit_review', review_id=existing_review.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        # Initialize formset with POST and FILES data
        image_formset = ReviewImageFormSet(
            request.POST,
            request.FILES,
            queryset=ReviewImage.objects.none()  # No existing images for new review
        )
        
        if form.is_valid() and image_formset.is_valid():
            try:
                # Start transaction to ensure data consistency
                with transaction.atomic():
                    # Save review
                    review = form.save(commit=False)
                    review.user = request.user
                    review.content_type = content_type
                    review.object_id = object_id
                    review.status = 'pending'  # All reviews require approval
                    review.save()
                    
                    # Save images
                    image_formset.instance = review
                    images = image_formset.save(commit=False)
                    
                    # Set the review for each image and save
                    for image in images:
                        image.review = review
                        image.save()
                    
                    # Delete any images marked for deletion
                    for obj in image_formset.deleted_objects:
                        obj.delete()
                
                # Send email notification (outside transaction)
                try:
                    from .utils import send_review_submission_email
                    send_review_submission_email(
                        user=request.user,
                        review=review,
                        content_object=content_object,
                        request=request
                    )
                except Exception as e:
                    # Log email error but don't fail the request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send review submission email: {str(e)}")
                
                # Redirect to the success page with the destination URL
                success_url = reverse('reviews:review_success')
                destination_url = request.META.get('HTTP_REFERER', reverse('core:home'))
                return redirect(f"{success_url}?destination={destination_url}")
                
            except Exception as e:
                # Log the error and show message to user
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving review: {str(e)}")
                messages.error(
                    request,
                    _('An error occurred while saving your review. Please try again.')
                )
    else:
        # Initialize empty form and formset for GET request
        form = ReviewForm(initial={
            'content_type': content_type_id,
            'object_id': object_id
        })
        image_formset = ReviewImageFormSet(queryset=ReviewImage.objects.none())
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'content_object': content_object,
        'content_type_id': content_type_id,
        'object_id': object_id,
    }
    
    return render(request, 'reviews/create_review.html', context)


@login_required
def edit_review(request, review_id):
    """
    Handle editing of an existing review.
    
    Allows users to edit their own reviews, or staff to edit any review.
    Handles both the review text/rating and any uploaded images.
    
    Args:
        request: The HTTP request object
        review_id: ID of the review to edit
        
    Returns:
        HttpResponse: Rendered form or redirect after submission
    """
    review = get_object_or_404(Review, id=review_id)
    
    # Check permissions - only the author or staff can edit
    if review.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden(_('You do not have permission to edit this review.'))
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        image_formset = ReviewImageFormSet(request.POST, request.FILES, instance=review)
        
        if form.is_valid() and image_formset.is_valid():
            # Save review
            review = form.save()
            # If user is not staff, review goes back to pending status
            if not request.user.is_staff:
                review.status = 'pending'
                review.save()
            
            # Save images
            image_formset.save()
            
            messages.success(
                request, 
                _('Your review has been updated successfully.')
            )
            
            # Redirect to the review detail page
            return redirect('reviews_new:review_detail', review_id=review.id)
    else:
        form = ReviewForm(instance=review)
        image_formset = ReviewImageFormSet(instance=review)
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'review': review,
    }
    
    return render(request, 'reviews/edit_review.html', context)


@login_required
@require_POST
def add_review_comment(request, review_id):
    """
    Handle adding a comment to a review.
    
    Processes form submission for adding comments to reviews.
    
    Args:
        request: The HTTP request object
        review_id: ID of the review to comment on
        
    Returns:
        HttpResponse: Redirect to review detail
    """
    review = get_object_or_404(Review, id=review_id)
    
    # Only allow comments on approved reviews
    if review.status != 'approved' and not request.user.is_staff:
        messages.error(
            request, 
            _('You can only comment on approved reviews.')
        )
        return redirect('reviews_new:review_list')
    
    form = ReviewCommentForm(request.POST, user=request.user)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.review = review
        comment.user = request.user
        
        # If user is staff and selected official response
        if request.user.is_staff and form.cleaned_data.get('is_official_response'):
            comment.is_official_response = True
            
        comment.save()
        
        messages.success(
            request, 
            _('Your comment has been added.')
        )
    else:
        messages.error(
            request, 
            _('There was an error with your comment. Please check and try again.')
        )
    
    return redirect('reviews_new:review_detail', review_id=review.id)


@login_required
@require_http_methods(["POST"])
def approve_comment(request, comment_id):
    """
    Approve a comment for public display.
    
    Args:
        request: The HTTP request object
        comment_id: ID of the comment to approve
        
    Returns:
        HttpResponse: Redirect to moderation page or review detail
    """
    comment = get_object_or_404(ReviewComment, id=comment_id)
    
    # Check if user has permission to moderate comments
    if not request.user.has_perm('reviews.moderate_comment'):
        messages.error(request, _('You do not have permission to moderate comments.'))
        return redirect('reviews:review_detail', review_id=comment.review.id)
    
    # Approve the comment
    comment.is_approved = True
    comment.save()
    
    messages.success(request, _('Comment has been approved.'))
    
    # Redirect back to moderation if from moderation, otherwise to review
    if 'moderation' in request.META.get('HTTP_REFERER', ''):
        return redirect('reviews:comment_moderation')
    return redirect('reviews:review_detail', review_id=comment.review.id)


@login_required
@require_http_methods(["POST"])
def reject_comment(request, comment_id):
    """
    Reject a comment, marking it as not approved.
    
    Args:
        request: The HTTP request object
        comment_id: ID of the comment to reject
        
    Returns:
        HttpResponse: Redirect to moderation page or review detail
    """
    comment = get_object_or_404(ReviewComment, id=comment_id)
    
    # Check if user has permission to moderate comments
    if not request.user.has_perm('reviews.moderate_comment'):
        messages.error(request, _('You do not have permission to moderate comments.'))
        return redirect('reviews:review_detail', review_id=comment.review.id)
    
    # Reject the comment
    comment.is_approved = False
    comment.save()
    
    messages.success(request, _('Comment has been rejected.'))
    
    # Redirect back to moderation if from moderation, otherwise to review
    if 'moderation' in request.META.get('HTTP_REFERER', ''):
        return redirect('reviews:comment_moderation')
    return redirect('reviews:review_detail', review_id=comment.review.id)


@login_required
@require_http_methods(["POST"])
def delete_comment(request, comment_id):
    """
    Delete a comment.
    
    Args:
        request: The HTTP request object
        comment_id: ID of the comment to delete
        
    Returns:
        HttpResponse: Redirect to moderation page or review detail
    """
    comment = get_object_or_404(ReviewComment, id=comment_id)
    review_id = comment.review.id
    
    # Check if user has permission to delete (author, review author, or staff)
    can_delete = (
        comment.user == request.user or  # Comment author
        comment.review.user == request.user or  # Review author
        request.user.has_perm('reviews.delete_comment')  # Staff with permission
    )
    
    if not can_delete:
        messages.error(request, _('You do not have permission to delete this comment.'))
        return redirect('reviews:review_detail', review_id=review_id)
    
    # Delete the comment
    comment.delete()
    
    messages.success(request, _('Comment has been deleted.'))
    
    # Redirect back to moderation if from moderation, otherwise to review
    if 'moderation' in request.META.get('HTTP_REFERER', ''):
        return redirect('reviews:comment_moderation')
    return redirect('reviews:review_detail', review_id=review_id)


@login_required
@permission_required('reviews.moderate_comment')
def comment_moderation(request):
    """
    Display a list of comments awaiting moderation.
    
    Shows paginated comments that need moderation (unapproved or flagged).
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered moderation page
    """
    # Get unapproved comments, ordered by creation date (oldest first)
    unapproved_comments = ReviewComment.objects.filter(
        is_approved=False
    ).select_related('user', 'review').order_by('created_at')
    
    # Get recently flagged comments
    flagged_comments = ReviewComment.objects.filter(
        is_approved=True,
        flag_count__gt=0
    ).select_related('user', 'review').order_by('-flag_count', '-created_at')
    
    context = {
        'unapproved_comments': unapproved_comments,
        'flagged_comments': flagged_comments,
    }
    
    return render(request, 'reviews/comment_moderation.html', context)


@login_required
@require_POST
def vote_helpful(request, review_id):
    """
    Handle helpful votes on reviews.
    
    Processes AJAX requests to vote on the helpfulness of reviews.
    Toggles votes - removes if already voted, adds if not.
    
    Args:
        request: The HTTP request object
        review_id: ID of the review to vote on
        
    Returns:
        JsonResponse: JSON response with updated vote counts
    """
    review = get_object_or_404(Review, id=review_id)
    
    # Only allow helpful votes on approved reviews
    if review.status != 'approved':
        return JsonResponse({
            'success': False,
            'error': _('You can only vote on approved reviews.')
        })
    
    # Check if user has already voted
    helpful_vote, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    # If not created, then user already voted, so remove the vote
    if not created:
        helpful_vote.delete()
        voted = False
    else:
        voted = True
    
    # Return updated count
    helpful_count = review.helpful_count
    
    return JsonResponse({
        'success': True,
        'voted': voted,
        'count': helpful_count
    })


class MyReviewsView(LoginRequiredMixin, ListView):
    """
    View for displaying reviews created by the current user.
    
    This view shows a paginated list of all reviews created by the currently
    logged-in user, with options to filter by status.
    
    Attributes:
        model: The model to list
        template_name: The template to render
        context_object_name: The name of the context variable containing the reviews
        paginate_by: Number of reviews per page
    """
    model = Review
    template_name = 'reviews/my_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get the queryset of reviews created by the current user.
        
        Applies filtering based on the 'status' query parameter if provided.
        
        Returns:
            QuerySet: Filtered queryset of the user's reviews
        """
        queryset = Review.objects.filter(
            user=self.request.user
        ).select_related('content_type').order_by('-created_at')
        
        status_filter = self.request.GET.get('status', '').lower()
        if status_filter in ['pending', 'approved', 'rejected']:
            queryset = queryset.filter(status=status_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Adds status filter information to context.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: Context dictionary with added filter data
        """
        context = super().get_context_data(**kwargs)
        
        # Add status filter information
        status_filter = self.request.GET.get('status', 'all')
        context['status_filter'] = status_filter
        
        # Add counts for each status
        context['all_count'] = Review.objects.filter(user=self.request.user).count()
        context['approved_count'] = Review.objects.filter(
            user=self.request.user, 
            status='approved'
        ).count()
        context['pending_count'] = Review.objects.filter(
            user=self.request.user, 
            status='pending'
        ).count()
        context['rejected_count'] = Review.objects.filter(
            user=self.request.user, 
            status='rejected'
        ).count()
        
        return context


class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting a review.
    
    Allows users to delete their own reviews, or staff to delete any review.
    Uses Django's DeleteView for confirmation and deletion.
    """
    model = Review
    template_name = 'reviews/review_confirm_delete.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('reviews:my_reviews')
    
    def test_func(self):
        """
        Test if the user has permission to delete the review.
        
        Returns:
            bool: True if user is the author or staff, False otherwise
        """
        review = self.get_object()
        return review.user == self.request.user or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a review.
        
        Args:
            request: The HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            HttpResponse: Redirect to success URL with success message
        """
        review = self.get_object()
        success_url = self.get_success_url()
        
        # Store review details for message
        content_object = review.content_object
        
        # Delete the review
        review.delete()
        
        # Add success message
        messages.success(
            request,
            _('Your review has been deleted successfully.')
        )
        
        return HttpResponseRedirect(success_url)


@login_required
@permission_required('reviews.change_review')
def review_moderation(request):
    """
    Handle moderation of reviews.
    
    Displays a list of reviews that need moderation and
    provides actions for approving, rejecting, or featuring reviews.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered moderation page
    """
    # Filter reviews by status if provided
    status_filter = request.GET.get('status', 'pending')
    
    if status_filter == 'all':
        reviews = Review.objects.all()
    else:
        reviews = Review.objects.filter(status=status_filter)
    
    # Apply additional filters
    reviews = reviews.select_related('user', 'content_type').order_by('-created_at')
    
    context = {
        'reviews': reviews,
        'status_filter': status_filter,
        'status_choices': dict(STATUS_CHOICES),
    }
    
    return render(request, 'reviews/review_moderation.html', context)


@login_required
@permission_required('reviews.change_review')
@require_POST
def approve_review(request, review_id):
    """
    Approve a review for public display.
    
    Args:
        request: The HTTP request object
        review_id: ID of the review to approve
        
    Returns:
        HttpResponse: Redirect to moderation page
    """
    review = get_object_or_404(Review, id=review_id)
    review.status = 'approved'
    review.save()
    
    messages.success(
        request, 
        _('Review has been approved and is now publicly visible.')
    )
    
    return redirect('reviews:review_moderation')


@login_required
@permission_required('reviews.delete_review')
@require_POST
def reject_review(request, review_id):
    """
    Reject a review, marking it as rejected.
    
    Args:
        request: The HTTP request object
        review_id: ID of the review to reject
        
    Returns:
        HttpResponse: Redirect to moderation page
    """
    review = get_object_or_404(Review, id=review_id)
    review.status = 'rejected'
    review.save()
    
    messages.success(
        request, 
        _('Review has been rejected.')
    )
    
    return redirect('reviews:review_moderation')


@login_required
@permission_required('reviews.change_review')
@require_POST
def feature_review(request, review_id):
    """
    Feature or unfeature a review.
    
    This view toggles the featured status of a review. If the review is currently
    featured, it will be unfeatured, and vice versa. The view requires the user
    to have the 'reviews.change_review' permission.
    
    Args:
        request: The HTTP request object
        review_id: ID of the review to feature/unfeature
        
    Returns:
        HttpResponseRedirect: Redirects to the review moderation page with a success message
        
    Raises:
        Http404: If the review with the given ID does not exist
    """
    # Get the review or return 404 if not found
    review = get_object_or_404(Review, id=review_id)
    
    # Toggle the featured status
    review.featured = not review.featured
    review.save()
    
    # Set appropriate success message
    if review.featured:
        message = _('Review is now featured and will be highlighted.')
    else:
        message = _('Review is no longer featured.')
    
    # Add success message and redirect to moderation page
    messages.success(request, message, extra_tags='success')
    
    # Redirect back to the review moderation page
    return redirect('reviews:review_moderation')


class TestTemplateTagView(TemplateView):
    """
    Test view to verify template tag functionality.
    
    This view provides a simple test page to verify that custom template tags
    are being loaded and executed correctly. It's primarily used for development
    and debugging purposes.
    
    Attributes:
        template_name (str): The template to render
    """
    template_name = 'reviews/test_template_tag.html'
    
    def get_context_data(self, **kwargs):
        """
        Add test data to the template context.
        
        Returns:
            dict: Context dictionary with test data including sample ratings
            and a test key to verify template tag functionality.
        """
        context = super().get_context_data(**kwargs)
        # Add a test dictionary to verify the get_item filter
        context['test_data'] = {
            'test_key': 'Template tags are working!',
            'rating_5': 10,
            'rating_4': 5,
            'rating_3': 2,
            'rating_2': 1,
            'rating_1': 0,
        }
        return context


def test_template_tag_view(request):
    """
    Function-based test view for template tag verification.
    
    This is an alternative to the class-based view above, provided in case
    there are any issues with class-based views in the URL configuration.
    
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        HttpResponse: Rendered template with test data for verifying
        template tag functionality.
    """
    context = {
        'test_data': {
            'test_key': 'Template tags are working! (Function-based view)',
            'rating_5': 10,
            'rating_4': 5,
            'rating_3': 2,
            'rating_2': 1,
            'rating_1': 0,
        }
    }
    return render(request, 'reviews/test_template_tag.html', context)

