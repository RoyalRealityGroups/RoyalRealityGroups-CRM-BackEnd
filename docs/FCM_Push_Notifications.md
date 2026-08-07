# Push Notifications — FCM Integration Guide (Mobile App)

## Overview

The RRGMS backend uses **Firebase Cloud Messaging (FCM)** to send push notifications to mobile devices. This document covers everything the mobile developer needs to integrate push notifications.

---

## Architecture

```
Mobile App → Login (sends FCM token) → Backend stores token in Device table
Backend Event (lead assigned, booking created, etc.) → send_push_notification()
  → Queries all active devices for user → Firebase Admin SDK → FCM → Mobile Device
```

---

## Authentication

All API requests require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## 1. Login — Register Device + FCM Token

### Endpoint

```
POST /api/users/login/
```

### Request Body

```json
{
  "username": "raju_sales",
  "password": "Test@1234",
  "user_type": "User",
  "device_name": "Raju's Phone",
  "device_uuid": "unique-device-id-from-android",
  "device_type": 1,
  "device_fcmtoken": "dK8s7f...your_fcm_registration_token...xYz",
  "device_apntoken": ""
}
```

### Field Details

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Username, email, or phone number |
| `password` | string | Yes | User's password |
| `user_type` | string | Yes | Always `"User"` for this app |
| `device_name` | string | No | Human-readable device name (e.g., "Samsung Galaxy S24") |
| `device_uuid` | string | Yes | Unique device identifier (use Android ID or a persistent UUID) |
| `device_type` | integer | Yes | `1` = Android, `2` = iOS, `3` = Web |
| `device_fcmtoken` | string | No | FCM registration token from Firebase SDK |
| `device_apntoken` | string | No | APNs token (iOS only, leave empty for Android) |

### Success Response (200 OK)

```json
{
  "id": "e524f33d-8935-412d-b5c7-248fad527ba8",
  "email": "raju@royalrealitygroup.com",
  "phone": "9876543210",
  "username": "raju_sales",
  "user_type": "User",
  "full_name": "Raju Kumar",
  "group_name": "Sales",
  "is_default_password": false,
  "is_superuser": false,
  "permissions": ["Lead.view_lead", "Lead.add_lead", ...],
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Error Responses

| Status | Error | Meaning |
|--------|-------|---------|
| 401 | `Account is inactive` | User deactivated by admin |
| 401 | `Incorrect password` | Wrong credentials |
| 401 | `This device not allowed` | Single-device policy violation |
| 401 | `This device type not allowed` | User's `device_access` restricts this device type |

---

## 2. Token Refresh

When the access token expires (24h in production), use the refresh token:

```
POST /api/users/token/refresh/
```

### Request

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Response (200 OK)

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...(new token)"
}
```

---

## 3. Update FCM Token (Token Refresh)

Firebase can rotate the FCM token at any time. When your app detects a new token via `onNewToken()`, upload it:

```
POST /api/users/login/
```

Re-login with the same credentials and updated `device_fcmtoken`. The backend will update the existing device record (matched by `device_uuid`).

**Alternative**: Directly update via device endpoint:

```
PATCH /api/users/userdevices/<device_id>
Authorization: Bearer <access_token>
```

```json
{
  "fcmtoken": "new_fcm_token_here"
}
```

---

## 4. Logout — Clear FCM Token

```
POST /api/users/logout/
Authorization: Bearer <access_token>
```

### Request

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

This clears the device's `fcmtoken` and `accesstoken` on the backend, stopping push notifications.

---

## 5. Push Notification Payload (What the app receives)

When the backend sends a push notification, the FCM message looks like:

### Notification (foreground display)

```json
{
  "notification": {
    "title": "New Lead Assigned",
    "body": "Lead 'Ramesh Reddy' has been assigned to you"
  },
  "data": {
    "id": "notification-uuid",
    "message": "Lead 'Ramesh Reddy' has been assigned to you",
    "type": "1",
    "ref_id": "lead-uuid",
    "modified_on": "2026-08-06T10:30:00+05:30",
    "web_navigation_url": "/lead/view/lead-uuid",
    "mobile_navigation_url": "/lead/view/lead-uuid"
  }
}
```

### Data Fields

| Field | Description |
|-------|-------------|
| `id` | Notification record ID (for marking as read) |
| `message` | Full notification message text |
| `type` | Notification type (1 = info, 2 = alert, etc.) |
| `ref_id` | Reference entity ID (lead ID, booking ID, etc.) |
| `modified_on` | Timestamp of the event |
| `web_navigation_url` | Path for web navigation (ignore in mobile) |
| `mobile_navigation_url` | Path for mobile app navigation |

---

## 6. Fetch In-App Notifications

```
GET /api/system/Notification/
Authorization: Bearer <access_token>
```

### Response (200 OK)

```json
{
  "count": 25,
  "next": "/api/system/Notification/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "subject": "New Lead Assigned",
      "body": "Lead 'Ramesh Reddy' has been assigned to you",
      "type": 1,
      "ref": "lead-uuid",
      "is_read": false,
      "created_on": "2026-08-06T10:30:00+05:30",
      "web_navigation_url": "/lead/view/lead-uuid",
      "mobile_navigation_url": "/lead/view/lead-uuid"
    }
  ]
}
```

### Mark as Read

```
PATCH /api/system/Notification/Clear/<notification_id>/
Authorization: Bearer <access_token>
```

### Clear All

```
POST /api/system/Notification/ClearAll/
Authorization: Bearer <access_token>
```

---

## 7. Call Log Sync (Android)

The mobile app syncs call logs to the backend. This is used for the dashboard calling analytics.

```
POST /api/lead/call-logs/
Authorization: Bearer <access_token>
```

### Request

```json
{
  "phone_number": "9001234567",
  "call_type": "outgoing",
  "duration_secs": 180,
  "called_at": "2026-08-06T14:30:00+05:30",
  "device_platform": "android"
}
```

### Field Details

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `phone_number` | string | Yes | Phone number called (with or without country code) |
| `call_type` | string | Yes | `outgoing`, `incoming`, `missed`, `rejected`, `unknown` |
| `duration_secs` | integer | Yes | Call duration in seconds (0 for missed/rejected) |
| `called_at` | datetime | Yes | ISO 8601 timestamp of when call started |
| `device_platform` | string | No | `"android"` or `"ios"` (default: android) |

### Response (201 Created / 200 OK for duplicates)

```json
{
  "id": 1,
  "phone_number": "9001234567",
  "call_type": "outgoing",
  "duration_secs": 180,
  "called_at": "2026-08-06T14:30:00+05:30",
  "device_platform": "android",
  "lead": "lead-uuid-if-matched",
  "lead_name": "Ramesh Reddy",
  "called_by": "user-uuid",
  "called_by_name": "Raju Kumar",
  "created_at": "2026-08-06T14:31:00+05:30"
}
```

**Duplicate Guard**: If the same `(phone_number, called_at, called_by)` already exists, it returns the existing record with 200 (not 201). Safe to re-sync.

---

## 8. Notification Events (When push is sent)

The backend sends push notifications on these events:

| Event | Recipient | Message |
|-------|-----------|---------|
| Lead assigned to employee | The assigned employee | "Lead 'X' has been assigned to you" |
| New booking created | Reporting manager | "New booking created by Y for project Z" |
| Follow-up reminder due | The employee | "Follow-up due for lead X" |
| Site visit scheduled | The assigned employee | "Site visit scheduled for X on DATE" |

---

## 9. Firebase Setup (Mobile App Side)

### Android (`google-services.json`)

1. Go to Firebase Console → Project Settings → Your apps → Android
2. Download `google-services.json`
3. Place in `app/` directory
4. Add Firebase dependencies to `build.gradle`

### Get FCM Token (Kotlin)

```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        // Send this token during login as device_fcmtoken
    }
}
```

### Handle Token Refresh

```kotlin
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        // Re-upload to backend via login or PATCH device endpoint
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        val data = remoteMessage.data
        val notificationId = data["id"]
        val message = data["message"]
        val type = data["type"]
        val refId = data["ref_id"]
        val navUrl = data["mobile_navigation_url"]
        
        // Show local notification & handle tap navigation
    }
}
```

---

## 10. Device Model (Backend)

| Field | Description |
|-------|-------------|
| `uuid` | Unique device identifier (your device ID) |
| `type` | 1=Android, 2=iOS, 3=Web |
| `fcmtoken` | Current FCM registration token |
| `apntoken` | APNs token (iOS) |
| `accesstoken` | Current JWT access token |
| `user_identifier` | User UUID |
| `user_type` | "User" |
| `is_active` | Whether device can receive pushes |
| `socket` | WebSocket connection ID (empty = not connected) |

**Push is sent to devices where**: `is_active=True AND fcmtoken != '' AND socket is empty`

(When socket is connected, real-time updates go via WebSocket instead of push.)

---

## 11. Device Access Control

Each user has a `device_access` setting:

| Value | Meaning |
|-------|---------|
| 1 | Only Mobile (Android/iOS) |
| 2 | Only Web |
| 3 | Both Mobile + Web |
| 4 | None (cannot login) |

If a user with `device_access = 2` (Only Web) tries to login from an Android device, the backend rejects with 401.

---

## Quick Reference — All Relevant Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/users/login/` | Login + register device + FCM token |
| POST | `/api/users/logout/` | Logout + clear FCM token |
| POST | `/api/users/token/refresh/` | Refresh access token |
| GET | `/api/users/userdevices/me` | List my devices |
| PATCH | `/api/users/userdevices/<id>` | Update device (FCM token) |
| GET | `/api/system/Notification/` | Fetch in-app notifications |
| PATCH | `/api/system/Notification/Clear/<id>/` | Mark notification as read |
| POST | `/api/system/Notification/ClearAll/` | Clear all notifications |
| POST | `/api/lead/call-logs/` | Sync call log from mobile |
| GET | `/api/lead/call-logs/` | List my call logs |

---

## Base URL

```
Production: https://your-domain.com
Development: http://localhost:8000
```

All endpoints are prefixed accordingly. Example full URL:
```
POST https://your-domain.com/api/users/login/
```
