# Alert Triggers API Specification

> For mobile application implementation (Android/iOS)

**Base URL:** `{{BASE_URL}}/api/system/`  
**Authentication:** Bearer Token (JWT) — `Authorization: Bearer <access_token>`

---

## Table of Contents

1. [Get Events Metadata](#1-get-events-metadata)
2. [List Alert Triggers](#2-list-alert-triggers)
3. [Get Single Alert Trigger](#3-get-single-alert-trigger)
4. [Create Alert Trigger](#4-create-alert-trigger)
5. [Update Alert Trigger](#5-update-alert-trigger)
6. [Toggle Trigger Status](#6-toggle-trigger-status)
7. [Delete Alert Trigger](#7-delete-alert-trigger)
8. [List Templates](#8-list-templates)
9. [Enums & Constants](#9-enums--constants)
10. [FCM Push Notification Payload](#10-fcm-push-notification-payload)

---

## 1. Get Events Metadata

Returns all available modules, events, channels, and recipient types for the trigger creation form.

**Endpoint:** `GET /api/system/alertconfigs/events/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "modules": [
    {
      "app_label": "Lead",
      "name": "Lead",
      "screens": [
        { "id": 12, "model": "lead", "name": "Lead" },
        { "id": 13, "model": "leadfollowup", "name": "Lead Follow Up" },
        { "id": 14, "model": "leadstatushistory", "name": "Lead Status History" },
        { "id": 15, "model": "calllog", "name": "Call Log" }
      ]
    },
    {
      "app_label": "Booking",
      "name": "Booking",
      "screens": [
        { "id": 20, "model": "booking", "name": "Booking" }
      ]
    },
    {
      "app_label": "Inventory",
      "name": "Inventory",
      "screens": [
        { "id": 25, "model": "inventory", "name": "Inventory" }
      ]
    },
    {
      "app_label": "ProjectManagement",
      "name": "Project Management",
      "screens": [
        { "id": 30, "model": "project", "name": "Project" }
      ]
    },
    {
      "app_label": "SiteVisit",
      "name": "Site Visit",
      "screens": [
        { "id": 35, "model": "sitevisit", "name": "Site Visit" },
        { "id": 36, "model": "calendartodo", "name": "Calendar Todo" }
      ]
    },
    {
      "app_label": "Documents",
      "name": "Documents",
      "screens": [
        { "id": 40, "model": "document", "name": "Document" }
      ]
    },
    {
      "app_label": "Users",
      "name": "Users",
      "screens": [
        { "id": 5, "model": "user", "name": "User" }
      ]
    }
  ],
  "events": [
    { "id": 1, "name": "Create" },
    { "id": 2, "name": "Update" },
    { "id": 3, "name": "Delete" },
    { "id": 4, "name": "Approved" },
    { "id": 5, "name": "Rejected" },
    { "id": 6, "name": "AddAssignee" },
    { "id": 7, "name": "RemoveAssignee" }
  ],
  "channels": [
    { "id": 1, "name": "SMS" },
    { "id": 2, "name": "Email" },
    { "id": 3, "name": "Notification" }
  ],
  "recipient_types": [
    { "id": 1, "name": "CreatedBy" },
    { "id": 2, "name": "Group" },
    { "id": 3, "name": "User" },
    { "id": 4, "name": "Variable" },
    { "id": 5, "name": "Value" }
  ],
  "priorities": [
    { "id": 1, "name": "Low" },
    { "id": 2, "name": "Medium" },
    { "id": 3, "name": "High" }
  ],
  "notification_types": [
    { "id": 1, "name": "Notification" },
    { "id": 2, "name": "Remainder" },
    { "id": 3, "name": "Alert" }
  ]
}
```

---

## 2. List Alert Triggers

**Endpoint:** `GET /api/system/alertconfigs/`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20) |
| `search` | string | Search by code, value, variable, group name |
| `event_type` | int | Filter by event type (1-7) |
| `type` | int | Filter by channel (1=SMS, 2=Email, 3=Notification) |
| `is_active` | boolean | Filter by active status |
| `sender_type` | int | Filter by sender type (1-5) |
| `is_scheduled` | boolean | Filter scheduled alerts |
| `message_priority` | int | Filter by priority (1-3) |
| `notification_type` | int | Filter by notification type (1-3) |

**Response (200):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "screen": {
        "id": 12,
        "app_label": "Lead",
        "model": "lead"
      },
      "event_type": 1,
      "event_type_name": "Create",
      "sender_type": 2,
      "sender_type_name": "Group",
      "type": 3,
      "type_name": "Notification",
      "message_priority": 2,
      "message_priority_name": "Medium",
      "notification_type": 1,
      "notification_type_name": "Notification",
      "frequency": null,
      "frequency_name": null,
      "gateway": null,
      "send_to_groups": [
        { "id": 1, "name": "Sales Team" }
      ],
      "alert_users": [],
      "value": null,
      "variable": null,
      "template": {
        "id": 5,
        "code": "TEMP-0005",
        "name": "New Lead Created",
        "message": "A new lead ((instance.name)) has been created from ((instance.lead_source)).",
        "is_active": true
      },
      "subject_template": {
        "id": 6,
        "code": "TEMP-0006",
        "name": "New Lead Subject",
        "message": "New Lead: ((instance.name))",
        "is_active": true
      },
      "repeat_interval": null,
      "start_time": null,
      "attachment_variable": null,
      "send_doc": false,
      "is_scheduled": false,
      "is_active": true,
      "is_attachment": false
    }
  ]
}
```

---

## 3. Get Single Alert Trigger

**Endpoint:** `GET /api/system/alertconfigs/{id}`

**Response (200):** Same structure as a single item from the list response above.

---

## 4. Create Alert Trigger

**Endpoint:** `POST /api/system/alertconfigs/create/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Example 1: Push notification to a group when a Lead is created

```json
{
  "screen_id": 12,
  "event_type": 1,
  "type": 3,
  "sender_type": 2,
  "send_to_group_ids": [1, 3],
  "template_id": 5,
  "subject_template_id": 6,
  "message_priority": 2,
  "notification_type": 1,
  "is_active": true,
  "is_scheduled": false,
  "send_doc": false,
  "is_attachment": false
}
```

### Example 2: Email to the created-by user when a Booking is approved

```json
{
  "screen_id": 20,
  "event_type": 4,
  "type": 2,
  "sender_type": 1,
  "template_id": 10,
  "subject_template_id": 11,
  "message_priority": 3,
  "notification_type": 1,
  "gateway": "Default",
  "is_active": true,
  "is_scheduled": false,
  "send_doc": true,
  "is_attachment": false
}
```

### Example 3: SMS to a specific variable (assigned employee) when Lead is updated

```json
{
  "screen_id": 12,
  "event_type": 2,
  "type": 1,
  "sender_type": 4,
  "variable": "assigned_employee",
  "template_id": 8,
  "message_priority": 1,
  "notification_type": 1,
  "gateway": "Default",
  "is_active": true,
  "is_scheduled": false,
  "send_doc": false,
  "is_attachment": false
}
```

### Example 4: Notification to specific users when a Site Visit is created

```json
{
  "screen_id": 35,
  "event_type": 1,
  "type": 3,
  "sender_type": 3,
  "alert_users": [
    { "user_type": "User", "user_identifier": "5" },
    { "user_type": "User", "user_identifier": "12" }
  ],
  "template_id": 15,
  "subject_template_id": 16,
  "message_priority": 2,
  "notification_type": 1,
  "is_active": true,
  "is_scheduled": false,
  "send_doc": false,
  "is_attachment": false
}
```

### Example 5: Scheduled reminder notification (repeats every 2 hours)

```json
{
  "screen_id": 13,
  "event_type": 1,
  "type": 3,
  "sender_type": 2,
  "send_to_group_ids": [2],
  "template_id": 20,
  "subject_template_id": 21,
  "message_priority": 3,
  "notification_type": 2,
  "is_active": true,
  "is_scheduled": true,
  "repeat_interval": 2,
  "frequency": 2,
  "start_time": "01-08-2026 09:00:00",
  "send_doc": false,
  "is_attachment": false
}
```

### Example 6: Email with document attachment to a fixed email value

```json
{
  "screen_id": 20,
  "event_type": 1,
  "type": 2,
  "sender_type": 5,
  "value": "accounts@royalrealitygroups.com",
  "template_id": 25,
  "subject_template_id": 26,
  "message_priority": 2,
  "notification_type": 1,
  "gateway": "Default",
  "is_active": true,
  "is_scheduled": false,
  "send_doc": true,
  "is_attachment": false
}
```

**Response (201):** Returns the full created trigger object (same structure as GET).

---

## 5. Update Alert Trigger

**Endpoint:** `PUT /api/system/alertconfigs/{id}`

**Payload:** Same structure as Create. All fields should be sent.

### Example: Update trigger ID 1 — change priority and add more groups

```json
{
  "screen_id": 12,
  "event_type": 1,
  "type": 3,
  "sender_type": 2,
  "send_to_group_ids": [1, 2, 3],
  "template_id": 5,
  "subject_template_id": 6,
  "message_priority": 3,
  "notification_type": 1,
  "is_active": true,
  "is_scheduled": false,
  "send_doc": false,
  "is_attachment": false
}
```

### Example: Update alert_users (add/remove specific users)

```json
{
  "screen_id": 35,
  "event_type": 1,
  "type": 3,
  "sender_type": 3,
  "alert_users": [
    { "id": "uuid-existing-user-1", "user_type": "User", "user_identifier": "5", "dodelete": false },
    { "id": "uuid-existing-user-2", "user_type": "User", "user_identifier": "12", "dodelete": true },
    { "user_type": "User", "user_identifier": "20", "dodelete": false }
  ],
  "template_id": 15,
  "subject_template_id": 16,
  "message_priority": 2,
  "notification_type": 1,
  "is_active": true,
  "is_scheduled": false,
  "send_doc": false,
  "is_attachment": false
}
```

> **Note on alert_users update:**
> - Include `"id"` to reference existing users
> - Set `"dodelete": true` to soft-delete an existing user from the trigger
> - Omit `"id"` to add a new user to the trigger

**Response (200):** Returns the full updated trigger object.

---

## 6. Toggle Trigger Status

Quick enable/disable without a full update.

**Endpoint:** `PATCH /api/system/alertconfigs/{id}/status/`

**Payload:**
```json
{
  "is_active": false
}
```

**Response (200):**
```json
{
  "id": 1,
  "is_active": false
}
```

---

## 7. Delete Alert Trigger

Soft-deletes the trigger (sets `is_deleted = true`).

**Endpoint:** `DELETE /api/system/alertconfigs/{id}`

**Response (204):** No content

---

## 8. List Templates

Get available message templates for dropdown selection.

**Endpoint:** `GET /api/system/template/mini/`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by code, name, or message content |

**Response (200):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "code": "TEMP-0005",
      "name": "New Lead Created",
      "message": "A new lead ((instance.name)) has been created from ((instance.lead_source)).",
      "is_active": true
    },
    {
      "id": 6,
      "code": "TEMP-0006",
      "name": "New Lead Subject",
      "message": "New Lead: ((instance.name))",
      "is_active": true
    },
    {
      "id": 10,
      "code": "TEMP-0010",
      "name": "Booking Approved",
      "message": "Your booking for ((instance.property_name)) has been approved.",
      "is_active": true
    }
  ]
}
```

### Template Variables

Templates support dynamic variables using double parentheses `(( ))`:

| Variable | Description |
|----------|-------------|
| `((instance.name))` | Any field on the triggering model instance |
| `((instance.id))` | Instance ID |
| `((instance.code))` | Instance code |
| `((instance.created_on))` | Created timestamp |
| `((user.username))` | Recipient user's username |
| `((user.first_name))` | Recipient user's first name |
| `((user.email))` | Recipient user's email |

---

## 9. Enums & Constants

### Event Types

| ID | Name | Description |
|----|------|-------------|
| 1 | Create | When a new record is created |
| 2 | Update | When an existing record is updated |
| 3 | Delete | When a record is deleted |
| 4 | Approved | When a record is approved (authorization) |
| 5 | Rejected | When a record is rejected (authorization) |
| 6 | AddAssignee | When a user is assigned to a record |
| 7 | RemoveAssignee | When a user is removed from a record |

### Channel Types

| ID | Name | Description |
|----|------|-------------|
| 1 | SMS | Sends SMS to user's phone |
| 2 | Email | Sends email to user's email |
| 3 | Notification | Sends FCM push notification |

### Sender/Recipient Types

| ID | Name | Description |
|----|------|-------------|
| 1 | CreatedBy | Sends to the user who created the record |
| 2 | Group | Sends to all users in specified groups |
| 3 | User | Sends to specific users by ID |
| 4 | Variable | Sends to user referenced by a model field (e.g., `assigned_employee`) |
| 5 | Value | Sends to a fixed email/phone value |

### Message Priority

| ID | Name |
|----|------|
| 1 | Low |
| 2 | Medium |
| 3 | High |

### Notification Type

| ID | Name |
|----|------|
| 1 | Notification |
| 2 | Remainder |
| 3 | Alert |

### Frequency (for scheduled triggers)

| ID | Name |
|----|------|
| 1 | Minutes |
| 2 | Hours |
| 3 | Days |
| 4 | Weeks |

### Date/Time Format

All datetime fields use: `DD-MM-YYYY HH:MM:SS`  
Example: `"01-08-2026 09:00:00"`

---

## 10. FCM Push Notification Payload

When a trigger fires with `type: 3` (Notification), the backend sends an FCM multicast message to all active device tokens for the recipient user(s).

### FCM Message Structure (received by mobile app)

```json
{
  "notification": {
    "title": "5",
    "body": "A new lead John Doe has been created from Website."
  },
  "data": {
    "id": "142",
    "message": "A new lead John Doe has been created from Website.",
    "type": "Lead",
    "ref_id": "55",
    "modified_on": "2026-08-07 14:30:00",
    "web_navigation_url": "/leads/55",
    "mobile_navigation_url": "/lead-detail/55"
  }
}
```

### Data Fields Description

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Notification record ID (in database) |
| `message` | string | Formatted message body |
| `type` | string | Model class name (e.g., "Lead", "Booking", "SiteVisit") |
| `ref_id` | string | Instance ID of the record that triggered the alert |
| `modified_on` | string | Timestamp when notification was created |
| `web_navigation_url` | string/null | URL path for web app navigation |
| `mobile_navigation_url` | string/null | Deep link path for mobile navigation |

### Device Token Registration

The mobile app must register its FCM token via the Device model:

**Endpoint:** `POST /api/users/device/register/` (or your existing device registration endpoint)

**Payload:**
```json
{
  "uuid": "device-unique-id",
  "fcmtoken": "firebase-cloud-messaging-token",
  "device_type": "android",
  "is_active": true
}
```

> The backend queries active devices with valid FCM tokens for the recipient user when sending push notifications.

---

## Mobile App Implementation Notes

### Trigger Creation Flow (screens)

1. **Select Module** → Show list of modules from `metadata.modules`
2. **Select Screen** → Show screens within selected module
3. **Select Event** → Show events from `metadata.events`
4. **Select Channel** → SMS / Email / Push Notification
5. **Select Recipients** → Based on `sender_type`:
   - `1 (CreatedBy)` — No extra input needed
   - `2 (Group)` — Show group picker (fetch from `/api/users/groups/`)
   - `3 (User)` — Allow adding user IDs
   - `4 (Variable)` — Text field for model field name
   - `5 (Value)` — Text field for email/phone
6. **Select Template** → Dropdown from `/api/system/template/mini/`
7. **Options** → Priority, notification type, enabled, scheduled
8. **Submit** → `POST /api/system/alertconfigs/create/`

### Handling Received Push Notifications

```kotlin
// Android (Kotlin) — FirebaseMessagingService
override fun onMessageReceived(remoteMessage: RemoteMessage) {
    val data = remoteMessage.data
    val notificationId = data["id"]
    val message = data["message"]
    val type = data["type"]           // "Lead", "Booking", etc.
    val refId = data["ref_id"]        // Instance ID to navigate to
    val mobileUrl = data["mobile_navigation_url"]  // Deep link path
    
    // Show local notification
    showNotification(
        title = remoteMessage.notification?.title ?: "New Alert",
        body = message ?: "",
        deepLink = mobileUrl
    )
}
```

```swift
// iOS (Swift) — UNUserNotificationCenterDelegate
func userNotificationCenter(_ center: UNUserNotificationCenter,
    didReceive response: UNNotificationResponse) {
    let userInfo = response.notification.request.content.userInfo
    let type = userInfo["type"] as? String       // "Lead", "Booking"
    let refId = userInfo["ref_id"] as? String    // Instance ID
    let mobileUrl = userInfo["mobile_navigation_url"] as? String
    
    // Navigate to the appropriate screen
    navigateToScreen(type: type, refId: refId, path: mobileUrl)
}
```

### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Validation error — missing required fields |
| 401 | Unauthorized — invalid/expired token |
| 404 | Trigger not found |
| 500 | Internal server error |

**Validation Error Example (400):**
```json
{
  "send_to_group_ids": ["send_to_group_ids is required when sender_type is GROUP."],
  "alert_users": ["alert_users is required when sender_type is USER."]
}
```

---

## Quick Reference — Common Use Cases

| Use Case | screen_id | event_type | type | sender_type |
|----------|-----------|------------|------|-------------|
| Notify sales team on new lead | Lead screen ID | 1 (Create) | 3 (Push) | 2 (Group) |
| Email employee when lead assigned | Lead screen ID | 6 (AddAssignee) | 2 (Email) | 4 (Variable: `assigned_employee`) |
| Push to creator when booking approved | Booking screen ID | 4 (Approved) | 3 (Push) | 1 (CreatedBy) |
| SMS to manager on booking creation | Booking screen ID | 1 (Create) | 1 (SMS) | 2 (Group) |
| Alert specific users on site visit | SiteVisit screen ID | 1 (Create) | 3 (Push) | 3 (User) |
| Scheduled follow-up reminder | LeadFollowUp screen ID | 1 (Create) | 3 (Push) | 1 (CreatedBy) |
