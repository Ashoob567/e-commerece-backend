# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Luxe Market - Django 5.0 e-commerce REST API with DRF, JWT authentication, and PostgreSQL.

## Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements/development.txt

# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Testing
pytest                                    # Run all tests
pytest apps/<app>/tests.py               # Run specific app tests

# Code quality
black .                                   # Format code
isort .                                   # Sort imports
flake8 .                                  # Lint
```

## Architecture

**Config structure:**
- `config/settings/` - Split settings: `base.py` (shared), `development.py`, `production.py`
- `DJANGO_SETTINGS_MODULE=config.settings` (uses `__init__.py` to export appropriate settings)

**Apps (`apps/`):**
- `users` - User authentication via JWT (SimpleJWT)
- `products` - Product catalog
- `orders` - Order management
- `payments` - Payment processing
- `cart` - Shopping cart

**API routes:** All endpoints prefixed with `/api/<app>/` (see `config/urls.py`)

**Key packages:**
- Authentication: `djangorestframework-simplejwt` (1hr access, 7day refresh)
- Database: PostgreSQL via `dj-database-url` (env: `DATABASE_URL`)
- CORS: `django-cors-headers` (env: `CORS_ALLOWED_ORIGINS`)
- Static files: `whitenoise`

**Environment:** Configure via `.env` (see `.env.example`). Secrets: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`.
