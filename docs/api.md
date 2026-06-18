# API Documentation

This document describes the request/response payloads and authentication flows of the platform's REST and WebSocket interfaces.

---

## Base Path
- **Local Dev Server**: `http://localhost:8000`
- **Docker Production Ingress**: `http://support.bangla-ai.local/api`

---

## Authentication Flow

All protected routes require a JWT bearer token passed in the HTTP headers:
`Authorization: Bearer <JWT_ACCESS_TOKEN>`

### 1. Register User
- **Endpoint**: `/api/auth/register`
- **Method**: `POST`
- **Request Body (JSON)**:
  ```json
  {
    "email": "customer@example.com",
    "password": "customerpassword123",
    "full_name": "Tahmid Hasan",
    "role": "customer"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": 3,
    "email": "customer@example.com",
    "full_name": "Tahmid Hasan",
    "role": "customer",
    "is_active": true,
    "created_at": "2026-06-18T18:00:00Z"
  }
  ```

### 2. Login to Obtain Token
- **Endpoint**: `/api/auth/token`
- **Method**: `POST`
- **Request Body (Form URL Encoded)**:
  - `username`: `agent@example.com`
  - `password`: `agentpassword123`
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "role": "agent"
  }
  ```

---

## Conversations & Chat

### 1. Chat Turn (REST)
- **Endpoint**: `/api/chat`
- **Method**: `POST`
- **Request Body (Multipart Form)**:
  - `message_in`: "আমার অর্ডার কোথায়?"
  - `session_id`: "session-user123"
- **Response (200 OK)**:
  ```json
  {
    "answer": "অর্ডার স্ট্যাটাস দেখতে অনুগ্রহ করে আপনার ৫ সংখ্যার অর্ডার আইডিটি উল্লেখ করুন।",
    "confidence_score": 0.9,
    "sources": [],
    "language": "bn",
    "sentiment": "neutral",
    "ticket_escalated": false,
    "ticket_id": null
  }
  ```

### 2. WebSocket Real-Time Chat (WebSocket)
- **Endpoint**: `/api/chat/ws/{session_id}`
- **Method**: `WS`
- **Payload format (Client to Server JSON)**:
  ```json
  {
    "message": "আমার বিলিং পেজ কাজ করছে না, সমস্যা হয়েছে।"
  }
  ```
- **Response format (Server to Client JSON)**:
  ```json
  {
    "answer": "আমি দুঃখিত যে স্বয়ংক্রিয়ভাবে আমি আপনার বিলিং সমস্যার সমাধান করতে পারছি না। আমি আপনার জন্য টিকিট তৈরি করেছি (টিকিট আইডি: TKT-A81F0B)...",
    "confidence_score": 1.0,
    "sources": [],
    "language": "bn",
    "sentiment": "negative",
    "ticket_escalated": true,
    "ticket_id": "TKT-A81F0B"
  }
  ```

---

## Ticket Management

### 1. Create Support Ticket
- **Endpoint**: `/api/tickets`
- **Method**: `POST`
- **Request Body (JSON)**:
  ```json
  {
    "customer_name": "Rahim Uddin",
    "email": "rahim@example.com",
    "category": "billing",
    "description": "Double charged on transaction #1002.",
    "priority": "medium"
  }
  ```

### 2. List Active Support Queue (Protected: Agent/Admin)
- **Endpoint**: `/api/tickets`
- **Method**: `GET`
- **Parameters**: `status` (optional), `priority` (optional)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "ticket_id": "TKT-31A8B2",
      "customer_name": "Rahim Uddin",
      "email": "rahim@example.com",
      "category": "billing",
      "priority": "urgent",
      "status": "open",
      "description": "Double charged on transaction #1002.",
      "sentiment": "negative",
      "assigned_agent_id": null,
      "created_at": "2026-06-18T18:10:00Z",
      "updated_at": "2026-06-18T18:10:00Z"
    }
  ]
  ```

---

## RAG Knowledge Seed

### Upload Knowledge File (Protected: Admin)
- **Endpoint**: `/api/upload`
- **Method**: `POST`
- **Request Body (Multipart Form)**:
  - `file`: `<PDF/CSV/DOCX/TXT file>`
- **Response (200 OK)**:
  ```json
  {
    "message": "File uploaded and processed successfully",
    "filename": "faq_guide.pdf",
    "chunks_created": 34,
    "document_id": 1
  }
  ```
