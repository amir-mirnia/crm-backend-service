"""
Internal dashboard URL configuration.
"""
from django.urls import path
from . import internal_views

app_name = 'internal'

urlpatterns = [
    path('', internal_views.index, name='index'),
    path('campaigns/', internal_views.campaigns_list, name='campaigns'),
    path('campaigns/<int:campaign_id>/', internal_views.campaign_detail, name='campaign_detail'),
    path('campaigns/<int:campaign_id>/run/', internal_views.campaign_run, name='campaign_run'),
    path('campaigns/<int:campaign_id>/pause/', internal_views.campaign_pause, name='campaign_pause'),
    path('campaigns/<int:campaign_id>/resume/', internal_views.campaign_resume, name='campaign_resume'),
]
