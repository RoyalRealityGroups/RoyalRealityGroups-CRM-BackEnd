# User soft-delete (`is_deleted`) — implementation notes

## Summary
Added a permanent, terminal soft-delete for users, distinct from the existing
reversible `is_active` login pause. `is_active` semantics are unchanged.

## Backend (RoyalRealityGroups-CRM-BackEnd)
- `Users/models.py`
  - Added `is_deleted = BooleanField(default=False, db_index=True)` to `Users.User`.
  - Overrode the inherited `CoreUser.username` to drop DB-level `unique=True`
    (kept `db_index=True`).
- `Users/migrations/0003_user_is_deleted_alter_user_username.py` (new) — adds
  `is_deleted` and alters `username` to non-unique.
- `BaseProject/settings.py` — `SILENCED_SYSTEM_CHECKS = ['auth.W004']` (username
  no longer DB-unique; custom auth backends resolve among non-deleted rows).
- `Users/views.py` — `UserDetails.destroy` now ALWAYS soft-deletes: sets
  `is_deleted=True` + `is_active=False`, purges `JwtToken` rows, blanks `Device`
  tokens, returns `{status: "deleted"}`. Removed the hard-delete branch. Kept the
  "cannot delete yourself" guard. Added `is_deleted=False` to every user
  queryset (UserList, UserCreate, UserDetails, UserMini*, ReportingManager,
  ForceLogout, ApplyTemplate, UserPermissionView, Employee* views).
- `Users/serializers.py` — username/email uniqueness + `_generate_username`
  collision check now filter `is_deleted=False`; `reporting_manager` queryset
  excludes deleted; `is_deleted` exposed read-only on `UserSerializer`.
- `Core/Core/authentication/Authentication.py` — per-request `JWTAuthentication`
  rejects `is_deleted` (and `is_active=False`) users; credential backend resolves
  only non-deleted users.
- `Core/Users/serializers.py` — LoginSerializer blocks login for deleted users;
  validation serializers (username/email/phone, IamUser, ValidateUsername) and
  group user listing filter non-deleted.
- `Core/Users/views.py` — UserActive / UserInActive return 404 on a deleted user;
  forgot/reset-password lookups exclude deleted.

## Username-uniqueness approach (as required by task item 4)
Chose to **drop the DB `unique=True` on username** and enforce uniqueness among
non-deleted users purely in serializer/validation logic. Rationale: production is
PostgreSQL and tests are sqlite, so a partial unique constraint would need to be
portable across both; dropping the DB constraint is simplest and fully portable,
and lets a deleted user's username/email/phone be reused.

## Tests — `Users/tests.py`
(a) delete sets `is_deleted`, keeps row + related Lead/Booking; (b) reuse of a
deleted user's username/email/phone; (c) deleted users absent from list + 404 on
direct GET; (d) login + per-request JWT auth reject a deleted user.

## Frontend (RoyalRealityGroups-CRM-FrontEnd)
- `src/pages/settings/UserList.tsx` — removed the "deactivate before delete"
  guard (delete now also deactivates), terminal-delete confirm wording, success
  toast on completion.
- `src/api/users.api.ts` — added `is_deleted?` to `UserDetail`; updated comments.
- No undelete UI exposed.

## Verification run
- Backend: `manage.py makemigrations --check --dry-run` → "No changes detected".
- Backend: `manage.py check` → no issues (1 silenced: auth.W004).
- Backend: migrations apply cleanly and 9 tests pass against a PostgreSQL test DB.
  NOTE: the project's default test config uses sqlite, but `Core.Users`
  migration 0001 uses a PostgreSQL `ArrayField`, so the sqlite test DB cannot be
  built (pre-existing, unrelated to this change). Migration 0003 itself applies
  OK on sqlite. Tests were run against a real postgres test DB
  (`test_rrg_softdelete`) via a throwaway settings module (not committed).
- Frontend: `npx tsc -b` → no errors; `npm run build` → built OK.
