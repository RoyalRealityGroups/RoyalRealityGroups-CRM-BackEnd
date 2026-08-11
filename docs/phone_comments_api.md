# Phone Comments API — Documentation

## Overview

The Phone Comments API allows mobile app users to add and manage notes/comments
against a specific phone number (contact). One comment per phone number per user —
posting again to the same number **updates** the existing comment (upsert).

Comments are automatically linked to a Lead if the phone number matches any lead's
`mobile` or `alternate_number`.

**Base URL:** `http://<server>:8000/api/lead/phone-comments/`

**Authentication:** Bearer token (JWT) required on all endpoints.

---

## Authentication

```
Authorization: Bearer <access_token>
```

---

## Endpoints

---

### 1. Create or Update a Comment

**`POST /api/lead/phone-comments/`**

Creates a new comment for a phone number. If a comment already exists for this
phone number by the same user, it is **updated** — not duplicated.

**Request Body:**
```json
{
  "phone_number": "9876543210",
  "comment":      "Interested in 3BHK. Call back after 5pm."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | The phone number to attach the comment to |
| `comment` | string | yes | The note/comment text |

**Response `201 Created` (new comment):**
```json
{
  "id":                1,
  "phone_number":      "9876543210",
  "comment":           "Interested in 3BHK. Call back after 5pm.",
  "lead":              "abc-uuid",
  "lead_name":         "John Doe",
  "commented_by":      42,
  "commented_by_name": "Ravi Kumar",
  "created_at":        "2026-08-11T10:00:00.000Z",
  "updated_at":        "2026-08-11T10:00:00.000Z"
}
```

**Response `200 OK` (existing comment updated):**
```json
{
  "id":                1,
  "phone_number":      "9876543210",
  "comment":           "Budget revised to 50L. Very interested.",
  "lead":              "abc-uuid",
  "lead_name":         "John Doe",
  "commented_by":      42,
  "commented_by_name": "Ravi Kumar",
  "created_at":        "2026-08-11T10:00:00.000Z",
  "updated_at":        "2026-08-11T11:30:00.000Z"
}
```

> `lead` and `lead_name` are auto-populated if the phone number matches a lead.
> They will be `null` if no match is found.

---

### 2. Get Comment for a Specific Phone Number

**`GET /api/lead/phone-comments/?phone_number=9876543210`**

Returns the comment for a given phone number by the authenticated user.

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | yes | The phone number to look up |

**Response `200 OK`:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id":                1,
      "phone_number":      "9876543210",
      "comment":           "Interested in 3BHK. Call back after 5pm.",
      "lead":              "abc-uuid",
      "lead_name":         "John Doe",
      "commented_by":      42,
      "commented_by_name": "Ravi Kumar",
      "created_at":        "2026-08-11T10:00:00.000Z",
      "updated_at":        "2026-08-11T10:00:00.000Z"
    }
  ]
}
```

> Returns empty `results: []` if no comment exists for that number.

---

### 3. List All My Comments

**`GET /api/lead/phone-comments/`**

Returns all comments created by the authenticated user, ordered by most recently updated.

**Response `200 OK`:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id":                2,
      "phone_number":      "9123456789",
      "comment":           "Not interested right now.",
      "lead":              null,
      "lead_name":         null,
      "commented_by":      42,
      "commented_by_name": "Ravi Kumar",
      "created_at":        "2026-08-11T09:00:00.000Z",
      "updated_at":        "2026-08-11T09:00:00.000Z"
    },
    {
      "id":                1,
      "phone_number":      "9876543210",
      "comment":           "Interested in 3BHK. Call back after 5pm.",
      "lead":              "abc-uuid",
      "lead_name":         "John Doe",
      "commented_by":      42,
      "commented_by_name": "Ravi Kumar",
      "created_at":        "2026-08-11T10:00:00.000Z",
      "updated_at":        "2026-08-11T10:00:00.000Z"
    }
  ]
}
```

---

### 4. Get a Single Comment

**`GET /api/lead/phone-comments/{id}/`**

**Response `200 OK`:** Returns the full comment object (same shape as above).

**Response `404 Not Found`:** If the record doesn't exist or belongs to another user.

---

### 5. Update a Comment

**`PATCH /api/lead/phone-comments/{id}/`**

Updates the comment text for an existing record.

**Request Body:**
```json
{
  "comment": "Updated note — confirmed budget of 60L."
}
```

**Response `200 OK`:** Returns the updated record with new `updated_at`.

---

### 6. Delete a Comment

**`DELETE /api/lead/phone-comments/{id}/`**

Permanently deletes the comment.

**Response `204 No Content`**

---

## Response Fields Reference

| Field | Type | Nullable | Description |
|---|---|---|---|
| `id` | integer | no | Record ID |
| `phone_number` | string | no | The phone number this comment is about |
| `comment` | string | no | The note/comment text |
| `lead` | string (UUID) | yes | Auto-matched lead ID (`null` if no match) |
| `lead_name` | string | yes | Matched lead's name (`null` if no match) |
| `commented_by` | integer | no | ID of the user who wrote the comment |
| `commented_by_name` | string | no | Full name or username of the commenter |
| `created_at` | string (ISO 8601) | no | When the comment was first created |
| `updated_at` | string (ISO 8601) | no | When the comment was last updated |

---

## Key Behaviours

1. **Upsert on POST** — one comment per phone number per user. Posting again to the same number updates the existing comment. No duplicates.

2. **Auto-match lead** — when a comment is created/updated, the server searches `Lead.mobile` and `Lead.alternate_number`. If a match is found, `lead` FK is auto-set.

3. **`commented_by` is server-side** — always set from the authenticated user. Never accepted from the request body.

4. **Visibility** — users see only their own comments. Superusers and staff see all.

---

## DB Table

**Table name:** `Lead_phonecomment`

```
unique_together: [phone_number, commented_by]
```

---

## Error Responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Missing `phone_number` or `comment` |
| `401 Unauthorized` | Missing or invalid Bearer token |
| `404 Not Found` | Record does not exist or not accessible |

**Example 400:**
```json
{
  "phone_number": ["This field is required."],
  "comment": ["This field is required."]
}
```

**Example 401:**
```json
{
  "detail": "Token has expired"
}
```
