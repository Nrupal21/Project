"""
Tours API v1 URL configuration.

Mount under: /api/v1/tours/

Provides REST endpoints via DRF ViewSets (currently maintenance stubs):
- /tours/
- /categories/
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "tours_api_v1"

router = DefaultRouter()
router.register(r"tours", views.TourViewSet, basename="tour")
router.register(r"categories", views.TourCategoryViewSet, basename="tourcategory")

urlpatterns = [
    path("", include(router.urls)),
]
