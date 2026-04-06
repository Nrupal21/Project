"""
Views package for the destinations app.

This __init__.py file imports and re-exports all view classes and functions
from the main views.py file to maintain compatibility with the project structure.
This allows both the views.py file and views/ directory to coexist without conflicts.

The indigo/violet color scheme is maintained throughout all view templates
and comprehensive comments are added to all functions for better code readability.
"""

# Import all views from the main views.py file
import sys
import os
import importlib.util

# Import views from separate modules
from .my_attractions import MyAttractionsView
from .manager_dashboard import ManagerDashboardView  # Dashboard view for managers and admins

# Get the path to the main views.py file
views_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'views.py')

# Import the views.py file as a module
spec = importlib.util.spec_from_file_location('views_module', views_path)
views_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(views_module)

# Re-export all the classes and functions from views.py
# Class-based views
DestinationListView = views_module.DestinationListView
DestinationDetailView = views_module.DestinationDetailView
RegionDetailView = views_module.RegionDetailView
AttractionListView = views_module.AttractionListView
AttractionDetailView = views_module.AttractionDetailView
DestinationCreateView = views_module.DestinationCreateView
AttractionCreateView = views_module.AttractionCreateView
GuideDashboardView = views_module.GuideDashboardView  # Dashboard view for local guides
MyDestinationsView = views_module.MyDestinationsView  # View for user's destinations

# API ViewSets
DestinationViewSet = views_module.DestinationViewSet
RegionViewSet = views_module.RegionViewSet
AttractionViewSet = views_module.AttractionViewSet
SeasonViewSet = views_module.SeasonViewSet

# Function-based views
destination_list_view = views_module.destination_list_view
destination_detail_view = views_module.destination_detail_view
nearby_destinations = views_module.nearby_destinations

# Note: Admin views are defined in the admin.py module within this package
# and are imported directly from there to avoid circular imports.
