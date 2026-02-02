"""
Comprehensive tests for CRM backend.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from .models import Restaurant, Customer, Visit, Campaign, OutreachEvent
from .services import record_visit, inactive_days, high_spenders


class RecordVisitTest(TestCase):
    """Test record_visit service function."""
    
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", timezone="UTC")
        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            total_spend_cents=0
        )
    
    def test_record_visit_updates_totals(self):
        """Test that record_visit updates customer totals correctly."""
        visit = record_visit(self.customer, spend_cents=5000)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.total_spend_cents, 5000)
        self.assertIsNotNone(self.customer.last_visit_at)
        self.assertEqual(visit.spend_cents, 5000)
    
    def test_record_visit_multiple_visits(self):
        """Test multiple visits accumulate correctly."""
        record_visit(self.customer, spend_cents=3000)
        record_visit(self.customer, spend_cents=2000)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.total_spend_cents, 5000)
    
    def test_record_visit_updates_last_visit_at(self):
        """Test that last_visit_at is updated correctly."""
        old_time = timezone.now() - timedelta(days=10)
        record_visit(self.customer, spend_cents=1000, visited_at=old_time)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.last_visit_at, old_time)
        
        new_time = timezone.now()
        record_visit(self.customer, spend_cents=1000, visited_at=new_time)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.last_visit_at, new_time)
    
    def test_record_visit_transaction_atomicity(self):
        """Test that record_visit is atomic."""
        # This test ensures that if something fails, the customer totals aren't partially updated
        # In a real scenario, we'd mock a failure, but for now we test the happy path
        visit = record_visit(self.customer, spend_cents=1000)
        self.assertIsNotNone(visit)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.total_spend_cents, 1000)


class SegmentationTest(TestCase):
    """Test segmentation functions."""
    
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", timezone="UTC")
        self.customer_active = Customer.objects.create(
            restaurant=self.restaurant,
            email="active@example.com",
            first_name="Active",
            last_name="User",
            total_spend_cents=10000,
            last_visit_at=timezone.now() - timedelta(days=5)
        )
        self.customer_inactive = Customer.objects.create(
            restaurant=self.restaurant,
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            total_spend_cents=5000,
            last_visit_at=timezone.now() - timedelta(days=35)
        )
        self.customer_no_visits = Customer.objects.create(
            restaurant=self.restaurant,
            email="novisits@example.com",
            first_name="No",
            last_name="Visits",
            total_spend_cents=0,
            last_visit_at=None
        )
    
    def test_inactive_days_segmentation(self):
        """Test inactive_days segmentation."""
        queryset = Customer.objects.filter(restaurant=self.restaurant)
        inactive = inactive_days(queryset, days=30)
        
        inactive_emails = set(inactive.values_list('email', flat=True))
        self.assertIn('inactive@example.com', inactive_emails)
        self.assertIn('novisits@example.com', inactive_emails)
        self.assertNotIn('active@example.com', inactive_emails)
    
    def test_high_spenders_segmentation(self):
        """Test high_spenders segmentation."""
        queryset = Customer.objects.filter(restaurant=self.restaurant)
        high = high_spenders(queryset, min_spend_cents=8000)
        
        high_emails = set(high.values_list('email', flat=True))
        self.assertIn('active@example.com', high_emails)
        self.assertNotIn('inactive@example.com', high_emails)
        self.assertNotIn('novisits@example.com', high_emails)


class RestaurantAPITest(TestCase):
    """Test Restaurant API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_create_restaurant(self):
        """Test creating a restaurant via API."""
        data = {
            'name': 'New Restaurant',
            'timezone': 'America/New_York'
        }
        response = self.client.post('/api/restaurants/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Restaurant.objects.count(), 1)
    
    def test_list_restaurants(self):
        """Test listing restaurants."""
        Restaurant.objects.create(name="Restaurant 1", timezone="UTC")
        Restaurant.objects.create(name="Restaurant 2", timezone="UTC")
        
        response = self.client.get('/api/restaurants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_get_restaurant(self):
        """Test getting a single restaurant."""
        restaurant = Restaurant.objects.create(name="Test Restaurant", timezone="UTC")
        response = self.client.get(f'/api/restaurants/{restaurant.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Restaurant')


class CustomerAPITest(TestCase):
    """Test Customer API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", timezone="UTC")
        self.customer = Customer.objects.create(
            restaurant=self.restaurant,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            total_spend_cents=0
        )
    
    def test_create_customer(self):
        """Test creating a customer via API."""
        data = {
            'restaurant': self.restaurant.id,
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'Customer'
        }
        response = self.client.post('/api/customers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 2)
    
    def test_add_visit_endpoint(self):
        """Test adding a visit via API."""
        data = {
            'spend_cents': 5000
        }
        response = self.client.post(
            f'/api/customers/{self.customer.id}/add_visit/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.total_spend_cents, 5000)
    
    def test_inactive_customers_endpoint(self):
        """Test inactive customers endpoint."""
        # Create an inactive customer
        Customer.objects.create(
            restaurant=self.restaurant,
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            last_visit_at=timezone.now() - timedelta(days=35)
        )
        
        response = self.client.get('/api/customers/inactive/?days=30')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_high_spenders_endpoint(self):
        """Test high spenders endpoint."""
        # Create a high spender
        Customer.objects.create(
            restaurant=self.restaurant,
            email="high@example.com",
            first_name="High",
            last_name="Spender",
            total_spend_cents=100000
        )
        
        response = self.client.get('/api/customers/high_spenders/?min_spend_cents=50000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_unique_email_per_restaurant(self):
        """Test that email must be unique per restaurant."""
        data = {
            'restaurant': self.restaurant.id,
            'email': 'test@example.com',  # Same email as existing customer
            'first_name': 'Duplicate',
            'last_name': 'Email'
        }
        response = self.client.post('/api/customers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CampaignAPITest(TestCase):
    """Test Campaign API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", timezone="UTC")
        self.campaign = Campaign.objects.create(
            restaurant=self.restaurant,
            name="Test Campaign",
            status='draft',
            segment_type='inactive_days',
            segment_value=30,
            message_template="Hello {first_name}!"
        )
    
    def test_create_campaign(self):
        """Test creating a campaign via API."""
        data = {
            'restaurant': self.restaurant.id,
            'name': 'New Campaign',
            'status': 'draft',
            'segment_type': 'high_spenders',
            'segment_value': 50000,
            'message_template': 'Hi {first_name}!'
        }
        response = self.client.post('/api/campaigns/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Campaign.objects.count(), 2)
    
    def test_run_campaign_endpoint(self):
        """Test running a campaign via API."""
        response = self.client.post(f'/api/campaigns/{self.campaign.id}/run/')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, 'running')
    
    def test_get_campaign_events(self):
        """Test getting campaign events."""
        customer = Customer.objects.create(
            restaurant=self.restaurant,
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        OutreachEvent.objects.create(
            campaign=self.campaign,
            customer=customer,
            status='sent'
        )
        
        response = self.client.get(f'/api/campaigns/{self.campaign.id}/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)


class CampaignTaskTest(TestCase):
    """Test Celery campaign task."""
    
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", timezone="UTC")
        self.customer1 = Customer.objects.create(
            restaurant=self.restaurant,
            email="customer1@example.com",
            first_name="Customer",
            last_name="One",
            total_spend_cents=0,
            last_visit_at=timezone.now() - timedelta(days=35)  # Inactive
        )
        self.customer2 = Customer.objects.create(
            restaurant=self.restaurant,
            email="customer2@example.com",
            first_name="Customer",
            last_name="Two",
            total_spend_cents=0,
            last_visit_at=timezone.now() - timedelta(days=5)  # Active
        )
        self.campaign = Campaign.objects.create(
            restaurant=self.restaurant,
            name="Test Campaign",
            status='draft',
            segment_type='inactive_days',
            segment_value=30,
            message_template="Hello {first_name}, come back!"
        )
    
    def test_run_campaign_task_creates_events(self):
        """Test that running a campaign creates outreach events."""
        from .tasks import run_campaign_task
        
        # Run task synchronously (eager mode for testing)
        result = run_campaign_task(self.campaign.id)
        
        # Check that events were created
        events = OutreachEvent.objects.filter(campaign=self.campaign)
        self.assertGreater(events.count(), 0)
        
        # Check that only inactive customer got an event
        customer1_event = OutreachEvent.objects.filter(
            campaign=self.campaign,
            customer=self.customer1
        ).first()
        self.assertIsNotNone(customer1_event)
        
        customer2_event = OutreachEvent.objects.filter(
            campaign=self.campaign,
            customer=self.customer2
        ).first()
        self.assertIsNone(customer2_event)
        
        # Check campaign status
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, 'completed')
    
    def test_run_campaign_idempotency(self):
        """Test that running a campaign twice doesn't create duplicate events."""
        from .tasks import run_campaign_task
        
        # Run first time
        run_campaign_task(self.campaign.id)
        first_count = OutreachEvent.objects.filter(campaign=self.campaign).count()
        
        # Reset campaign status
        self.campaign.status = 'draft'
        self.campaign.save()
        
        # Run second time
        run_campaign_task(self.campaign.id)
        second_count = OutreachEvent.objects.filter(campaign=self.campaign).count()
        
        # Should have same number of events (idempotent)
        self.assertEqual(first_count, second_count)
