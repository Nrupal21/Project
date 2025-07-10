from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = 'core'

urlpatterns = [
    # Home page
    path('', views.HomeView.as_view(), name='home'),
    
    # Static pages
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    
    # Redirect any old URLs to the new ones
    path('core/home/', RedirectView.as_view(pattern_name='core:home', permanent=True)),
    path('core/about/', RedirectView.as_view(pattern_name='core:about', permanent=True)),
    path('core/contact/', RedirectView.as_view(pattern_name='core:contact', permanent=True)),
    path('core/terms/', RedirectView.as_view(pattern_name='core:terms', permanent=True)),
]
