# Call Logs API — Documentation

## Overview

The Call Logs API allows Android mobile apps to sync phone call records to the CRM.
Each call log is automatically matched to a Lead by phone number.

**Base URL:** `http://<server>:8000/api/lead/call-logs/`

**Authentication:** Bearer token (JWT) required on all endpoints.

**DB Table:** `Lead_calllog`

**Indexes:** `phone_number`, `called_at`, `(phone_number, called_by)` composite

---

## Authentication

```
Authorization: Bearer <access_token>
```

---

## Duplicate Handling & Call Count

- Every POST creates a new record **unless** the exact same call is synced again (same `phone_number` + `called_at` + same user).
- On an exact duplicate sync → **no new row** is created. Instead `call_count` is incremented and the `called_at` is appended to `call_times`.
- On a new call to the same number (different `called_at`) → new row with `call_count = 1`.
- `call_count` — how many times this exact call was synced.
- `call_times` — list of all timestamps when this call was synced (including duplicates).

---

## Endpoints

---

### 1. Sync a Call Log

**`POST /api/lead/call-logs/`**

**Request Body:**
```json
{
  "phone_number":    "9876543210",
  "call_type":       "outgoing",
  "duration_secs":   65,
  "called_at":       "2026-08-11T08:30:00.000Z",
  "device_platform": "android"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | Dialed/received number |
| `call_type` | string | yes | `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | yes | Duration in seconds. `0` for missed/rejected |
| `called_at` | string (ISO 8601 UTC) | yes | Exact call timestamp from device |
| `device_platform` | string | yes | Always `"android"` |

**Response `201 Created` (new call):**
```json
{
  "id":             1,
  "phone_number":   "9876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-11T08:30:00.000Z",
  "device_platform":"android",
  "lead":           "abc-uuid",
  "lead_name":      "John Doe",
  "called_by":      "uuid",
  "called_by_name": "Ravi Kumar",
  "call_count":     1,
  "call_times":     ["2026-08-11T08:30:00.000Z"],
  "created_at":     "2026-08-11T08:31:00.000Z"
}
```

**Response `200 OK` (duplicate sync — same phone + called_at + user):**
```json
{
  "id":             1,
  "phone_number":   "9876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-11T08:30:00.000Z",
  "device_platform":"android",
  "lead":           "abc-uuid",
  "lead_name":      "John Doe",
  "called_by":      "uuid",
  "called_by_name": "Ravi Kumar",
  "call_count":     2,
  "call_times":     [
    "2026-08-11T08:30:00.000Z",
    "2026-08-11T08:30:00.000Z"
  ],
  "created_at":     "2026-08-11T08:31:00.000Z"
}
```

---

### 2. List Call Logs

**`GET /api/lead/call-logs/`**

Agents see only their own logs. Superusers see all.

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `phone_number` | string | Filter by phone number |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Records per page (default: 10) |

**Response `200 OK`:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id":             2,
      "phone_number":   "9876543210",
      "call_type":      "outgoing",
      "duration_secs":  65,
      "called_at":      "2026-08-11T10:00:00.000Z",
      "device_platform":"android",
      "lead":           "abc-uuid",
      "lead_name":      "John Doe",
      "called_by":      "uuid",
      "called_by_name": "Ravi Kumar",
      "call_count":     3,
      "call_times":     [
        "2026-08-11T10:00:00.000Z",
        "2026-08-11T10:00:00.000Z",
        "2026-08-11T10:00:00.000Z"
      ],
      "created_at":     "2026-08-11T10:01:00.000Z"
    }
  ]
}
```

> Ordered by `called_at` descending (most recent first).

---

### 3. Get a Single Call Log

**`GET /api/lead/call-logs/{id}/`**

**Response `200 OK`:** Full record including `call_count` and `call_times`.

---

### 4. Update a Call Log

**`PATCH /api/lead/call-logs/{id}/`**

**Request Body (all optional):**
```json
{
  "call_type":     "incoming",
  "duration_secs": 120
}
```

**Response `200 OK`:** Full updated record.

---

### 5. Call Count Summary per Phone Number

**`GET /api/lead/call-logs/summary/`**

Returns total distinct call records per phone number.

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `phone_number` | string | Filter to a specific number |

**Response `200 OK`:**
```json
{
  "count": 2,
  "results": [
    {
      "phone_number":   "9876543210",
      "call_count":     5,
      "last_called_at": "2026-08-11T10:00:00.000Z"
    }
  ]
}
```

---

## Response Fields Reference

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | integer | no | Record ID |
| `phone_number` | string | no | The phone number |
| `call_type` | string | no | `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | no | Duration in seconds |
| `called_at` | string (ISO 8601) | no | Timestamp of the call |
| `device_platform` | string | no | Always `android` |
| `lead` | UUID | yes | Auto-matched lead ID |
| `lead_name` | string | yes | Matched lead name |
| `called_by` | UUID | no | Authenticated user ID |
| `called_by_name` | string | no | Full name or username |
| `call_count` | integer | no | Times this exact call was synced (starts at 1) |
| `call_times` | array | no | List of all sync timestamps for this call |
| `created_at` | string (ISO 8601) | no | When first created in CRM |

---

## Key Behaviours

1. **Auto-match lead** — matches `Lead.mobile` and `Lead.alternate_number`. `lead` is `null` if no match.
2. **`called_by` is server-side** — set from authenticated user, never from request body.
3. **Duplicate sync** — same `phone_number + called_at + called_by` → increments `call_count`, appends to `call_times`, returns `200 OK`.
4. **New call same number** — different `called_at` → new row with `call_count = 1`.
5. **Visibility** — agents see only their own logs. Superusers see all.
6. **No DELETE** — call logs cannot be deleted via API.

---

## DB Indexes

| Index | Type | Purpose |
|---|---|---|
| `phone_number` | Single | Filter by number |
| `called_at` | Single | Order by time |
| `(phone_number, called_by)` | Composite | Most common query |

---

## Error Responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Missing required fields |
| `401 Unauthorized` | Missing or expired token |
| `404 Not Found` | Record not found or not accessible |
