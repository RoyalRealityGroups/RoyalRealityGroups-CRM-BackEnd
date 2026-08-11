# Phone Comments API — Documentation

## Overview

Allows mobile app users to add notes/comments against a phone number (contact-level note).
One comment record per phone number per user. Posting again **updates** the existing comment
and saves the old one to `comment_history`.

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

Every time a comment is updated, the **old comment is saved** to `comment_history` with its timestamp.

- `comment` → always the **latest** comment
- `comment_history` → all **previous** comments in order

Example after 3 updates:
```json
{
  "comment": "Very interested, finalizing soon",
  "comment_history": [
    { "comment": "First note — call back after 5pm", "commented_at": "2026-08-11T10:00:00Z" },
    { "comment": "Budget revised to 50L",            "commented_at": "2026-08-11T14:30:00Z" }
  ]
}
```

---

## Endpoints

---

### 1. Create or Update a Comment

**`POST /api/lead/phone-comments/`**

Creates a new comment. If a comment already exists for this number by the same user,
old comment is moved to `comment_history` and new comment becomes current.

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
| `comment` | string | yes | The note/comment text |

**Response `201 Created` (new comment):**
```json
{
  "id":                1,
  "phone_number":      "9876543210",
  "comment":           "Interested in 3BHK. Call back after 5pm.",
  "comment_history":   [],
  "lead":              "abc-uuid",
  "lead_name":         "John Doe",
  "commented_by":      "uuid",
  "commented_by_name": "Ravi Kumar",
  "created_at":        "2026-08-11T10:00:00.000Z",
  "updated_at":        "2026-08-11T10:00:00.000Z"
}
```

**Response `200 OK` (updated — previous comment saved to history):**
```json
{
  "id":                1,
  "phone_number":      "9876543210",
  "comment":           "Budget revised to 50L. Very interested.",
  "comment_history": [
    {
      "comment":      "Interested in 3BHK. Call back after 5pm.",
      "commented_at": "2026-08-11T10:00:00.000Z"
    }
  ],
  "lead":              "abc-uuid",
  "lead_name":         "John Doe",
  "commented_by":      "uuid",
  "commented_by_name": "Ravi Kumar",
  "created_at":        "2026-08-11T10:00:00.000Z",
  "updated_at":        "2026-08-11T14:30:00.000Z"
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

**Response `200 OK`:**
```json
{
  "count": 1,
  "results": [
    {
      "id":                1,
      "phone_number":      "9876543210",
      "comment":           "Interested in 3BHK. Call back after 5pm.",
      "comment_history":   [],
      "lead":              "abc-uuid",
      "lead_name":         "John Doe",
      "commented_by":      "uuid",
      "commented_by_name": "Ravi Kumar",
      "created_at":        "2026-08-11T10:00:00.000Z",
      "updated_at":        "2026-08-11T10:00:00.000Z"
    }
  ]
}
```

> Returns `results: []` if no comment exists for that number.

---

### 3. List All My Comments

**`GET /api/lead/phone-comments/`**

Returns all comments by the authenticated user, ordered by most recently updated.

---

### 4. Get a Single Comment

**`GET /api/lead/phone-comments/{id}/`**

Returns the full comment record including `comment_history`.

---

### 5. Update a Comment

**`PATCH /api/lead/phone-comments/{id}/`**

Updates comment text. Old comment is automatically moved to `comment_history`.

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
| `phone_number` | string | no | The phone number (must exist in call logs) |
| `comment` | string | no | Latest comment text |
| `comment_history` | array | no | All previous comments with timestamps |
| `lead` | UUID | yes | Auto-matched lead ID |
| `lead_name` | string | yes | Matched lead name |
| `commented_by` | UUID | no | User who wrote the comment |
| `commented_by_name` | string | no | Full name or username |
| `created_at` | string (ISO 8601) | no | When first created |
| `updated_at` | string (ISO 8601) | no | When last updated |

### `comment_history` item shape:
```json
{
  "comment":      "Previous comment text",
  "commented_at": "2026-08-11T10:00:00.000Z"
}
```

---

## Key Behaviours

1. **Phone must be in call logs** — `phone_number` must exist in `CallLog` for the authenticated user. Returns `400` otherwise.
2. **Upsert on POST** — one record per phone per user. Old comment → `comment_history`. New comment → `comment`.
3. **`commented_by` is server-side** — set from authenticated user, never from request body.
4. **Auto-match lead** — matches `Lead.mobile` and `Lead.alternate_number`. `null` if no match.
5. **Visibility** — users see only their own comments. Superusers see all.
6. **History preserved on PATCH** — updating via PATCH also moves old comment to history.

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
