---
description: Smoke-test the running Bangla AI Customer Support app — checks health, chat, order lookup, ticket creation, and the orders API. Requires both servers already running (use the run skill first).
---

# Verify — Smoke Test

Confirms the live stack is working end-to-end. Run this after starting servers with the `run` skill, or after making changes to validate nothing is broken.

## Prerequisites

Both servers must be running:
- Backend: http://localhost:8090
- Frontend: http://localhost:5173

## Run the smoke test

```powershell
powershell -ExecutionPolicy Bypass -File .claude\skills\verify\smoke.ps1
```

Or run checks individually below.

## Manual checks

### 1. Backend health
```powershell
Invoke-RestMethod http://localhost:8090/
# Expected: { status = "online" }
```

### 2. Agent login (get JWT token)
```powershell
$form = @{ username = 'agent@example.com'; password = 'agentpassword123' }
$token = (Invoke-RestMethod -Uri 'http://localhost:8090/api/auth/token' -Method POST -Form $form).access_token
Write-Output "Token: $token"
```

### 3. Chat endpoint
```powershell
$form = @{ message_in = 'Hello, what are your delivery times?'; session_id = 'test-session-001' }
$resp = Invoke-RestMethod -Uri 'http://localhost:8090/api/chat' -Method POST -Form $form
Write-Output "Answer: $($resp.answer)"
Write-Output "Language: $($resp.language)  Sentiment: $($resp.sentiment)"
```

### 4. Order lookup via chat (real DB)
```powershell
$form = @{ message_in = 'Where is my order ORD-A1B2C?'; session_id = 'test-session-002' }
$resp = Invoke-RestMethod -Uri 'http://localhost:8090/api/chat' -Method POST -Form $form
Write-Output "Answer: $($resp.answer)"
# Expected: real order status for ORD-A1B2C (shipped)
```

### 5. Orders API — list
```powershell
$headers = @{ Authorization = "Bearer $token" }
$orders = Invoke-RestMethod -Uri 'http://localhost:8090/api/orders' -Headers $headers
Write-Output "Total orders: $($orders.Count)"
$orders | Select-Object order_id, customer_name, status | Format-Table
```

### 6. Create a new order
```powershell
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$body = @{
    customer_name = 'Test User'
    customer_email = 'test@example.com'
    items = @('Test Item A', 'Test Item B')
    total_amount = 999.00
    estimated_delivery = '2026-07-01'
} | ConvertTo-Json
$newOrder = Invoke-RestMethod -Uri 'http://localhost:8090/api/orders' -Method POST -Headers $headers -Body $body
Write-Output "Created: $($newOrder.order_id) — status: $($newOrder.status)"
```

### 7. Update order status
```powershell
$body = @{ status = 'shipped' } | ConvertTo-Json
$updated = Invoke-RestMethod -Uri "http://localhost:8090/api/orders/$($newOrder.order_id)" -Method PUT -Headers $headers -Body $body
Write-Output "Updated status: $($updated.status)"
```

### 8. Ticket creation (escalation)
```powershell
$headers2 = @{ 'Content-Type' = 'application/json' }
$body = @{
    customer_name = 'Test Customer'
    email = 'testcustomer@example.com'
    category = 'billing'
    description = 'I was charged twice and I am very frustrated!'
} | ConvertTo-Json
$ticket = Invoke-RestMethod -Uri 'http://localhost:8090/api/tickets' -Method POST -Headers $headers2 -Body $body
Write-Output "Ticket: $($ticket.ticket_id)  Priority: $($ticket.priority)  Sentiment: $($ticket.sentiment)"
# Expected: priority = urgent (negative sentiment auto-escalates)
```

### 9. Feedback submission
```powershell
$body = @{ session_id = 'test-session-001'; rating = 5; comment = 'Great support!' } | ConvertTo-Json
$fb = Invoke-RestMethod -Uri 'http://localhost:8090/api/feedback' -Method POST -Headers $headers2 -Body $body
Write-Output "Feedback ID: $($fb.id)  Rating: $($fb.rating)"
```

### 10. Analytics summary (admin only)
```powershell
$adminForm = @{ username = 'admin@example.com'; password = 'adminpassword123' }
$adminToken = (Invoke-RestMethod -Uri 'http://localhost:8090/api/auth/token' -Method POST -Form $adminForm).access_token
$adminHeaders = @{ Authorization = "Bearer $adminToken" }
$summary = Invoke-RestMethod -Uri 'http://localhost:8090/api/analytics/summary' -Headers $adminHeaders
Write-Output "Conversations: $($summary.total_conversations)  Tickets: $($summary.total_tickets)"
```

## What to look for

| Check | Pass condition |
|---|---|
| Health | `status = "online"` |
| Chat | `answer` is non-empty, `language` is detected |
| Order lookup | Returns real customer name + status from DB |
| Orders list | At least 5 seeded orders present |
| Create order | Returns new `ORD-XXXXX` id with `status = processing` |
| Ticket (negative) | `priority = urgent` auto-assigned |
| Analytics | `total_conversations` increments after chat calls |
