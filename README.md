# CRM Backend Service

A production-leaning backend service for customer lifecycle management and automated outreach, built with Django REST Framework, Celery, PostgreSQL, and Redis. The system provides RESTful APIs for customer segmentation and campaign execution, and includes a minimal Bootstrap-based internal dashboard for operational visibility.

## Features

- **Restaurant & Customer Management**: Full CRUD operations for restaurants and customers
- **Visit Tracking**: Record customer visits with automatic total spend calculation
- **Customer Segmentation**: Filter customers by inactivity days or spending thresholds
- **Campaign Management**: Create and manage marketing campaigns with segmentation rules
- **Automated Outreach**: Asynchronous campaign processing using Celery
- **Audit Trail**: Complete outreach event tracking with status and error handling
- **REST API**: Full-featured REST API using Django REST Framework
- **Internal Dashboard**: Bootstrap-based ops dashboard for campaign management
- **Comprehensive Tests**: Automated test suite covering core functionality

## Architecture

### ORM-First Backend Design

The backend is designed around Django’s ORM as the primary data access layer, prioritizing correctness, consistency, and maintainability.

- **Centralized data access** All database interactions flow through the Django ORM; raw SQL is intentionally avoided
- **Advanced querying**: Use of filtered QuerySets, annotations, and aggregations
- **Query optimization**: Consistent use of `select_related` and `prefetch_related` to avoid N+1 query patterns
- **Transactional integrity**: Critical write paths use `transaction.atomic` and row-level locking (`select_for_update`) to ensure correctness under concurrent access
- **Idempotent operations**: Campaign execution and outreach event creation rely on idempotent ORM patterns (`get_or_create`, `update_or_create`)
- **Model-level guarantees**: Uniqueness constraints and indexes defined at the schema level
- **Service layer**: Business logic is encapsulated in services, keeping views thin and focused

### MTV Alignment

The codebase follows Django’s MTV (Model–Template–View) architecture:

- **Models** define domain entities, constraints, and persistence logic.
- **Views** handle request orchestration via DRF viewsets and internal controllers.
- **Templates** are used exclusively for a minimal, server-rendered internal dashboard.

This separation keeps domain logic isolated, APIs clean, and presentation concerns intentionally scoped.


### Technology Stack

- **Language**: Python 3.9+
- **Application Layer**: Django + Django REST Framework
- **Data Persistence**: PostgreSQL (via Django ORM)
- **Asynchronous Processing**: Celery with Redis as broker and result backend
- **Local Infrastructure**: Docker Compose

**Note**: Specific package versions are pinned in `requirements.txt` and `docker-compose.yml` for reproducible deployments.

## Prerequisites

- **Operating System**: Windows 10/11, Linux, or macOS
- **Docker** (Docker Desktop on Windows/macOS, Docker Engine on Linux)
- **Python 3.9+** installed
- **Git** installed
- **Terminal**: Git Bash (Windows), Terminal (Linux/macOS), or any Unix-like shell

## Cross-Platform Support

This project is **fully cross-platform** and works on:
- ✅ **Windows** (10/11) - Tested with Git Bash
- ✅ **Linux** (Ubuntu, Debian, etc.) - Native support
- ✅ **macOS** - Native support

The only platform-specific configuration is Celery's worker pool, which is automatically detected:
- **Windows**: Uses `solo` pool (required due to lack of fork support)
- **Linux/macOS**: Uses `prefork` pool (better performance, multi-process)

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd /c/Django/CRMBackendService
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Activate virtual environment:**

**On Windows (Git Bash):**
```bash
source venv/Scripts/activate
```

**On Linux/macOS:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt after activation.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Windows-specific**: If you encounter issues installing `psycopg2-binary` on Windows (especially with Python 3.13), you may need to install Microsoft Visual C++ Build Tools. Alternatively:

```bash
pip install psycopg2-binary --upgrade
```

Or install from a pre-built wheel (adjust URL for your Python version):

```bash
pip install https://github.com/psycopg/psycopg2/releases/download/2.9.9/psycopg2_binary-2.9.9-cp39-cp39-win_amd64.whl
```

**Linux/macOS**: `psycopg2-binary` typically installs without issues.

### 4. Configure Environment Variables

Create a local `.env` file from the provided template:
```bash
cp .env.example .env
```

Edit .env as needed for your environment (at minimum, set SECRET_KEY).

Configuration is documented in .env.example.

**Important**: Never commit the `.env` file to version control.

### 5. Start Docker Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

Verify services are running:

```bash
docker-compose ps
```

Both services should show "healthy" status.

### 6. Run Database Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

This allows access to Django admin at `/admin/`.

## Running the Application

### Start Django Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

### Start Celery Worker

Open a **new terminal**, activate the virtual environment, and run:

**On Windows:**
```bash
source venv/Scripts/activate
celery -A crm_backend worker --loglevel=info --pool=solo
```

**On Linux/macOS:**
```bash
source venv/bin/activate
celery -A crm_backend worker --loglevel=info
```

**Note**: 
- On Windows, `--pool=solo` is required to avoid permission errors (automatically configured in `settings.py`)
- On Linux/macOS, the default `prefork` pool works perfectly and provides better performance

The Celery worker will process campaign tasks asynchronously.

### Access Internal Dashboard

Navigate to `http://localhost:8000/internal/` in your browser.

## API Endpoints

### Restaurants

- `GET /api/restaurants/` - List restaurants
- `POST /api/restaurants/` - Create restaurant
- `GET /api/restaurants/{id}/` - Get restaurant
- `PUT /api/restaurants/{id}/` - Update restaurant
- `DELETE /api/restaurants/{id}/` - Delete restaurant

### Customers

- `GET /api/customers/` - List customers
- `POST /api/customers/` - Create customer
- `GET /api/customers/{id}/` - Get customer
- `PUT /api/customers/{id}/` - Update customer
- `DELETE /api/customers/{id}/` - Delete customer
- `POST /api/customers/{id}/add_visit/` - Add visit to customer
- `GET /api/customers/inactive/?days=30` - Get inactive customers
- `GET /api/customers/high_spenders/?min_spend_cents=50000` - Get high spenders

### Visits

- `GET /api/visits/` - List visits
- `POST /api/visits/` - Create visit
- `GET /api/visits/{id}/` - Get visit
- `PUT /api/visits/{id}/` - Update visit
- `DELETE /api/visits/{id}/` - Delete visit

### Campaigns

- `GET /api/campaigns/` - List campaigns
- `POST /api/campaigns/` - Create campaign
- `GET /api/campaigns/{id}/` - Get campaign
- `PUT /api/campaigns/{id}/` - Update campaign
- `DELETE /api/campaigns/{id}/` - Delete campaign
- `POST /api/campaigns/{id}/run/` - Trigger campaign execution
- `GET /api/campaigns/{id}/events/` - Get campaign outreach events

### Outreach Events

- `GET /api/outreach-events/` - List outreach events
- `GET /api/outreach-events/{id}/` - Get outreach event

## Example API Usage

### Create a Restaurant

```bash
curl -X POST http://localhost:8000/api/restaurants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pizza Palace",
    "timezone": "America/New_York"
  }'
```

### Create a Customer

```bash
curl -X POST http://localhost:8000/api/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant": 1,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Add a Visit

```bash
curl -X POST http://localhost:8000/api/customers/1/add_visit/ \
  -H "Content-Type: application/json" \
  -d '{
    "spend_cents": 2500
  }'
```

### Create a Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant": 1,
    "name": "Win Back Inactive Customers",
    "status": "draft",
    "segment_type": "inactive_days",
    "segment_value": 30,
    "message_template": "Hi {first_name}, we miss you! Come back for 20% off."
  }'
```

### Run a Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/1/run/
```

### Get Inactive Customers

```bash
curl http://localhost:8000/api/customers/inactive/?days=30
```

### Get High Spenders

```bash
curl http://localhost:8000/api/customers/high_spenders/?min_spend_cents=50000
```

## Running Tests

Run the full test suite:

```bash
python manage.py test
```

Run tests with verbose output (shows test names as they run):

```bash
python manage.py test --verbosity=2
```

Run tests and filter output to show only test names and results:

```bash
python manage.py test --verbosity=2 2>&1 | grep -E "test_|Ran|OK|FAILED"
```

This command provides a clean, concise view of which tests ran and their results by filtering out migration messages and other verbose output.

**Note**: 
- On Linux/macOS and Git Bash (Windows): `grep` is available by default
- On Windows CMD (without Git Bash): Use `findstr` instead:
  ```cmd
  python manage.py test --verbosity=2 2>&1 | findstr /R "test_ Ran OK FAILED"
  ```

Run tests for a specific app:

```bash
python manage.py test crm
```

Run a specific test class:

```bash
python manage.py test crm.tests.RecordVisitTest
```

## Docker Compose Commands

### Start Services

```bash
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs -f
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

**Warning**: This will delete all database data.

## Project Structure

```
CRMBackendService/
├── crm_backend/          # Django project settings
│   ├── __init__.py
│   ├── settings.py       # Django settings with env var loading
│   ├── urls.py           # Root URL configuration
│   ├── wsgi.py
│   └── celery.py         # Celery app configuration
├── crm/                  # Main CRM app
│   ├── models.py         # Domain models with constraints/indexes
│   ├── services.py       # Business logic layer (ORM usage)
│   ├── serializers.py   # DRF serializers
│   ├── views.py          # DRF viewsets
│   ├── urls.py           # API URL configuration
│   ├── tasks.py          # Celery async tasks
│   ├── internal_views.py # Internal dashboard views
│   ├── internal_urls.py  # Internal dashboard URLs
│   └── tests.py          # Comprehensive test suite
├── templates/            # Django templates
│   ├── base.html
│   └── crm/
│       ├── campaigns_list.html
│       └── campaign_detail.html
├── docker-compose.yml    # PostgreSQL + Redis services
├── requirements.txt      # Python dependencies
├── manage.py
└── README.md
```

## ORM Usage Highlights

### Transaction Safety

The `record_visit` service function demonstrates proper transaction handling:

```python
@transaction.atomic
def record_visit(customer, spend_cents, visited_at=None):
    customer = Customer.objects.select_for_update().get(pk=customer.pk)
    visit = Visit.objects.create(...)
    customer.total_spend_cents += spend_cents
    customer.save()
```

### Query Optimization

Views use `select_related` and `prefetch_related` to avoid N+1 queries:

```python
queryset = Customer.objects.select_related('restaurant').all()
```

### Aggregation and Annotation

The internal dashboard uses `annotate` and `aggregate` for efficient counting:

```python
campaigns = Campaign.objects.annotate(
    total_events=Count('outreach_events'),
    sent_events=Count('outreach_events', filter=Q(outreach_events__status='sent')),
)
```

### Idempotent Operations

Campaign tasks use `get_or_create` for safe concurrent execution:

```python
event, created = OutreachEvent.objects.get_or_create(
    campaign=campaign,
    customer=customer,
    defaults={'status': 'queued'}
)
```

## Internal Dashboard

The internal dashboard (`/internal/`) provides:

- **Campaign List**: View all campaigns with status and event counts
- **Campaign Detail**: View campaign details, event statistics, and paginated event list
- **Campaign Controls**: Run, pause, and resume campaigns
- **Real-time Updates**: See campaign execution progress

Access at: `http://localhost:8000/internal/`

## Database Schema

### Models

- **Restaurant**: Restaurant entities with timezone support
- **Customer**: Customers with unique email per restaurant, total spend tracking
- **Visit**: Individual visit/order records
- **Campaign**: Marketing campaigns with segmentation rules
- **OutreachEvent**: Audit trail for all outreach attempts

### Constraints

- Unique constraint: `(restaurant, email)` on Customer
- Unique constraint: `(campaign, customer)` on OutreachEvent
- Indexes on `Customer.last_visit_at` and `Customer.total_spend_cents`

## Development Notes

### Environment Variables

All configuration is loaded from `.env` using `python-dotenv`. Never commit `.env` to version control.

### Logging

The project includes structured logging configuration. Check console output for:
- Campaign execution progress
- Email sending simulation
- Error messages

### Celery Tasks

Campaign execution runs asynchronously via Celery. Tasks:
- Load campaigns and customers via ORM
- Apply segmentation filters
- Create outreach events idempotently
- Process in batches of 200
- Simulate email sending (logs output)
- Update event status and capture errors

## Troubleshooting

### Database Connection Issues

If you can't connect to PostgreSQL:

1. Verify Docker containers are running: `docker-compose ps`
2. Check database credentials in `.env`
3. Ensure PostgreSQL is healthy: `docker-compose logs postgres`

### Celery Worker Not Processing Tasks

1. Ensure Redis is running: `docker-compose ps`
2. Check Celery worker logs for errors
3. Verify `CELERY_BROKER_URL` in `.env` matches Redis URL

**Windows-specific**: If you see `PermissionError: [WinError 5] Access is denied` errors, make sure you're using `--pool=solo` flag:
```bash
celery -A crm_backend worker --loglevel=info --pool=solo
```
This is required because Windows doesn't support Unix-style process forking used by Celery's default prefork pool. On Linux/macOS, the default prefork pool works without issues.

### Migration Issues

If migrations fail:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Port Already in Use

If port 8000 is in use:

```bash
python manage.py runserver 8001
```

## Production Considerations

This is a development setup. For production:

1. Set `DEBUG=False` and configure `ALLOWED_HOSTS`
2. Use a strong `SECRET_KEY`
3. Configure proper database credentials
4. Set up proper email service (replace simulation)
5. Use a production WSGI server (e.g., Gunicorn)
6. Configure static file serving
7. Set up proper monitoring and logging
8. Use environment-specific settings

## License

This project is provided as-is for demonstration purposes.

## Support

For issues or questions, please refer to the Django and Celery documentation:

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
