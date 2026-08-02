"""
Screen-level permission enforcement for RRGMS.

Maps API URL prefixes to Screen codes, and uses Django's built-in
group permissions (from import_menu_data) to check whether the user
can perform the requested action.
"""
from rest_framework.permissions import BasePermission


URL_TO_PERMISSION_MODEL = {
    # Lead Management
    '/api/lead/followups/reminders/': None,  # exempt
    '/api/lead/leads/choices/': None,        # exempt
    '/api/lead/followups/': ('Lead', 'leadfollowup'),
    '/api/lead/leads/cross_check/': ('Lead', 'lead'),
    '/api/lead/leads/export/': ('Lead', 'lead'),
    '/api/lead/': ('Lead', 'lead'),

    # Site Visit
    '/api/sitevisit/': ('SiteVisit', 'sitevisit'),

    # Project Management
    '/api/projects/': ('ProjectManagement', 'project'),

    # Inventory
    '/api/inventory/plots/': ('Inventory', 'plotinventory'),
    '/api/inventory/flats/': ('Inventory', 'flatinventory'),
    '/api/inventory/': ('Inventory', 'plotinventory'),

    # Booking
    '/api/booking/bookings/choices/': None,  # exempt
    '/api/booking/': ('Booking', 'booking'),

    # Documents
    '/api/documents/': ('Documents', 'document'),

    # Reports & Dashboards
    '/api/re-reports/': None,
    '/api/dashboards/': ('dashboards', 'dashboard'),

    # User Management
    '/api/usermanagement/': ('Users', 'user'),
}

METHOD_TO_PERM_ACTION = {
    'GET': 'view',
    'HEAD': 'view',
    'OPTIONS': 'view',
    'POST': 'add',
    'PUT': 'change',
    'PATCH': 'change',
    'DELETE': 'delete',
}

EXEMPT_PREFIXES = (
    '/api/users/',        # Auth (login, logout, token refresh)
    '/api/system/',       # System config, menu
    '/api/reports/',      # Import/export framework
    '/api/general/',      # General settings
    '/api/usermanagement/dropdowns/',       # Dropdowns needed by all screens
    '/api/usermanagement/my-permissions/',  # Needed for frontend permission checks
)


class ScreenPermission(BasePermission):
    """
    Enforces Django group permissions based on URL-to-model mapping.

    - Superusers bypass all checks.
    - Exempt URLs pass through.
    - For mapped URLs, checks user.has_perm('{app_label}.{action}_{model}')
    """

    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return True  # defer to IsAuthenticated

        if user.is_superuser:
            return True

        path = request.path
        if not path.endswith('/'):
            path = path + '/'

        # Check exempt prefixes first
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True

        # Find which permission model this URL maps to (check longer prefixes first)
        perm_model = None
        matched_prefix = ''
        for prefix, model_info in URL_TO_PERMISSION_MODEL.items():
            if path.startswith(prefix) and len(prefix) > len(matched_prefix):
                perm_model = model_info
                matched_prefix = prefix

        # No mapping found — allow (don't break unmapped endpoints)
        if perm_model is None:
            return True

        app_label, model_name = perm_model
        action = METHOD_TO_PERM_ACTION.get(request.method, 'view')
        perm_codename = f"{app_label}.{action}_{model_name}"

        return user.has_perm(perm_codename)
