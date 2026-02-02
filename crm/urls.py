"""
API URL configuration for CRM app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RestaurantViewSet, CustomerViewSet, VisitViewSet,
    CampaignViewSet, OutreachEventViewSet
)

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'visits', VisitViewSet, basename='visit')
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'outreach-events', OutreachEventViewSet, basename='outreach-event')

urlpatterns = [
    path('', include(router.urls)),
]
