"""
Screen-level permission enforcement for RRGMS.

Maps API URL prefixes to Menuitem codes, then queries the UserPermission
table to decide if the user can perform the requested action.

Superusers bypass all checks.
Exempt prefixes always pass through.
"""
from rest_framework.permissions import BasePermission


# URL prefix → Menuitem.code  (longer prefix wins)
# These codes should match the 'code' field in System.Menuitem table
URL_TO_MENUITEM_CODE = {
    '/api/lead/followups/reminders/':       None,           # exempt
    '/api/lead/leads/choices/':             None,           # exempt
    '/api/lead/call-logs/':                 None,           # exempt
    '/api/lead/phone-comments/':            None,           # exempt
    '/api/lead/followups/':                 'FOLLOWUP',
    '/api/lead/leads/cross_check/':         'CROSS_LEAD',
    '/api/lead/leads/export/':              'LEAD',
    '/api/lead/':                           'LEAD',

    '/api/sitevisit/':                      'SITE_VISIT',
    '/api/projects/':                       'PROJECT',

    '/api/inventory/':                      'INVENTORY',
    '/api/availability/projects/choices/':  None,           # exempt
    '/api/availability/':                   'INVENTORY',

    '/api/booking/bookings/choices/':       None,           # exempt
    '/api/booking/':                        'BOOKING',

    '/api/documents/':                      'DOCUMENT',
    '/api/re-reports/':                     'REPORTS',
    '/api/dashboards/':                     'DASHBOARD',
    '/api/usermanagement/':                 'USER_PERMISSION',
}

METHOD_TO_ACTION = {
    'GET':     'view',
    'HEAD':    'view',
    'OPTIONS': 'view',
    'POST':    'add',
    'PUT':     'edit',
    'PATCH':   'edit',
    'DELETE':  'delete',
}

EXEMPT_PREFIXES = (
    '/api/users/',
    '/api/system/',
    '/api/reports/',
    '/api/general/',
    '/api/usermanagement/dropdowns/',
    '/api/usermanagement/my-permissions/',
)


class ScreenPermission(BasePermission):
    """
    Checks the UserPermission table on every API request.

    Flow:
    1. Superusers → always allowed.
    2. Exempt prefix → allowed.
    3. URL matched to Menuitem code → check UserPermission row.
       - Row found and flag is True → allowed.
       - Row missing or flag False  → denied.
    4. No URL match → allowed (fail-open for unmapped endpoints).
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
            path += '/'

        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True

        # Find longest matching prefix
        menuitem_code = None
        matched_len = 0
        for prefix, code in URL_TO_MENUITEM_CODE.items():
            if path.startswith(prefix) and len(prefix) > matched_len:
                menuitem_code = code
                matched_len = len(prefix)

        if matched_len == 0:
            return True   # no mapping — allow

        if menuitem_code is None:
            return True   # explicitly exempted

        action = METHOD_TO_ACTION.get(request.method, 'view')

        try:
            from Users.models import UserPermission
            # Check permission via Menuitem code
            perm = UserPermission.objects.filter(
                user=user, 
                menuitem__code=menuitem_code
            ).select_related('menuitem').first()

            if perm is None:
                self.message = f'You do not have permission to access this screen ({menuitem_code}).'
                return False

            if not perm.has_permission(action):
                self.message = f'You do not have {action} permission for this screen ({menuitem_code}).'
                return False
                
            return True
        except Exception as e:
            # Log the error but fail open so app doesn't break
            import logging
            logging.getLogger(__name__).error(f"ScreenPermission check failed: {e}")
            return True
