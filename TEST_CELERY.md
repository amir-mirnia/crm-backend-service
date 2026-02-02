## How to Test Celery

### Step 1: Create Test Data

First, create a restaurant and customer:

```bash
# Create a restaurant
curl -X POST http://localhost:8000/api/restaurants/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Pizza Palace", "timezone": "UTC"}'

# Response will include restaurant ID (e.g., {"id": 1, ...})
```

```bash
# Create a customer (replace 1 with your restaurant ID)
curl -X POST http://localhost:8000/api/customers/ \
  -H "Content-Type: application/json" \
  -d '{"restaurant": 1, "email": "test@example.com", "first_name": "John", "last_name": "Doe"}'

# Response will include customer ID (e.g., {"id": 1, ...})
```

```bash
# Make customer inactive by adding an old visit (30+ days ago)
# This requires using Django shell or API with visited_at parameter
```

### Step 2: Create a Campaign

```bash
# Create a campaign targeting inactive customers
curl -X POST http://localhost:8000/api/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant": 1,
    "name": "Win Back Campaign",
    "status": "draft",
    "segment_type": "inactive_days",
    "segment_value": 30,
    "message_template": "Hi {first_name}, we miss you! Come back for 20% off."
  }'

# Response will include campaign ID (e.g., {"id": 1, ...})
```

### Step 3: Trigger Campaign (This Uses Celery!)

```bash
# Run the campaign (replace 1 with your campaign ID)
curl -X POST http://localhost:8000/api/campaigns/1/run/

# Response: {"message": "Campaign execution started", "campaign_id": 1}
```

### Step 4: Watch Celery Worker

In your Celery worker terminal, you should see:

```
[2026-02-02 00:XX:XX,XXX: INFO/MainProcess] Task crm.tasks.run_campaign_task[<task-id>] received
[2026-02-02 00:XX:XX,XXX: INFO/MainProcess] Starting campaign 1: Win Back Campaign
[2026-02-02 00:XX:XX,XXX: INFO/MainProcess] Found X customers matching segment
[2026-02-02 00:XX:XX,XXX: INFO/MainProcess] Sending email to test@example.com: Hi John, we miss you!...
[2026-02-02 00:XX:XX,XXX: INFO/MainProcess] Campaign 1 completed: X processed, Y sent, Z failed
[2026-02-02 00:XX:XX,XXX: INFO/MainProcess] Task crm.tasks.run_campaign_task[<task-id>] succeeded
```

### Step 5: Check Results

```bash
# Check campaign events
curl http://localhost:8000/api/campaigns/1/events/

# Or use the internal dashboard
# Visit: http://localhost:8000/internal/campaigns/1/
```

---

## Quick Test via Internal Dashboard

1. Visit: http://localhost:8000/internal/campaigns/
2. Create a campaign (if you haven't already)
3. Click "Run Campaign" button
4. Watch the Celery worker terminal for activity
5. Refresh the campaign detail page to see results

---

## What Success Looks Like

✅ **Celery Worker Terminal:**
- Shows task received
- Shows campaign processing logs
- Shows "Task succeeded" message
- No errors

✅ **API Response:**
- Campaign status changes to "running" then "completed"
- Outreach events are created
- Events have status "sent" or "failed"

✅ **Internal Dashboard:**
- Campaign shows event counts
- Events appear in the table
- Status updates in real-time

---

## Troubleshooting

**No activity in Celery worker:**
- Check Redis is running: `docker-compose ps`
- Verify campaign status is "draft" or "paused" before running
- Check Django server logs for errors

**Tasks not processing:**
- Ensure Celery worker is running
- Check Redis connection in Celery logs
- Verify task is registered: Should see `crm.tasks.run_campaign_task` in startup

**Permission errors:**
- Make sure you're using `--pool=solo` on Windows
- Check settings.py has `CELERY_WORKER_POOL = 'solo'` for Windows
