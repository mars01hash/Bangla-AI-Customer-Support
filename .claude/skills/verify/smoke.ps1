# Automated smoke test for Bangla AI Customer Support platform
# Run from project root: powershell -ExecutionPolicy Bypass -File .claude\skills\verify\smoke.ps1
# Requires: backend running on http://localhost:8090

$pass = 0
$fail = 0

function Check {
    param($label, $block)
    try {
        $result = & $block
        Write-Host "  PASS  $label" -ForegroundColor Green
        $script:pass++
        return $result
    } catch {
        Write-Host "  FAIL  $label -- $_" -ForegroundColor Red
        $script:fail++
        return $null
    }
}

# Helper: encode a hashtable as application/x-www-form-urlencoded
function To-FormBody($h) {
    ($h.GetEnumerator() | ForEach-Object { "$([Uri]::EscapeDataString($_.Key))=$([Uri]::EscapeDataString($_.Value))" }) -join '&'
}

Write-Host ""
Write-Host "Bangla AI Support -- Smoke Test" -ForegroundColor Cyan
Write-Host ""

# 1. Health
Check "Backend health" {
    $r = Invoke-RestMethod http://localhost:8090/ -TimeoutSec 5
    if ($r.status -ne 'online') { throw "status=$($r.status)" }
}

# 2. Agent auth
$token = $null
$tok = Check "Agent login" {
    $body = To-FormBody @{ username='agent@example.com'; password='agentpassword123' }
    $resp = Invoke-RestMethod -Uri 'http://localhost:8090/api/auth/token' -Method POST `
        -Body $body -ContentType 'application/x-www-form-urlencoded' -TimeoutSec 5
    $resp.access_token
}
$token = $tok
$jsonHeaders = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }

# 3. Chat (English)
Check "Chat EN greeting" {
    $body = To-FormBody @{ message_in='Hello, how can I get help?'; session_id='smoke-001' }
    $r = Invoke-RestMethod -Uri 'http://localhost:8090/api/chat' -Method POST `
        -Body $body -ContentType 'application/x-www-form-urlencoded' -TimeoutSec 15
    if (-not $r.answer) { throw "Empty answer" }
}

# 4. Order lookup from real DB
Check "Order lookup ORD-A1B2C via chat" {
    $body = To-FormBody @{ message_in='Where is my order ORD-A1B2C?'; session_id='smoke-002' }
    $r = Invoke-RestMethod -Uri 'http://localhost:8090/api/chat' -Method POST `
        -Body $body -ContentType 'application/x-www-form-urlencoded' -TimeoutSec 15
    if ($r.answer -notmatch 'ORD-A1B2C') { throw "Order ID not in response: $($r.answer)" }
}

# 5. Orders API list
Check "Orders API -- seeded data present" {
    $r = Invoke-RestMethod -Uri 'http://localhost:8090/api/orders' -Headers $jsonHeaders -TimeoutSec 5
    if ($r.Count -lt 1) { throw "Expected orders, got $($r.Count)" }
}

# 6. Create order
$createdId = $null
$created = Check "Create order via API" {
    $b = @{ customer_name='Smoke User'; customer_email='smoke@test.com'; items=@('Widget A'); total_amount=500.0 } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri 'http://localhost:8090/api/orders' -Method POST -Headers $jsonHeaders -Body $b -TimeoutSec 5
    if ($r.status -ne 'processing') { throw "Expected processing, got $($r.status)" }
    $r
}
if ($created) { $createdId = $created.order_id }

# 7. Update order status
Check "Update order status to shipped" {
    if (-not $createdId) { throw "No order to update (create step failed)" }
    $b = @{ status='shipped' } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "http://localhost:8090/api/orders/$createdId" -Method PUT -Headers $jsonHeaders -Body $b -TimeoutSec 5
    if ($r.status -ne 'shipped') { throw "Expected shipped, got $($r.status)" }
}

# 8. Ticket auto-escalation (negative sentiment -> urgent)
Check "Ticket urgent priority for negative text" {
    $h = @{ 'Content-Type'='application/json' }
    $b = @{ customer_name='Angry User'; email='angry@test.com'; category='billing'; description='This is terrible, I want a refund now!' } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri 'http://localhost:8090/api/tickets' -Method POST -Headers $h -Body $b -TimeoutSec 5
    if ($r.priority -ne 'urgent') { throw "Expected urgent, got $($r.priority)" }
}

# 9. Feedback (uses session from check 3)
Check "Submit feedback rating" {
    $h = @{ 'Content-Type'='application/json' }
    $b = @{ session_id='smoke-001'; rating=4; comment='Good bot' } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri 'http://localhost:8090/api/feedback' -Method POST -Headers $h -Body $b -TimeoutSec 5
    if ($r.rating -ne 4) { throw "Rating mismatch: $($r.rating)" }
}

# Summary
Write-Host ""
$color = if ($fail -eq 0) { 'Green' } else { 'Yellow' }
Write-Host "--- Results: $pass passed, $fail failed ---" -ForegroundColor $color
Write-Host ""
exit $fail
