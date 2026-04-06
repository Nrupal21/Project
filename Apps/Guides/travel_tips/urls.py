"""
URL configuration for the travel_tips app.

This module defines all the URL patterns for the travel tips functionality,
including listing, detail views, and management interfaces.
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

# App namespace for URL reversing
app_name = 'travel_tips'

urlpatterns = [
    # Public views
    path('', views.TravelTipListView.as_view(), name='list'),
    path('category/', views.TravelTipCategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.TravelTipCategoryDetailView.as_view(), name='category_detail'),
    path('<slug:slug>/', views.TravelTipDetailView.as_view(), name='detail'),
    
    # Comment and bookmark actions
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('<slug:slug>/bookmark/', login_required(views.toggle_bookmark), name='toggle_bookmark'),
    path('bookmarks/', login_required(views.my_bookmarks), name='my_bookmarks'),
    
    # Tip management (requires login)
    path('create/', login_required(views.TravelTipCreateView.as_view()), name='create'),
    path('<slug:slug>/update/', login_required(views.TravelTipUpdateView.as_view()), name='update'),
    path('<slug:slug>/delete/', login_required(views.TravelTipDeleteView.as_view()), name='delete'),
    
    # Admin/management views (staff only)
    path('drafts/', login_required(views.TravelTipDraftListView.as_view()), name='draft_list'),
    path('pending-comments/', login_required(views.PendingCommentListView.as_view()), 
         name='pending_comments'),
    path('comment/<int:pk>/approve/', login_required(views.approve_comment), 
         name='approve_comment'),
    path('comment/<int:pk>/delete/', login_required(views.delete_comment), 
         name='delete_comment'),
]
