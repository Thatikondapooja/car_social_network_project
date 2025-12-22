# Car Social — Backend

A Django-based backend for the Car Social project (car_social). This repository contains the server-side code, configuration, and instructions to run the development server, run tests, and deploy the application.

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
  - [Clone repository](#clone-repository)
  - [Create virtual environment](#create-virtual-environment)
  - [Install dependencies](#install-dependencies)
  - [Environment variables](#environment-variables)
  - [Database setup & migrations](#database-setup--migrations)
- [Running the Development Server](#running-the-development-server)
- [Static files & Media](#static-files--media)
- [Running Tests](#running-tests)
- [Linting & Formatting](#linting--formatting)
- [Deployment (production)](#deployment-production)
  - [Gunicorn + Nginx (Linux)](#gunicorn--nginx-linux)
  - [Docker (optional)](#docker-optional)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Project Overview

`car_social` is a Django application that provides backend services for a social platform focused on car enthusiasts: user accounts, posts, interactions, admin panels, media uploads, and analytics endpoints.

This repository contains Django apps such as `mainapp`, `userapp`, and `adminapp`, configuration (`car_social_network/settings.py`), and management scripts (`manage.py`).

## Features

- User registration and auth
- User profiles and media uploads
- Admin dashboards and moderation
- Feedback and interactions models
- Sentiment analysis endpoints (where applicable)

## Tech Stack

- Python 3.8+ (recommend 3.9/3.10)
- Django 4.x
- PostgreSQL (recommended for production) or SQLite (development)
- Optional: Gunicorn, Nginx, Docker

## Prerequisites

- Python 3.8 or newer installed
- pip installed
- Git
- (Optional) PostgreSQL or other DB for production

## Local Setup

1. Clone the repository

```bash
git clone <your-repo-url>
cd car_social
```

2. Create and activate a virtual environment

Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (cmd)

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

Unix / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

If a `requirements.txt` file exists in the project root:

```bash
pip install -r requirements.txt
```

If no `requirements.txt` is present, install Django and typical libraries:

```bash
pip install django psycopg2-binary djangorestframework
```

4. Environment variables

Create a file named `.env` (or set env vars in your environment) with at minimum:

```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DBNAME  # optional
ALLOWED_HOSTS=localhost,127.0.0.1
MEDIA_ROOT=media/
```

Adjust `car_social_network/settings.py` to load your environment variables (the repo may already include `emailsettings.py` and settings that read env vars).

5. Database setup & migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

If you are using PostgreSQL, ensure the database exists and your `DATABASES` settings or `DATABASE_URL` point to it.

## Running the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

Admin site: http://127.0.0.1:8000/admin/ (use superuser credentials)

## Static files & Media

For development, media files are usually served by Django when `DEBUG=True`.

To collect static files for production:

```bash
python manage.py collectstatic --noinput
```

Ensure `MEDIA_ROOT` and `STATIC_ROOT` are configured in settings for production hosting.

## Running Tests

Run Django tests with:

```bash
python manage.py test
```

Address failing tests by reading the failure trace and updating code or test expectations.

## Linting & Formatting

Recommended tools:

```bash
pip install black flake8 isort
black .
flake8
```

## Deployment (production)

Production deployment depends on your hosting environment. Typical approach:

### Gunicorn + Nginx (Linux)

1. Install system packages and Python deps
2. Configure Gunicorn to serve the Django WSGI app:

```bash
gunicorn car_social_network.wsgi:application --bind 0.0.0.0:8000
```

3. Put Nginx in front to serve static files and proxy requests to Gunicorn.
4. Use `systemd` to run Gunicorn as a service.

### Docker (optional)

Create a `Dockerfile` and `docker-compose.yml` for local production-like runs. A minimal Docker workflow:

```bash
docker build -t car_social:latest .
docker run -e SECRET_KEY=... -p 8000:8000 car_social:latest
```

Include database service in `docker-compose.yml` for multi-container setups.

## Troubleshooting

- If migrations fail: confirm DB credentials and connectivity.
- If static files not found: check `STATIC_ROOT` and `collectstatic`.
- If email sending fails: verify settings in `emailsettings.py` and env vars.

## Contributing

Contributions are welcome. Suggested workflow:

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make changes and add tests
4. Run tests and linters
5. Open a pull request with a clear description

Please follow the project's code style and testing practices.

## License

Specify the project's license here (e.g., MIT). If no license file is present, add a `LICENSE` file to the repo and include the license name.

## Contact

For questions or help, open an issue in the repository or contact the maintainers.

---

This README is a starting point. Edit sections to reflect specific project details, dependency versions, deployment hosts, and any additional setup steps required by your environment.
