# Phone Comments API — Documentation

## Overview

Allows mobile app users to add notes/comments against a phone number (contact-level note).
One comment record per phone number per user. Posting again **updates** the existing comment
and appends the new comment to `comment_history`.

**Phone number must exist in the user's call logs** — you can only comment on numbers you have called.

**Base URL:** `http://<server>:8000/api/lead/phone-comments/`

**Authentication:** Bearer token (JWT) required on all endpoints.

**DB Table:** `Lead_phonecomment`

**Indexes:** `phone_number`, `(phone_number, commented_by)` composite + unique

---

## Authentication

```
Authorization: Bearer <access_token>
```

---

## Comment History

Every comment (including the first one) is stored in `comment_history` with its IST timestamp.
The `comment` field is **not returned** in any response — all history is in `comment_history`.

Example after 2 posts:
```json
{
  "comment_history": [
    { "comment": "First note — call back after 5pm", "time": "2026-08-11T10:00:00+05:30" },
    { "comment": "Budget revised to 50L",            "time": "2026-08-11T14:30:00+05:30" }
  ]
}
```

---

## Cascade Delete

`PhoneComment` is linked to `CallLog` via a FK (`call_log`). When the linked `CallLog` is deleted, this `PhoneComment` is **automatically deleted** (CASCADE).

---

## Endpoints

---

### 1. Create or Update a Comment

**`POST /api/lead/phone-comments/`**

Creates a new comment. If a comment already exists for this number by the same user,
the new comment is appended to `comment_history`.

**Validation:** `phone_number` must exist in the user's call logs (`/api/lead/call-logs/`).

**Request Body:**
```json
{
  "phone_number": "9876543210",
  "comment":      "Interested in 3BHK. Call back after 5pm."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | Must exist in your call logs |
| `comment` | string | yes | The note/comment text (write-only — not in response) |

**Response `201 Created` (new comment):**
```json
{
  "id":                1,
  "phone_number":      "9876543210",
  "comment_history": [
    {
      "comment": "Interested in 3BHK. Call back after 5pm.",
      "time":    "2026-08-11T10:00:00+05:30"
    }
  ],
  "lead":              "abc-uuid",
  "lead_name":         "John Doe",
  "commented_by":      "uuid",
  "commented_by_name": "Ravi Kumar",
  "created_at":        "2026-08-11T10:00:00+05:30",
  "updated_at":        "2026-08-11T10:00:00+05:30"
}
```

**Response `200 OK` (updated — new comment appended to history):**
```json
{
  "id":                1,
  "phone_number":      "9876543210",
  "comment_history": [
    {
      "comment": "Interested in 3BHK. Call back after 5pm.",
      "time":    "2026-08-11T10:00:00+05:30"
    },
    {
      "comment": "Budget revised to 50L. Very interested.",
      "time":    "2026-08-11T14:30:00+05:30"
    }
  ],
  "lead":              "abc-uuid",
  "lead_name":         "John Doe",
  "commented_by":      "uuid",
  "commented_by_name": "Ravi Kumar",
  "created_at":        "2026-08-11T10:00:00+05:30",
  "updated_at":        "2026-08-11T14:30:00+05:30"
}
```

**Response `400 Bad Request` (phone not in call logs):**
```json
{
  "phone_number": [
    "This phone number does not exist in your call logs. You can only comment on numbers you have called."
  ]
}
```

---

### 2. Get Comment for a Phone Number

**`GET /api/lead/phone-comments/?phone_number=9876543210`**

**Query Parameters:**

| Param | Type | Required | Description | Example |
|---|---|---|---|---|
| `phone_number` | string | no | Filter by exact phone number | `9876543210` |
| `from_date` | YYYY-MM-DD | no | Filter by `updated_at` from this date | `2026-08-01` |
| `to_date` | YYYY-MM-DD | no | Filter by `updated_at` up to this date | `2026-08-11` |
| `ordering` | string | no | Sort field. Prefix `-` for descending | `-updated_at` |
| `page` | integer | no | Page number (default: `1`) | `1` |
| `page_size` | integer | no | Records per page | `20` |

**Response `200 OK`:**
```json
{
  "count": 1,
  "results": [
    {
      "id":                1,
      "phone_number":      "9876543210",
      "comment_history": [
        { "comment": "Interested in 3BHK.", "time": "2026-08-11T10:00:00+05:30" }
      ],
      "lead":              "abc-uuid",
      "lead_name":         "John Doe",
      "commented_by":      "uuid",
      "commented_by_name": "Ravi Kumar",
      "created_at":        "2026-08-11T10:00:00+05:30",
      "updated_at":        "2026-08-11T10:00:00+05:30"
    }
  ]
}
```

> Returns `results: []` if no comment exists for that number.

---

### 3. List All My Comments

**`GET /api/lead/phone-comments/`**

Returns all comments by the authenticated user, ordered by most recently updated.
Supports same filters as Endpoint 2.

---

### 4. Get a Single Comment

**`GET /api/lead/phone-comments/{id}/`**

Returns the full record including full `comment_history`.

---

### 5. Update a Comment

**`PATCH /api/lead/phone-comments/{id}/`**

Appends new comment to `comment_history`.

**Request Body:**
```json
{
  "comment": "Confirmed budget of 60L. Site visit scheduled."
}
```

**Response `200 OK`:** Full updated record with updated `comment_history`.

---

### 6. Delete a Comment

**`DELETE /api/lead/phone-comments/{id}/`**

Permanently deletes the comment and its history.

**Response `204 No Content`**

---

## Response Fields Reference

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | integer | no | Record ID |
| `phone_number` | string | no | The phone number |
| `comment_history` | array | no | All comments with IST timestamps (newest last) |
| `lead` | UUID | yes | Auto-matched lead ID |
| `lead_name` | string | yes | Matched lead name |
| `commented_by` | UUID | no | User who wrote the comment |
| `commented_by_name` | string | no | Full name or username |
| `created_at` | string (ISO 8601 IST) | no | When first created |
| `updated_at` | string (ISO 8601 IST) | no | When last updated |

> **Note:** `comment` field is **write-only** — accepted in POST/PATCH request body but never returned in responses.

### `comment_history` item shape:
```json
{
  "comment": "Comment text",
  "time":    "2026-08-11T10:00:00+05:30"
}
```

---

## Key Behaviours

1. **Phone must be in call logs** — `phone_number` must exist in `CallLog` for the authenticated user. Returns `400` otherwise.
2. **Upsert on POST** — one record per phone per user. Each POST appends the new comment to `comment_history`.
3. **`comment` is write-only** — never returned in responses. All data is in `comment_history`.
4. **Timestamps in IST** — `time` in `comment_history` is ISO 8601 with `+05:30` offset.
5. **`commented_by` is server-side** — set from authenticated user, never from request body.
6. **Auto-match lead** — matches `Lead.mobile` and `Lead.alternate_number`. `null` if no match.
7. **Visibility** — users see only their own comments. Superusers see all.
8. **Auto-deleted with CallLog** — deleting the linked `CallLog` cascades and deletes this record.

---

## DB Indexes

| Index | Type | Purpose |
|---|---|---|
| `phone_number` | Single | Filter by number |
| `(phone_number, commented_by)` | Composite + Unique | Primary lookup, enforces one comment per user per number |

---

## Error Responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Missing fields or phone not in call logs |
| `401 Unauthorized` | Missing or expired token |
| `404 Not Found` | Record not found or not accessible |
