# Call Logs API — Backend Implementation Spec

## Base URL
```
http://<server>:8000/api/
```

---

## Overview

The Call Logs API allows Android mobile apps to sync phone call records to the CRM.
Each call log is automatically matched to a Lead by phone number.

### Duplicate Handling
- If the **same call** is synced again (same `phone_number` + `called_at` + same user), **no new record is created** — instead the existing record's `call_count` is incremented.
- If the **same number is called again** at a different time (`called_at` differs), a **new record** is created with `call_count = 1`.
- `call_count` tracks how many times a duplicate sync was received for the same call.

---

## Authentication

Include the access token in every request:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Endpoint 1 — Sync a Call Log Entry

**`POST /api/lead/call-logs/`**

**Auth:** Bearer token

**Request Body (JSON):**
```json
{
  "phone_number":    "+919876543210",
  "call_type":       "outgoing",
  "duration_secs":   65,
  "called_at":       "2026-08-11T08:30:00.000Z",
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
| `device_platform` | string | yes | Always `"android"` from mobile |

**Response `201 Created` (new call):**
```json
{
  "id":             1,
  "phone_number":   "+919876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-11T08:30:00.000Z",
  "device_platform":"android",
  "lead":           "abc-uuid",
  "lead_name":      "John Doe",
  "called_by":      42,
  "called_by_name": "Ravi Kumar",
  "call_count":     1,
  "created_at":     "2026-08-11T08:31:00.000Z"
}
```

**Response `200 OK` (duplicate — same phone + called_at + user):**

Returns the same shape as above with `call_count` incremented:
```json
{
  "id":             1,
  "phone_number":   "+919876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-11T08:30:00.000Z",
  "device_platform":"android",
  "lead":           "abc-uuid",
  "lead_name":      "John Doe",
  "called_by":      42,
  "called_by_name": "Ravi Kumar",
  "call_count":     2,
  "created_at":     "2026-08-11T08:31:00.000Z"
}
```

---

### Endpoint 2 — Get Call History for a Phone Number

**`GET /api/lead/call-logs/?phone_number=+919876543210&page_size=10`**

**Auth:** Bearer token

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | no | Filter logs by this number |
| `page_size` | integer | no | Default `10`, max `100` |

**Response `200 OK`:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id":             2,
      "phone_number":   "+919876543210",
      "call_type":      "outgoing",
      "duration_secs":  65,
      "called_at":      "2026-08-11T08:30:00.000Z",
      "device_platform":"android",
      "lead":           "abc-uuid",
      "lead_name":      "John Doe",
      "called_by":      42,
      "called_by_name": "Ravi Kumar",
      "call_count":     3,
      "created_at":     "2026-08-11T08:31:00.000Z"
    },
    {
      "id":             1,
      "phone_number":   "+919876543210",
      "call_type":      "missed",
      "duration_secs":  0,
      "called_at":      "2026-08-10T14:15:00.000Z",
      "device_platform":"android",
      "lead":           "abc-uuid",
      "lead_name":      "John Doe",
      "called_by":      42,
      "called_by_name": "Ravi Kumar",
      "call_count":     1,
      "created_at":     "2026-08-10T14:16:00.000Z"
    }
  ]
}
```

> Results ordered by `called_at` descending (most recent first).

---

### Endpoint 3 — Get a Single Call Log Record

**`GET /api/lead/call-logs/{id}/`**

**Auth:** Bearer token

**Response `200 OK`:** Same shape as above including `call_count`.

---

### Endpoint 4 — Update a Call Log Record

**`PATCH /api/lead/call-logs/{id}/`**

**Auth:** Bearer token

**Request Body (JSON) — all fields optional:**
```json
{
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-11T08:30:00.000Z"
}
```

**Response `200 OK`:** Returns the full updated record.

---

### Endpoint 5 — Call Count Summary per Phone Number

**`GET /api/lead/call-logs/summary/`**

**Auth:** Bearer token

Returns the total number of distinct call records per phone number (not `call_count` — this counts actual separate calls).

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | no | Filter to a specific number |

**Response `200 OK`:**
```json
{
  "count": 2,
  "results": [
    {
      "phone_number":   "+919876543210",
      "call_count":     5,
      "last_called_at": "2026-08-11T08:30:00.000Z"
    },
    {
      "phone_number":   "+919123456789",
      "call_count":     2,
      "last_called_at": "2026-08-10T11:00:00.000Z"
    }
  ]
}
```

---

## Response Fields Reference

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | integer | no | Record ID |
| `phone_number` | string | no | The phone number of the call |
| `call_type` | string | no | `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | no | Duration in seconds (`0` for missed/rejected) |
| `called_at` | string (ISO 8601) | no | Timestamp of the call |
| `device_platform` | string | no | Always `android` |
| `lead` | string (UUID) | yes | Auto-matched lead ID (`null` if no match) |
| `lead_name` | string | yes | Matched lead's name (`null` if no match) |
| `called_by` | integer | no | ID of the authenticated user |
| `called_by_name` | string | no | Full name or username of the caller |
| `call_count` | integer | no | How many times this exact call was synced (starts at 1, increments on duplicate sync) |
| `created_at` | string (ISO 8601) | no | When the record was first created in the CRM |

---

## Call Type Values

| Value | Description |
|---|---|
| `outgoing` | Call made by the agent |
| `incoming` | Call received by the agent |
| `missed` | Incoming call not answered |
| `rejected` | Call actively rejected |
| `unknown` | Type could not be determined |

---

## Key Behaviours

1. **Auto-match lead** — on `POST`, server searches `Lead.mobile` and `Lead.alternate_number` for a match. If found, `lead` FK is auto-set. If not found, `lead` is `null` — request still succeeds.

2. **`called_by` is server-side** — always set from the authenticated user. Never accepted from the request body.

3. **Duplicate sync handling** — if the same `phone_number + called_at + called_by` already exists, the existing record's `call_count` is incremented and returned with `200 OK`. No new row is created.

4. **Different call = new record** — if `called_at` differs (even for the same phone number), a new row is created with `call_count = 1`.

5. **Visibility** — agents see only their own call logs. Superusers and staff see all logs.

6. **No DELETE** — call logs cannot be deleted via the API.

---

## DB Model

```python
class CallLog(models.Model):
    CALL_TYPE_CHOICES = [
        ('outgoing', 'Outgoing'),
        ('incoming', 'Incoming'),
        ('missed',   'Missed'),
        ('rejected', 'Rejected'),
        ('unknown',  'Unknown'),
    ]

    phone_number    = models.CharField(max_length=20, db_index=True)
    call_type       = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES)
    duration_secs   = models.PositiveIntegerField(default=0)
    called_at       = models.DateTimeField(db_index=True)
    device_platform = models.CharField(max_length=10, default='android')
    called_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    lead            = models.ForeignKey('Lead', on_delete=models.SET_NULL, null=True, blank=True)
    call_count      = models.PositiveIntegerField(default=1)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-called_at']
```

**DB Table:** `Lead_calllog`

---

## Error Responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Missing required fields or invalid values |
| `401 Unauthorized` | Missing or invalid Bearer token |
| `404 Not Found` | Record does not exist or not accessible |

**Example 401:**
```json
{
  "detail": "Token has expired"
}
```
