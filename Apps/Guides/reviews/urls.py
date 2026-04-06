from django.urls import path
from . import views
from .views import TestTemplateTagView, test_template_tag_view
from .views_success import ReviewSuccessView

"""
URL configuration for reviews app
Defines all URL patterns for the review system including:
- Review list views (general and per-object)
- Detail view for individual reviews
- Create, edit, and delete review functionality 
- Review moderation endpoints
- Review helpful voting
- Comment management
"""

app_name = 'reviews'

urlpatterns = [
    # Review listing views
    path('', views.ReviewListView.as_view(), name='review_list'),
    path('my-reviews/', views.MyReviewsView.as_view(), name='my_reviews'),
    path('moderation/', views.review_moderation, name='review_moderation'),
    
    # Object-specific reviews
    path('for/<str:content_type>/<int:object_id>/', 
         views.ReviewListView.as_view(), 
         name='object_review_list'),
    
    # Individual review management
    path('<int:review_id>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('create/<int:content_type_id>/<int:object_id>/', 
         views.create_review, 
         name='create_review'),
    path('<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete_review'),
    
    # Review moderation actions
    path('<int:review_id>/approve/', views.approve_review, name='approve_review'),
    path('<int:review_id>/reject/', views.reject_review, name='reject_review'),
    path('<int:review_id>/feature/', views.feature_review, name='feature_review'),
    
    # Review helpful voting
    # Helpful voting for reviews
    path('<int:review_id>/helpful/', views.vote_helpful, name='vote_helpful'),
    # Backward compatibility
    path('<int:review_id>/mark_helpful/', views.vote_helpful, name='mark_review_helpful'),
    
    # Review success page
    path('success/', ReviewSuccessView.as_view(), name='review_success'),
    
    # Comment management
    path('<int:review_id>/comments/add/', views.add_review_comment, name='add_review_comment'),
    # Backward compatibility
    path('<int:review_id>/comment/', views.add_review_comment, name='add_comment'),
    
    # Test template tag
    path('test-template-tag/', TestTemplateTagView.as_view(), name='test_template_tag'),
    path('test-template-tag-fn/', test_template_tag_view, name='test_template_tag_fn'),
    
    # Comment moderation
    path('comments/moderate/', views.comment_moderation, name='comment_moderation'),
    path('comments/<int:comment_id>/approve/', views.approve_comment, name='approve_comment'),
    path('comments/<int:comment_id>/reject/', views.reject_comment, name='reject_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]
