"""
CRM domain models with proper constraints and indexes.
All database access should go through Django ORM.
"""
from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
import pytz


class Restaurant(models.Model):
    """Restaurant entity."""
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def get_timezone(self):
        """Return pytz timezone object."""
        try:
            return pytz.timezone(self.timezone)
        except pytz.UnknownTimeZoneError:
            return pytz.UTC


class Customer(models.Model):
    """Customer entity with unique email per restaurant."""
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='customers'
    )
    email = models.EmailField(validators=[EmailValidator()])
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    total_spend_cents = models.BigIntegerField(default=0)
    last_visit_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['restaurant', 'email']]
        indexes = [
            models.Index(fields=['last_visit_at']),
            models.Index(fields=['total_spend_cents']),
            models.Index(fields=['restaurant', 'email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def total_spend_dollars(self):
        """Return total spend in dollars."""
        return self.total_spend_cents / 100.0


class Visit(models.Model):
    """Customer visit/order record."""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='visits'
    )
    visited_at = models.DateTimeField(default=timezone.now)
    spend_cents = models.BigIntegerField()

    class Meta:
        ordering = ['-visited_at']
        indexes = [
            models.Index(fields=['visited_at']),
            models.Index(fields=['customer', 'visited_at']),
        ]

    def __str__(self):
        return f"Visit {self.id} - {self.customer.email} - {self.visited_at}"

    @property
    def spend_dollars(self):
        """Return spend in dollars."""
        return self.spend_cents / 100.0


class Campaign(models.Model):
    """Campaign with segmentation rules."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    SEGMENT_TYPE_CHOICES = [
        ('inactive_days', 'Inactive Days'),
        ('high_spenders', 'High Spenders'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    segment_type = models.CharField(max_length=20, choices=SEGMENT_TYPE_CHOICES)
    segment_value = models.IntegerField(help_text="Days for inactive_days, cents for high_spenders")
    message_template = models.TextField(help_text="Supports {first_name} placeholder")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['restaurant', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"


class OutreachEvent(models.Model):
    """Outreach event audit trail."""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
    ]

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='outreach_events'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='outreach_events'
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='email')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['campaign', 'customer']]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.campaign.name} -> {self.customer.email} ({self.status})"
