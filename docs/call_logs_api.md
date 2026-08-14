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

- Every POST is deduplicated by **`phone_number + called_by` only** (one record per contact per user).
- If a record already exists for that phone number by the same user → **no new row** is created. Instead `call_count` is incremented and the `called_at` is appended to `call_times` in IST format.
- First POST for a new number → new row with `call_count = 1`.
- `call_count` — total number of times any call to this number was synced.
- `call_times` — list of IST-formatted timestamps for each sync (e.g. `"11 Aug 2026, 02:00 PM"`).

---

## Cascade Delete

Deleting a `CallLog` record **automatically deletes** the linked `PhoneComment` record for the same phone number and user (via `CASCADE` FK on `PhoneComment.call_log`).

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
  "called_at":       "2026-08-11T08:30:00+05:30",
  "device_platform": "android"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | Dialed/received number |
| `call_type` | string | yes | `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | yes | Duration in seconds. `0` for missed/rejected |
| `called_at` | string (ISO 8601) | yes | Exact call timestamp from device |
| `device_platform` | string | yes | Always `"android"` |

**Response `201 Created` (new number):**
```json
{
  "id":             1,
  "phone_number":   "9876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-11T08:30:00+05:30",
  "device_platform": "android",
  "lead":           "abc-uuid",
  "lead_name":      "John Doe",
  "called_by":      "uuid",
  "called_by_name": "Ravi Kumar",
  "call_count":     1,
  "call_times":     ["11 Aug 2026, 02:00 PM"],
  "created_at":     "2026-08-11T08:31:00+05:30"
}
```

**Response `200 OK` (same phone number, already exists):**
```json
{
  "id":             1,
  "phone_number":   "9876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-12T10:00:00+05:30",
  "device_platform": "android",
  "lead":           "abc-uuid",
  "lead_name":      "John Doe",
  "called_by":      "uuid",
  "called_by_name": "Ravi Kumar",
  "call_count":     2,
  "call_times":     [
    "11 Aug 2026, 02:00 PM",
    "12 Aug 2026, 10:00 AM"
  ],
  "created_at":     "2026-08-11T08:31:00+05:30"
}
```

---

### 2. List Call Logs

**`GET /api/lead/call-logs/`**

Agents see only their own logs. Superusers see all.

**Query Parameters:**

| Param | Type | Required | Description | Example |
|---|---|---|---|---|
| `phone_number` | string | no | Filter by exact phone number | `9876543210` |
| `call_type` | string | no | Filter by call type | `outgoing` |
| `device_platform` | string | no | Filter by platform | `android` |
| `from_date` | YYYY-MM-DD | no | Filter calls from this date (inclusive) | `2026-08-01` |
| `to_date` | YYYY-MM-DD | no | Filter calls up to this date (inclusive) | `2026-08-11` |
| `ordering` | string | no | Sort field. Prefix `-` for descending | `-called_at` |
| `page` | integer | no | Page number (default: `1`) | `2` |
| `page_size` | integer | no | Records per page | `20` |

**Available `ordering` values:**
- `called_at` / `-called_at` ← default desc
- `duration_secs` / `-duration_secs`
- `created_at` / `-created_at`

**Response `200 OK`:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id":             1,
      "phone_number":   "9876543210",
      "call_type":      "outgoing",
      "duration_secs":  65,
      "called_at":      "2026-08-11T08:30:00+05:30",
      "device_platform": "android",
      "lead":           "abc-uuid",
      "lead_name":      "John Doe",
      "called_by":      "uuid",
      "called_by_name": "Ravi Kumar",
      "call_count":     2,
      "call_times":     [
        "11 Aug 2026, 02:00 PM",
        "12 Aug 2026, 10:00 AM"
      ],
      "created_at":     "2026-08-11T08:31:00+05:30"
    }
  ]
}
```

---

### 3. Get a Single Call Log

**`GET /api/lead/call-logs/{id}/`**

Returns full record including `call_count` and `call_times`.

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

### 5. Delete a Call Log

**`DELETE /api/lead/call-logs/{id}/`**

Permanently deletes the call log. **Also deletes the linked `PhoneComment`** for the same phone number and user automatically.

**Response `204 No Content`**

---

### 6. Call Count Summary per Phone Number

**`GET /api/lead/call-logs/summary/`**

Returns total call count per phone number for the authenticated user.

**Query Parameters:**

| Param | Type | Required | Description | Example |
|---|---|---|---|---|
| `phone_number` | string | no | Filter to a specific number | `9876543210` |

**Response `200 OK`:**
```json
{
  "count": 2,
  "results": [
    {
      "phone_number":   "9876543210",
      "call_count":     5,
      "last_called_at": "2026-08-11T10:00:00+05:30"
    },
    {
      "phone_number":   "9123456789",
      "call_count":     2,
      "last_called_at": "2026-08-10T14:00:00+05:30"
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
| `called_at` | string (ISO 8601 IST) | no | Timestamp of the call |
| `device_platform` | string | no | Always `android` |
| `lead` | UUID | yes | Auto-matched lead ID |
| `lead_name` | string | yes | Matched lead name |
| `called_by` | UUID | no | Authenticated user ID |
| `called_by_name` | string | no | Full name or username |
| `call_count` | integer | no | Total syncs for this phone number (starts at 1) |
| `call_times` | array | no | IST-formatted timestamps of each sync e.g. `"14 Aug 2026, 02:00 PM"` |
| `created_at` | string (ISO 8601 IST) | no | When first created in CRM |

---

## Key Behaviours

1. **Dedup by phone number** — one record per phone per user, regardless of `called_at`. Multiple syncs increment `call_count` and append to `call_times`.
2. **Auto-match lead** — matches `Lead.mobile` and `Lead.alternate_number`. `lead` is `null` if no match.
3. **`called_by` is server-side** — set from authenticated user, never from request body.
4. **`call_times` in IST** — each entry is formatted as `"14 Aug 2026, 02:00 PM"`.
5. **Visibility** — agents see only their own logs. Superusers see all.
6. **Cascade delete** — deleting a `CallLog` automatically deletes the linked `PhoneComment`.

---

## DB Indexes

| Index | Type | Purpose |
|---|---|---|
| `phone_number` | Single | Filter by number |
| `called_at` | Single | Order by time |
| `(phone_number, called_by)` | Composite | Primary dedup + lookup query |

---

## Error Responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Missing required fields |
| `401 Unauthorized` | Missing or expired token |
| `404 Not Found` | Record not found or not accessible |
