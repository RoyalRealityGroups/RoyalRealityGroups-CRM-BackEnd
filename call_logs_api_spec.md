# Call Logs API — Backend Implementation Spec

## Base URL
```
http://16.113.17.48:8000/api/
```

---

## Endpoint 1 — Sync a Call Log Entry

**`POST /api/lead/call-logs/`**

**Auth:** Bearer token

**Request Body (JSON):**
```json
{
  "phone_number":    "+919876543210",
  "call_type":       "outgoing",
  "duration_secs":   65,
  "called_at":       "2025-07-10T08:30:00.000Z",
  "device_platform": "android"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | Dialed/received number (digits + optional leading `+`) |
| `call_type` | string (enum) | yes | One of: `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | yes | Call duration in seconds. `0` for missed/rejected |
| `called_at` | string (ISO 8601 UTC) | yes | Exact timestamp of the call from device |
| `device_platform` | string | yes | Always `"android"` from mobile (iOS does not sync) |

**Response `201 Created`:**
```json
{
  "id":             "123",
  "phone_number":   "+919876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2025-07-10T08:30:00.000Z",
  "lead":           "456",
  "lead_name":      "John Doe",
  "called_by_name": "Agent Name"
}
```

**Response Fields:**

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | string/int | no | Record ID |
| `phone_number` | string | no | Same as request |
| `call_type` | string | no | Same as request |
| `duration_secs` | integer | no | Same as request |
| `called_at` | string (ISO 8601) | no | Same as request |
| `lead` | string/int | yes | Auto-matched lead ID by phone number (null if no match) |
| `lead_name` | string | yes | Matched lead's name (null if no match) |
| `called_by_name` | string | no | Full name of the authenticated user |

---

## Endpoint 2 — Get Call History for a Phone Number

**`GET /api/lead/call-logs/?phone_number=+919876543210&page_size=10`**

**Auth:** Bearer token

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | Filter logs by this number |
| `page_size` | integer | no | Default `10`, max suggested `50` |

**Response `200 OK`:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id":             "123",
      "phone_number":   "+919876543210",
      "call_type":      "outgoing",
      "duration_secs":  65,
      "called_at":      "2025-07-10T08:30:00.000Z",
      "lead":           "456",
      "lead_name":      "John Doe",
      "called_by_name": "Agent Name"
    },
    {
      "id":             "120",
      "phone_number":   "+919876543210",
      "call_type":      "missed",
      "duration_secs":  0,
      "called_at":      "2025-07-09T14:15:00.000Z",
      "lead":           "456",
      "lead_name":      "John Doe",
      "called_by_name": "Agent Name"
    }
  ]
}
```

> Results must be ordered by `called_at` descending (most recent first).

---

## Endpoint 3 — Get a Single Call Log Record

**`GET /api/lead/call-logs/{id}/`**

**Auth:** Bearer token

**Response `200 OK`:**
```json
{
  "id":             "123",
  "phone_number":   "+919876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2025-07-10T08:30:00.000Z",
  "lead":           "456",
  "lead_name":      "John Doe",
  "called_by_name": "Agent Name"
}
```

---

## Endpoint 4 — Update a Call Log Record

**`PATCH /api/lead/call-logs/{id}/`**

**Auth:** Bearer token

**Request Body (JSON) — all fields optional:**
```json
{
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2025-07-10T08:30:00.000Z"
}
```

**Response `200 OK`:** Returns the full updated record (same shape as Endpoint 3).

---

## URL Registration

Add to `lead/urls.py`:

```python
from rest_framework.routers import DefaultRouter
from .views import CallLogViewSet

router = DefaultRouter()
router.register(r'call-logs', CallLogViewSet, basename='call-log')
```

This registers all four endpoints above automatically.

---

## Django Model

```python
class CallLog(models.Model):
    CALL_TYPE_CHOICES = [
        ('outgoing', 'Outgoing'),
        ('incoming', 'Incoming'),
        ('missed',   'Missed'),
        ('rejected', 'Rejected'),
        ('unknown',  'Unknown'),
    ]

    phone_number     = models.CharField(max_length=20)
    call_type        = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES)
    duration_secs    = models.PositiveIntegerField(default=0)
    called_at        = models.DateTimeField()
    device_platform  = models.CharField(max_length=10, default='android')
    called_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    lead             = models.ForeignKey('Lead', on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-called_at']
```

---

## Key Backend Behaviors

1. **Auto-match lead** — on `POST`, look up `Lead` by `phone_number` and auto-assign the `lead` FK if found. Do not fail if no match found, just leave `lead` as null.
2. **`called_by`** — always set from `request.user` on the server side, never accepted from the request body.
3. **`called_by_name`** — read-only serializer field returning `called_by.get_full_name()` or `called_by.username`.
4. **`lead_name`** — read-only serializer field returning the matched lead's name, null if no lead matched.
5. **Duplicate guard** — if a record with the same `phone_number` + `called_at` + `called_by` already exists, return the existing record with `200` instead of creating a duplicate.
6. **Permissions** — authenticated users only. Agents see only their own logs; superusers/managers see all (follow the same permission pattern used in `lead/leads/`).
