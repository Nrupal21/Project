"""
Transportation API v1 URL configuration.

Mount under: /api/v1/transportation/

Provides REST endpoints via DRF ViewSets:
- /types/
- /providers/
- /routes/
- /schedules/
- /options/
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "transportation_api_v1"

router = DefaultRouter()
router.register(r"types", views.TransportationTypeViewSet, basename="transportation-type")
router.register(r"providers", views.TransportationProviderViewSet, basename="transportation-provider")
router.register(r"routes", views.RouteViewSet, basename="transportation-route")
router.register(r"schedules", views.ScheduleViewSet, basename="transportation-schedule")
router.register(r"options", views.TransportationOptionViewSet, basename="transportation-option")

urlpatterns = [
    path("", include(router.urls)),
]
