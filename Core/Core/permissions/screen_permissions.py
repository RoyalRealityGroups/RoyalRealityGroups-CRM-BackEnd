"""
Screen-level permission enforcement for RRGMS.

Maps API URL prefixes to Screen codes, and uses Django's built-in
group permissions (from import_menu_data) to check whether the user
can perform the requested action.

This replaces AllPermissions with a screen-aware approach that maps
HTTP methods to the standard Django permission codenames
(view_X, add_X, change_X, delete_X) for each screen's model.
"""
from rest_framework.permissions import BasePermission


# Map URL path prefixes to the Django app_label.model used for permission checking.
# Format: prefix -> (app_label, model_name)
# The permission codename will be: {action}_{model_name}
# e.g. POST /api/lead/leads/ -> checks Lead.add_lead
URL_TO_PERMISSION_MODEL = {
    '/api/lead/followups/reminders/': None,  # exempt
    '/api/lead/leads/choices/': None,  # exempt
    '/api/lead/followups/': ('Lead', 'leadfollowup'),
    '/api/lead/leads/cross_check/': ('Lead', 'lead'),
    '/api/lead/leads/export/': ('Lead', 'lead'),  # export uses export_ perm
    '/api/lead/': ('Lead', 'lead'),
    '/api/sitevisit/': ('SiteVisit', 'sitevisit'),
    '/api/masters/projects/': ('Masters', 'project'),
    '/api/projects/': ('Masters', 'project'),
    '/api/inventory/plots/': ('Inventory', 'plotinventory'),
    '/api/inventory/flats/': ('Inventory', 'flatinventory'),
    '/api/inventory/': ('Inventory', 'plotinventory'),
    '/api/booking/bookings/choices/': None,  # exempt
    '/api/booking/': ('Booking', 'booking'),
    '/api/documents/': ('Documents', 'document'),
    '/api/re-reports/': None,  # exempt — reports
    '/api/dashboards/': None,  # exempt — dashboards
    '/api/usermanagement/dropdowns/': None,  # exempt
    '/api/usermanagement/my-permissions/': None,  # exempt
    '/api/usermanagement/': ('Users', 'user'),
    '/api/masters/countries/': ('Masters', 'country'),
    '/api/masters/states/': ('Masters', 'state'),
    '/api/masters/cities/': ('Masters', 'city'),
    '/api/masters/area/': ('Masters', 'area'),
    '/api/masters/company/': ('Masters', 'company'),
    '/api/masters/location/': ('Masters', 'location'),
    '/api/masters/warehouses/': ('Masters', 'warehouse'),
    '/api/masters/uom/': ('Masters', 'uom'),
    '/api/masters/categories/': ('Masters', 'category'),
    '/api/masters/brands/': ('Masters', 'brand'),
    '/api/masters/tax/': ('Masters', 'tax'),
    '/api/masters/items/': ('Masters', 'item'),
    '/api/masters/item-tax-composition/': ('Masters', 'itemtaxcomposition'),
    '/api/masters/outlet-types/': ('Masters', 'outlettype'),
    '/api/masters/superstockist/': ('Masters', 'superstockist'),
    '/api/masters/distributor/': ('Masters', 'distributor'),
    '/api/masters/retailer/': ('Masters', 'retailer'),
    '/api/masters/route/': ('Masters', 'route'),
    '/api/masters/': ('Masters', 'project'),  # fallback for other masters
}

# Map HTTP methods to Django permission action prefix
METHOD_TO_PERM_ACTION = {
    'GET': 'view',
    'HEAD': 'view',
    'OPTIONS': 'view',
    'POST': 'add',
    'PUT': 'change',
    'PATCH': 'change',
    'DELETE': 'delete',
}

# URL prefixes that skip permission checks entirely
EXEMPT_PREFIXES = (
    '/api/users/',        # Auth (login, logout, token refresh)
    '/api/system/',       # System config, menu
    '/api/reports/',      # Import/export framework
    '/api/general/',      # General settings
    '/api/thirdparty/',   # Focus ERP
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

        # None means explicitly exempt
        # (already handled above but also in the map for specific sub-URLs)

        app_label, model_name = perm_model

        # Determine action
        action = METHOD_TO_PERM_ACTION.get(request.method, 'view')

        # Build permission string: e.g. "Lead.view_lead", "Masters.add_project"
        perm_codename = f"{app_label}.{action}_{model_name}"

        return user.has_perm(perm_codename)
