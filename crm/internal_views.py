"""
Internal ops dashboard views using Django templates and Bootstrap.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Campaign, OutreachEvent
from .tasks import run_campaign_task


def index(request):
    """Redirect to campaigns list."""
    return redirect('internal:campaigns')


@require_http_methods(["GET"])
def campaigns_list(request):
    """List all campaigns with status and segment info."""
    campaigns = Campaign.objects.select_related('restaurant').annotate(
        total_events=Count('outreach_events'),
        sent_events=Count('outreach_events', filter=Q(outreach_events__status='sent')),
        failed_events=Count('outreach_events', filter=Q(outreach_events__status='failed')),
    ).order_by('-created_at')
    
    context = {
        'campaigns': campaigns,
    }
    return render(request, 'crm/campaigns_list.html', context)


@require_http_methods(["GET"])
def campaign_detail(request, campaign_id):
    """Campaign detail with event counts and paginated events table."""
    campaign = get_object_or_404(
        Campaign.objects.select_related('restaurant'),
        pk=campaign_id
    )
    
    # Get event counts using annotate/aggregate
    events = OutreachEvent.objects.filter(campaign=campaign).select_related(
        'customer', 'customer__restaurant'
    )
    
    event_counts = events.aggregate(
        total=Count('id'),
        queued=Count('id', filter=Q(status='queued')),
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed')),
        skipped=Count('id', filter=Q(status='skipped')),
    )
    
    # Paginate recent events
    events_ordered = events.order_by('-created_at')
    paginator = Paginator(events_ordered, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'campaign': campaign,
        'event_counts': event_counts,
        'page_obj': page_obj,
    }
    return render(request, 'crm/campaign_detail.html', context)


@require_http_methods(["POST"])
def campaign_run(request, campaign_id):
    """Trigger campaign execution."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    
    if campaign.status not in ['draft', 'paused']:
        messages.error(
            request,
            f'Campaign must be draft or paused, current status: {campaign.status}'
        )
    else:
        run_campaign_task.delay(campaign.id)
        campaign.status = 'running'
        campaign.save(update_fields=['status'])
        messages.success(request, f'Campaign "{campaign.name}" execution started')
    
    return redirect('internal:campaign_detail', campaign_id=campaign_id)


@require_http_methods(["POST"])
def campaign_pause(request, campaign_id):
    """Pause a running campaign."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    
    if campaign.status == 'running':
        campaign.status = 'paused'
        campaign.save(update_fields=['status'])
        messages.success(request, f'Campaign "{campaign.name}" paused')
    else:
        messages.error(request, f'Campaign is not running, current status: {campaign.status}')
    
    return redirect('internal:campaign_detail', campaign_id=campaign_id)


@require_http_methods(["POST"])
def campaign_resume(request, campaign_id):
    """Resume a paused campaign."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    
    if campaign.status == 'paused':
        run_campaign_task.delay(campaign.id)
        campaign.status = 'running'
        campaign.save(update_fields=['status'])
        messages.success(request, f'Campaign "{campaign.name}" resumed')
    else:
        messages.error(request, f'Campaign is not paused, current status: {campaign.status}')
    
    return redirect('internal:campaign_detail', campaign_id=campaign_id)
