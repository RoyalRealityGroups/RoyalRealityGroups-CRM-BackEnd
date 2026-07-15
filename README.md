# Real Estate CRM — Backend

Django + Django REST Framework backend for the Real Estate CRM application.

## Tech Stack

- **Python 3.10**
- **Django** + **Django REST Framework**
- **uv** for Python package management
- **SQLite** (default) / **PostgreSQL** (recommended for production)
- **JWT** authentication via `djangorestframework-simplejwt`

## Prerequisites

- **Python 3.10** (managed via uv)
- **uv** package manager — install from https://docs.astral.sh/uv/

## Setup

### 1. Install Python 3.10

```bash
uv python install 3.10
```

### 2. Create virtual environment

```bash
uv venv venv --python 3.10
```

### 3. Activate virtual environment

**Linux / macOS:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Upgrade pip

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run database migrations

```bash
python manage.py migrate
```

### 7. Sync menu / permission fixtures

```bash
python manage.py UpdateContentTypeDetail
python manage.py UpdatePermissionDetail
python manage.py import_menu_data
```

These commands:
- `UpdateContentTypeDetail` — registers all Django app content types
- `UpdatePermissionDetail` — creates per-model permissions
- `import_menu_data` — imports sidebar menus from `Menu/` JSON fixtures

### 8. Create superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 9. Run development server

```bash
python manage.py runserver
```

API will be available at: **http://localhost:8000**

Admin panel: **http://localhost:8000/admin/**

## Project Structure

```
BE/
├── BaseProject/          # Django project settings, root urls, wsgi/asgi
├── Core/                 # Core modules (Users, System, Reports)
├── Users/                # User management app
├── Masters/              # Master data (products, projects, customers, etc.)
├── Sales/                # Sales orders, schemes
├── Lead/                 # Lead management + follow-ups
├── SiteVisit/            # Site visit management
├── Inventory/            # Plot and flat inventory
├── Dispatch/             # Dispatch workflows
├── Invoice/              # Invoicing
├── Receipts/             # Receipts
├── General/              # General settings
├── thirdparty/           # Third-party integrations
├── dashboards/           # Dashboard widgets
├── Media/                # JSON data fixtures
├── Menu/                 # Sidebar menu fixtures (JSON)
├── static_assets/        # Static files
├── .env                  # Environment variables (create this)
└── manage.py
```

## Environment Variables

Create a `.env` file in this folder with:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
URL_SCHEMA=http
GLOBAL_API_URL=http://localhost:8000
```

For production, set `DEBUG=False` and use a strong secret key.

## Common Tasks

### Create a new app

```bash
python manage.py startapp <app_name>
```

Then:
1. Add `<app_name>` to `INSTALLED_APPS` in `BaseProject/settings.py`
2. Add `path('api/<app_name>/', include('<app_name>.urls'))` to `BaseProject/urls.py`
3. Define models in `<app_name>/models.py`
4. Create serializers in `<app_name>/serializers.py`
5. Create viewsets in `<app_name>/views.py`
6. Register routes via DefaultRouter in `<app_name>/urls.py`

### Generate migrations after model changes

```bash
python manage.py makemigrations <app_name>
python manage.py migrate <app_name>
```

### Re-sync menu / permission fixtures

After adding new models or apps, run:

```bash
python manage.py UpdateContentTypeDetail
python manage.py UpdatePermissionDetail
python manage.py import_menu_data
```

### Update menu fixtures

Menu entries are stored in `Menu/submenu.json`, `Menu/menuitem.json`, etc. After editing JSON:

```bash
python manage.py import_menu_data
```

### Access Django admin

Visit http://localhost:8000/admin/ and log in with superuser credentials.

### Export menu data

```bash
python manage.py export_menu_data
```

Writes current menu state to `General/Data/` JSON files.

## API Endpoints

All endpoints are prefixed with `/api/`.

| Module | Endpoint |
|---|---|
| Lead | `/api/lead/leads/`, `/api/lead/followups/` |
| Site Visit | `/api/sitevisit/site-visits/` |
| Inventory | `/api/inventory/plots/`, `/api/inventory/flats/` |
| Sales | `/api/sales/orders/` |
| Masters | `/api/masters/` |
| Users | `/api/usermanagement/` |
| Reports | `/api/reports/` |

## Troubleshooting

### "No module named 'X'"

Reinstall dependencies:
```bash
pip install -r requirements.txt
```

### Migration conflicts

```bash
python manage.py makemigrations <app_name>
python manage.py migrate
```

If still broken, check for conflicting migrations in `<app>/migrations/`.

### Menu not appearing in sidebar

Run the three menu commands again:
```bash
python manage.py UpdateContentTypeDetail
python manage.py UpdatePermissionDetail
python manage.py import_menu_data
```

Then hard-refresh the browser (Ctrl+Shift+R).

### Permission denied errors

Ensure you're logged in as superuser OR the user has the required permission via their group.

## Need Help?

Refer to:
- `requirements.txt` for all Python dependencies
- `BaseProject/settings.py` for installed apps and middleware
- `Menu/` folder for menu JSON fixtures
- Frontend README at `../FE/README.md`
