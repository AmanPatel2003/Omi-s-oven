# 🎂 Cake Shop — FastAPI Backend

## Stack
- **FastAPI** — REST API
- **MongoDB + Motor** — Async database
- **Redis + Celery** — Background tasks & caching
- **Razorpay** — UPI & payments
- **Cloudinary** — Image storage
- **Twilio** — WhatsApp notifications
- **WeasyPrint** — PDF salary slips & invoices

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Fill in your keys in .env

# 3. Run with Docker (recommended)
docker-compose up --build

# 4. Or run locally
uvicorn app.main:app --reload

# API docs available at:
# http://localhost:8000/docs
```

## Project Structure
```
app/
├── main.py          # Entry point, CORS, router registration
├── config.py        # All settings from .env
├── database.py      # MongoDB connection + indexes
├── api/v1/          # Route handlers (thin — just call services)
│   └── admin/       # Admin-only routes
├── models/          # MongoDB document shapes
├── schemas/         # Request/response Pydantic schemas
├── services/        # All business logic lives here
├── core/            # Auth, dependencies, exceptions
├── tasks/           # Celery background jobs
└── utils/           # Helpers (PDF, image, maps, pagination)
```

## Running Background Workers
```bash
# Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Scheduler (for daily tasks)
celery -A app.tasks.celery_app beat --loglevel=info
```
