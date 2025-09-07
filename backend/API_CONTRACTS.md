# API Contracts Implementation

This document describes the exact API contracts implemented according to the specifications.

## Health Check

### GET /health
**Description**: Basic health check  
**Auth**: None required  
**Response**:
```json
{"status": "ok"}
```

## User Restaurant Management

### GET /api/v1/me/restaurant
**Description**: Get the single restaurant owned by the authenticated user  
**Auth**: Required  
**Response**: Restaurant object or `null` if none exists
```json
{
  "id": "uuid",
  "owner_user_id": "uuid", 
  "name": "Restaurant Name",
  "cuisine": "Italian",
  "city": "San Francisco",
  "state": "CA",
  "contact_email": "contact@restaurant.com",
  "contact_phone": "+1-555-0123",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### PUT /api/v1/me/restaurant
**Description**: Upsert restaurant for authenticated user  
**Auth**: Required  
**Body**:
```json
{
  "name": "Restaurant Name",
  "cuisine": "Italian", 
  "city": "San Francisco",
  "state": "CA",
  "contact_email": "contact@restaurant.com",
  "contact_phone": "+1-555-0123"
}
```
**Response**: Restaurant object (same as GET)

## Diners Database

### GET /api/v1/diners
**Description**: Get diners with filtering and pagination  
**Auth**: Required  
**Query Parameters**:
- `city?`: Case-insensitive ILIKE filter
- `state?`: Exact two-letter match (full names normalized)
- `interests?`: Comma-separated list
- `match?`: `any` (default) or `all` for interests matching
- `page?`: Page number (default: 1)
- `pageSize?`: Items per page (default: 25, max: 100)

**Response**:
```json
{
  "total": 150,
  "items": [
    {
      "id": "uuid",
      "first_name": "John",
      "last_name": "Doe", 
      "seniority": "director",
      "city": "San Francisco",
      "state": "CA",
      "address_text": "123 Main St",
      "interests": ["fine_dining", "coffee_shops"],
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "consent_email": true,
      "consent_sms": true
    }
  ]
}
```

**SQL Logic Implemented**:
- City: `city ILIKE '%{city}%'`
- State: `state = '{normalized_state}'`
- Interests ANY: `interests && ARRAY[{interests}]`
- Interests ALL: `interests @> ARRAY[{interests}]`
- Ordering: `ORDER BY last_name NULLS LAST, first_name NULLS LAST`
- Pagination: `LIMIT {pageSize} OFFSET {(page-1)*pageSize}`

## AI Content Generation

### POST /api/v1/ai/offer
**Description**: Generate AI-powered marketing content  
**Auth**: Required  
**Body**:
```json
{
  "cuisine": "Italian",
  "tone": "friendly",
  "channel": "email",
  "goal": "drive traffic",
  "constraints": "mention lunch specials"
}
```

**Response for Email** (body ≤ 500 chars):
```json
{
  "subject": "🍽️ Delicious Italian Awaits You!",
  "body": "Hi {FirstName}, come try our amazing Italian dishes. Visit us today! Book your table now for our lunch specials."
}
```

**Response for SMS** (body ≤ 160 chars):
```json
{
  "body": "Hey {FirstName}! Try our amazing Italian today! Visit us for lunch specials!"
}
```

**Features**:
- Length enforcement (email: 500 chars, SMS: 160 chars)
- Automatic `{FirstName}` token injection
- OpenAI integration (fallback to templates if no API key)
- Smart truncation at word boundaries

## Campaign Management

### POST /api/v1/campaigns
**Description**: Create campaign with audience building  
**Auth**: Required  
**Body**:
```json
{
  "channel": "email",
  "subject": "Special Offer!",
  "body": "Hi {FirstName}, check out our special offer!",
  "filters": {
    "city": "San Francisco",
    "state": "CA", 
    "interests": ["fine_dining"],
    "match": "any"
  }
}
```

**Server Logic**:
1. Find user's restaurant (must exist)
2. Build audience query respecting consent:
   - Email: `consent_email=true AND email IS NOT NULL`
   - SMS: `consent_sms=true AND phone IS NOT NULL`
3. Insert campaign row
4. For each matched diner, insert `campaign_recipients` with:
   - `delivery_status='simulated_sent'`
   - `preview_payload_json` = rendered message with fake `{FirstName}`

**Response**:
```json
{
  "campaignId": "uuid",
  "audienceSize": 42,
  "previews": [
    {
      "diner_id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "rendered_message": "Hi John, check out our special offer!"
    }
  ]
}
```

### GET /api/v1/campaigns
**Description**: List campaigns for authenticated user  
**Auth**: Required  
**Response**:
```json
[
  {
    "id": "uuid",
    "created_at": "2024-01-01T12:00:00Z",
    "channel": "email", 
    "subject": "Special Offer!",
    "body": "Hi {FirstName}, check out our special offer!",
    "audience_size": 42
  }
]
```

### GET /api/v1/campaigns/{id}
**Description**: Get campaign details with recipients  
**Auth**: Required  
**Response**:
```json
{
  "id": "uuid",
  "created_at": "2024-01-01T12:00:00Z",
  "channel": "email",
  "subject": "Special Offer!",
  "body": "Hi {FirstName}, check out our special offer!",
  "filters": {
    "city": "San Francisco",
    "state": "CA",
    "interests": ["fine_dining"],
    "match": "any"
  },
  "recipients": [
    {
      "diner_id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com", 
      "phone": "+1-555-0123",
      "delivery_status": "simulated_sent",
      "preview_payload": {
        "channel": "email",
        "subject": "Special Offer!",
        "body": "Hi John, check out our special offer!",
        "recipient_name": "John Doe",
        "sent_at": "2024-01-01T12:00:00Z"
      }
    }
  ]
}
```

## Authentication

All protected endpoints require:
```
Authorization: Bearer <supabase_jwt_token>
```

The middleware automatically:
- Extracts and verifies JWT tokens
- Sets `request.state.user_id` and `request.state.user`
- Handles missing/invalid tokens appropriately

## Database Schema

All endpoints work with the Supabase schema defined in `../supabase/schema.sql`:
- `restaurants` - Restaurant ownership
- `diners` - Customer database with interests and consent
- `campaigns` - Campaign metadata
- `campaign_recipients` - Delivery tracking and previews

## Error Handling

Standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid auth)
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message",
  "type": "error_type"
}
```
