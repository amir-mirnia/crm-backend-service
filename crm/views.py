"""
DRF viewsets for CRM API.
Uses select_related/prefetch_related to avoid N+1 queries.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Restaurant, Customer, Visit, Campaign, OutreachEvent
from .serializers import (
    RestaurantSerializer, CustomerSerializer, VisitSerializer,
    AddVisitSerializer, CampaignSerializer, OutreachEventSerializer
)
from .services import record_visit, inactive_days, high_spenders
from .tasks import run_campaign_task


class RestaurantViewSet(viewsets.ModelViewSet):
    """Restaurant CRUD."""
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """Customer CRUD with segmentation endpoints."""
    queryset = Customer.objects.select_related('restaurant').all()
    serializer_class = CustomerSerializer
    
    def get_queryset(self):
        """Filter by restaurant if provided."""
        queryset = super().get_queryset()
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def add_visit(self, request, pk=None):
        """Add a visit to a customer."""
        customer = self.get_object()
        serializer = AddVisitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        visit = record_visit(
            customer=customer,
            spend_cents=serializer.validated_data['spend_cents'],
            visited_at=serializer.validated_data.get('visited_at')
        )
        
        return Response(
            VisitSerializer(visit).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def inactive(self, request):
        """Get inactive customers."""
        days = int(request.query_params.get('days', 30))
        queryset = self.get_queryset()
        queryset = inactive_days(queryset, days)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_spenders(self, request):
        """Get high spending customers."""
        min_spend_cents = int(request.query_params.get('min_spend_cents', 50000))
        queryset = self.get_queryset()
        queryset = high_spenders(queryset, min_spend_cents)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VisitViewSet(viewsets.ModelViewSet):
    """Visit CRUD."""
    queryset = Visit.objects.select_related('customer', 'customer__restaurant').all()
    serializer_class = VisitSerializer
    
    def get_queryset(self):
        """Filter by customer if provided."""
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset


class CampaignViewSet(viewsets.ModelViewSet):
    """Campaign CRUD with run action."""
    queryset = Campaign.objects.select_related('restaurant').all()
    serializer_class = CampaignSerializer
    
    def get_queryset(self):
        """Filter by restaurant if provided."""
        queryset = super().get_queryset()
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Trigger campaign execution via Celery."""
        campaign = self.get_object()
        
        if campaign.status not in ['draft', 'paused']:
            return Response(
                {'error': f'Campaign must be draft or paused, current status: {campaign.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task
        run_campaign_task.delay(campaign.id)
        
        # Update status to running
        campaign.status = 'running'
        campaign.save(update_fields=['status'])
        
        return Response(
            {'message': 'Campaign execution started', 'campaign_id': campaign.id},
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get paginated outreach events for a campaign."""
        campaign = self.get_object()
        queryset = OutreachEvent.objects.filter(
            campaign=campaign
        ).select_related('customer', 'customer__restaurant').order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OutreachEventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OutreachEventSerializer(queryset, many=True)
        return Response(serializer.data)


class OutreachEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Outreach event read-only viewset."""
    queryset = OutreachEvent.objects.select_related(
        'campaign', 'customer', 'customer__restaurant'
    ).all()
    serializer_class = OutreachEventSerializer
    
    def get_queryset(self):
        """Filter by campaign if provided."""
        queryset = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        return queryset
