# Quick Start Guide

## Prerequisites Check

- [ ] Docker (Docker Desktop on Windows/macOS, Docker Engine on Linux)
- [ ] Python 3.9+ is installed
- [ ] Terminal/Shell (Git Bash on Windows, Terminal on Linux/macOS)

## Setup Steps

1. **Activate virtual environment** (IMPORTANT: Do this in every new terminal)
   
   **On Windows:**
   ```bash
   source venv/Scripts/activate
   ```
   
   **On Linux/macOS:**
   ```bash
   source venv/bin/activate
   ```
   
   You should see `(venv)` in your prompt after activation.

2. **Install dependencies** (if not already installed)
   ```bash
   pip install -r requirements.txt
   ```
   
   **Windows-specific**: If you encounter `psycopg2-binary` build errors (especially with Python 3.13):
   - Try: `pip install psycopg2-binary --upgrade` first, then `pip install -r requirements.txt`
   - Or install Microsoft Visual C++ Build Tools
   
   **Linux/macOS**: Typically installs without issues.

3. **Create .env file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration if needed.

4. **Start Docker services**
   ```bash
   docker-compose up -d
   ```
   
   **Windows-specific**: If you have a local PostgreSQL service running, Docker uses port 5433 instead of 5432. The `.env` file is configured for this.
   
   **Linux/macOS**: Typically uses port 5432. Update `.env` if you have port conflicts.

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start Django server** (Terminal 1)
   ```bash
   python manage.py runserver
   ```

7. **Start Celery worker** (Terminal 2)
   
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
   
   **Note**: Windows requires `--pool=solo` (automatically configured in settings.py). Linux/macOS uses the default prefork pool for better performance.

## Access Points

- **API**: http://localhost:8000/api/
- **Internal Dashboard**: http://localhost:8000/internal/
- **Django Admin**: http://localhost:8000/admin/ (if superuser created)

**Note**: If port 8000 is in use, Django will automatically use port 8001. Check the terminal output to see which port is actually being used.

## Quick Test

```bash
# Create a restaurant (replace 8000 with your actual port)
curl -X POST http://localhost:8000/api/restaurants/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Restaurant", "timezone": "UTC"}'

# Create a customer
curl -X POST http://localhost:8000/api/customers/ \
  -H "Content-Type: application/json" \
  -d '{"restaurant": 1, "email": "test@example.com", "first_name": "Test", "last_name": "User"}'

# Add a visit
curl -X POST http://localhost:8000/api/customers/1/add_visit/ \
  -H "Content-Type: application/json" \
  -d '{"spend_cents": 5000}'
```

## Running Tests

```bash
python manage.py test
```

## Troubleshooting

- **Port 8000 in use**: Use `python manage.py runserver 8001`
- **Database connection error**: Check `docker-compose ps` and ensure containers are healthy
- **Celery not working**: Ensure Redis is running and check worker logs
