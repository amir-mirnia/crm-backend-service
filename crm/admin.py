"""
Django admin configuration (optional, not the main interface).
"""
from django.contrib import admin
from .models import Restaurant, Customer, Visit, Campaign, OutreachEvent


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'timezone', 'created_at']
    list_filter = ['timezone', 'created_at']
    search_fields = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'first_name', 'last_name', 'restaurant', 'total_spend_cents', 'last_visit_at']
    list_filter = ['restaurant', 'last_visit_at']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['total_spend_cents', 'created_at']


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'visited_at', 'spend_cents']
    list_filter = ['visited_at']
    search_fields = ['customer__email']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'restaurant', 'status', 'segment_type', 'segment_value', 'created_at']
    list_filter = ['status', 'segment_type', 'created_at']
    search_fields = ['name']


@admin.register(OutreachEvent)
class OutreachEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'campaign', 'customer', 'channel', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'channel', 'created_at']
    search_fields = ['customer__email', 'campaign__name']
