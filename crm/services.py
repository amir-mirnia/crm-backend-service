"""
Domain service layer for CRM business logic.
All database operations use Django ORM with proper transaction handling.
"""
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Customer, Visit


@transaction.atomic
def record_visit(customer, spend_cents, visited_at=None):
    """
    Record a customer visit and update customer totals atomically.
    
    Uses select_for_update to prevent race conditions when updating
    customer totals.
    
    Args:
        customer: Customer instance or Customer ID
        spend_cents: Integer amount in cents
        visited_at: Optional datetime, defaults to now
    
    Returns:
        Visit instance
    """
    if visited_at is None:
        visited_at = timezone.now()
    
    # Ensure we have a Customer instance
    if isinstance(customer, int):
        customer = Customer.objects.select_for_update().get(pk=customer)
    else:
        # Refresh with select_for_update to lock the row
        customer = Customer.objects.select_for_update().get(pk=customer.pk)
    
    # Create visit record
    visit = Visit.objects.create(
        customer=customer,
        visited_at=visited_at,
        spend_cents=spend_cents
    )
    
    # Update customer totals atomically
    customer.total_spend_cents += spend_cents
    if customer.last_visit_at is None or visited_at > customer.last_visit_at:
        customer.last_visit_at = visited_at
    customer.save(update_fields=['total_spend_cents', 'last_visit_at'])
    
    return visit


def inactive_days(queryset, days):
    """
    Filter customers who haven't visited in N days.
    
    Args:
        queryset: Customer QuerySet
        days: Integer number of days
    
    Returns:
        Filtered QuerySet
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    return queryset.filter(
        Q(last_visit_at__lt=cutoff_date) | Q(last_visit_at__isnull=True)
    )


def high_spenders(queryset, min_spend_cents):
    """
    Filter customers with total spend >= min_spend_cents.
    
    Args:
        queryset: Customer QuerySet
        min_spend_cents: Integer minimum spend in cents
    
    Returns:
        Filtered QuerySet
    """
    return queryset.filter(total_spend_cents__gte=min_spend_cents)
