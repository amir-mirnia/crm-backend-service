"""
DRF serializers for CRM API.
"""
from rest_framework import serializers
from .models import Restaurant, Customer, Visit, Campaign, OutreachEvent
from .services import record_visit, inactive_days, high_spenders


class RestaurantSerializer(serializers.ModelSerializer):
    """Restaurant serializer."""
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'timezone', 'created_at']
        read_only_fields = ['id', 'created_at']


class CustomerSerializer(serializers.ModelSerializer):
    """Customer serializer."""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    total_spend_dollars = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = Customer
        fields = [
            'id', 'restaurant', 'restaurant_name', 'email', 'first_name',
            'last_name', 'total_spend_cents', 'total_spend_dollars',
            'last_visit_at', 'created_at'
        ]
        read_only_fields = ['id', 'total_spend_cents', 'created_at']


class VisitSerializer(serializers.ModelSerializer):
    """Visit serializer."""
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    spend_dollars = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = Visit
        fields = ['id', 'customer', 'customer_email', 'visited_at', 'spend_cents', 'spend_dollars']
        read_only_fields = ['id']


class AddVisitSerializer(serializers.Serializer):
    """Serializer for adding a visit to a customer."""
    spend_cents = serializers.IntegerField(min_value=0)
    visited_at = serializers.DateTimeField(required=False)


class CampaignSerializer(serializers.ModelSerializer):
    """Campaign serializer."""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'restaurant', 'restaurant_name', 'name', 'status',
            'segment_type', 'segment_value', 'message_template', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OutreachEventSerializer(serializers.ModelSerializer):
    """Outreach event serializer."""
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    
    class Meta:
        model = OutreachEvent
        fields = [
            'id', 'campaign', 'campaign_name', 'customer', 'customer_email',
            'channel', 'status', 'error_message', 'sent_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
