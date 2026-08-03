# Call Logs API — Documentation

## Overview

The Call Logs API allows Android mobile apps to sync phone call records to the CRM.
Each call log is automatically matched to a Lead by phone number.

**Base URL:** `http://<server>:8000/api/lead/call-logs/`

**Authentication:** Bearer token (JWT) required on all endpoints.

---

## Authentication

Include the access token in every request header:

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. Sync a Call Log

**`POST /api/lead/call-logs/`**

Syncs a single call record from the device. Auto-matches to a Lead by phone number.
If the same record already exists (same phone + timestamp + user), returns the existing record with `200` instead of creating a duplicate.

**Request Body:**

```json
{
  "phone_number":    "+919876543210",
  "call_type":       "outgoing",
  "duration_secs":   65,
  "called_at":       "2026-08-03T08:30:00.000Z",
  "device_platform": "android"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | Dialed/received number (digits + optional leading `+`) |
| `call_type` | string | yes | One of: `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | yes | Call duration in seconds. `0` for missed/rejected |
| `called_at` | string (ISO 8601 UTC) | yes | Exact timestamp of the call from the device |
| `device_platform` | string | yes | Always `"android"` (iOS does not sync) |

**Response `201 Created` (new record):**

```json
{
  "id":             1,
  "phone_number":   "+919876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-03T08:30:00.000Z",
  "device_platform":"android",
  "lead":           "abc123",
  "lead_name":      "John Doe",
  "called_by":      42,
  "called_by_name": "Ravi Kumar",
  "created_at":     "2026-08-03T08:31:00.000Z"
}
```

**Response `200 OK` (duplicate — record already exists):**

Returns the same shape as above with the existing record's data.

---

### 2. List Call Logs

**`GET /api/lead/call-logs/`**

Returns call logs for the authenticated user. Superusers/managers see all logs.

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | no | Filter by phone number |
| `page` | integer | no | Page number (default: 1) |
| `page_size` | integer | no | Records per page (default: 10, max: 100) |

**Example:**
```
GET /api/lead/call-logs/?phone_number=+919876543210&page_size=10
```

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
      "called_at":      "2026-08-03T08:30:00.000Z",
      "device_platform":"android",
      "lead":           "abc123",
      "lead_name":      "John Doe",
      "called_by":      42,
      "called_by_name": "Ravi Kumar",
      "created_at":     "2026-08-03T08:31:00.000Z"
    },
    {
      "id":             1,
      "phone_number":   "+919876543210",
      "call_type":      "missed",
      "duration_secs":  0,
      "called_at":      "2026-08-02T14:15:00.000Z",
      "device_platform":"android",
      "lead":           "abc123",
      "lead_name":      "John Doe",
      "called_by":      42,
      "called_by_name": "Ravi Kumar",
      "created_at":     "2026-08-02T14:16:00.000Z"
    }
  ]
}
```

> Results are ordered by `called_at` descending (most recent first).

---

### 3. Get a Single Call Log

**`GET /api/lead/call-logs/{id}/`**

**Response `200 OK`:**

```json
{
  "id":             1,
  "phone_number":   "+919876543210",
  "call_type":      "outgoing",
  "duration_secs":  65,
  "called_at":      "2026-08-03T08:30:00.000Z",
  "device_platform":"android",
  "lead":           "abc123",
  "lead_name":      "John Doe",
  "called_by":      42,
  "called_by_name": "Ravi Kumar",
  "created_at":     "2026-08-03T08:31:00.000Z"
}
```

**Response `404 Not Found`:** If the record does not exist or belongs to another user.

---

### 4. Update a Call Log

**`PATCH /api/lead/call-logs/{id}/`**

Update specific fields of an existing call log. All fields are optional.

**Request Body:**

```json
{
  "call_type":     "outgoing",
  "duration_secs": 120,
  "called_at":     "2026-08-03T08:30:00.000Z"
}
```

**Response `200 OK`:** Returns the full updated record (same shape as endpoint 3).

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
| `called_by` | integer | no | ID of the authenticated user who made/received the call |
| `called_by_name` | string | no | Full name or username of the caller |
| `created_at` | string (ISO 8601) | no | Timestamp when the record was created in the CRM |

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

1. **Auto-match lead** — on `POST`, the server searches for a Lead with a matching `mobile` or `alternate_number`. If found, the `lead` FK is set automatically. If not found, `lead` is `null` — the request still succeeds.

2. **`called_by` is server-side** — always set from the authenticated user. Never accepted from the request body.

3. **Duplicate guard** — if a record with the same `phone_number` + `called_at` + `called_by` already exists, the existing record is returned with `200 OK` instead of creating a duplicate.

4. **Visibility** — agents see only their own call logs. Superusers and staff see all logs.

5. **No DELETE** — call logs cannot be deleted via the API.

---

## Error Responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Missing required fields or invalid values |
| `401 Unauthorized` | Missing or invalid Bearer token |
| `404 Not Found` | Record does not exist or not accessible |

**Example 400:**
```json
{
  "call_type": ["This field is required."],
  "called_at": ["This field is required."]
}
```

**Example 401:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```
