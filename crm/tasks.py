"""
Celery tasks for async campaign processing.
"""
import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .models import Campaign, Customer, OutreachEvent
from .services import inactive_days, high_spenders

logger = logging.getLogger(__name__)


@shared_task
def run_campaign_task(campaign_id):
    """
    Process a campaign asynchronously.
    
    - Loads campaign and restaurant via ORM
    - Selects customers via ORM segmentation
    - Creates OutreachEvents idempotently
    - Processes in batches
    - Simulates sending (logs output)
    - Updates status and sent_at
    - Captures failures with error_message
    """
    try:
        # Load campaign with restaurant
        campaign = Campaign.objects.select_related('restaurant').get(pk=campaign_id)
        logger.info(f"Starting campaign {campaign.id}: {campaign.name}")
        
        # Get restaurant customers
        customers_queryset = Customer.objects.filter(restaurant=campaign.restaurant)
        
        # Apply segmentation
        if campaign.segment_type == 'inactive_days':
            customers_queryset = inactive_days(customers_queryset, campaign.segment_value)
        elif campaign.segment_type == 'high_spenders':
            customers_queryset = high_spenders(customers_queryset, campaign.segment_value)
        else:
            logger.error(f"Unknown segment_type: {campaign.segment_type}")
            return
        
        # Get customer IDs
        customer_ids = list(customers_queryset.values_list('id', flat=True))
        logger.info(f"Found {len(customer_ids)} customers matching segment")
        
        # Process in batches
        batch_size = 200
        total_processed = 0
        total_sent = 0
        total_failed = 0
        
        for i in range(0, len(customer_ids), batch_size):
            batch_ids = customer_ids[i:i + batch_size]
            batch_customers = Customer.objects.filter(id__in=batch_ids)
            
            for customer in batch_customers:
                # Create or get outreach event idempotently
                event, created = OutreachEvent.objects.get_or_create(
                    campaign=campaign,
                    customer=customer,
                    defaults={
                        'status': 'queued',
                        'channel': 'email',
                    }
                )
                
                # Skip if already processed
                if event.status in ['sent', 'skipped']:
                    continue
                
                # Process the event
                try:
                    # Format message
                    message = campaign.message_template.format(
                        first_name=customer.first_name
                    )
                    
                    # Simulate sending (in production, this would call email service)
                    logger.info(
                        f"Sending email to {customer.email}: {message[:50]}..."
                    )
                    
                    # Simulate success/failure (90% success rate for demo)
                    import random
                    if random.random() < 0.9:
                        event.status = 'sent'
                        event.sent_at = timezone.now()
                        event.error_message = None
                        total_sent += 1
                    else:
                        event.status = 'failed'
                        event.error_message = "Simulated email delivery failure"
                        total_failed += 1
                    
                    event.save(update_fields=['status', 'sent_at', 'error_message'])
                    total_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing event {event.id}: {str(e)}")
                    event.status = 'failed'
                    event.error_message = str(e)
                    event.save(update_fields=['status', 'error_message'])
                    total_failed += 1
                    total_processed += 1
        
        # Update campaign status
        campaign.status = 'completed'
        campaign.save(update_fields=['status'])
        
        logger.info(
            f"Campaign {campaign.id} completed: "
            f"{total_processed} processed, {total_sent} sent, {total_failed} failed"
        )
        
        return {
            'campaign_id': campaign_id,
            'total_processed': total_processed,
            'total_sent': total_sent,
            'total_failed': total_failed,
        }
        
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return {'error': f'Campaign {campaign_id} not found'}
    except Exception as e:
        logger.error(f"Error running campaign {campaign_id}: {str(e)}", exc_info=True)
        # Update campaign status to paused on error
        try:
            campaign = Campaign.objects.get(pk=campaign_id)
            campaign.status = 'paused'
            campaign.save(update_fields=['status'])
        except:
            pass
        raise
