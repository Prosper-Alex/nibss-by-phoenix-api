#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# NIBSS by Phoenix — Full API Integration Test
# Tests every endpoint in the correct sequence.
# Run this AFTER the server is running on http://localhost:3000
# ═══════════════════════════════════════════════════════════════

BASE_URL="http://localhost:3000/api"
DIVIDER="────────────────────────────────────────"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  NIBSS by Phoenix — Integration Test     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── STEP 1: Fintech Onboarding ────────────────────────────────
echo "[$DIVIDER]"
echo "[1] POST /api/fintech/onboard"
echo "$DIVIDER"
ONBOARD_RESPONSE=$(curl -s -X POST "$BASE_URL/fintech/onboard" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Bank", "email":"testbank@nibss.test"}')
echo "$ONBOARD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ONBOARD_RESPONSE"

API_KEY=$(echo "$ONBOARD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('apiKey',''))" 2>/dev/null)
API_SECRET=$(echo "$ONBOARD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('apiSecret',''))" 2>/dev/null)
echo ""
echo "→ apiKey    : $API_KEY"
echo "→ apiSecret : $API_SECRET"
echo ""

# ── STEP 2: Login ─────────────────────────────────────────────
echo "[$DIVIDER]"
echo "[2] POST /api/auth/token"
echo "$DIVIDER"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"apiKey\":\"$API_KEY\",\"apiSecret\":\"$API_SECRET\"}")
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
echo ""
echo "→ JWT Token : ${TOKEN:0:60}..."
echo ""

# ── STEP 3: Insert BVN (public route) ────────────────────────
echo "[$DIVIDER]"
echo "[3] POST /api/insertBvn"
echo "$DIVIDER"
BVN_INSERT=$(curl -s -X POST "$BASE_URL/insertBvn" \
  -H "Content-Type: application/json" \
  -d '{
    "bvn": "10840712847",
    "firstName": "Prosper",
    "lastName": "Alex",
    "dob": "2000-05-15",
    "phone": "08012345678"
  }')
echo "$BVN_INSERT" | python3 -m json.tool 2>/dev/null || echo "$BVN_INSERT"
echo ""

# ── STEP 4: Insert NIN (public route) ────────────────────────
echo "[$DIVIDER]"
echo "[4] POST /api/insertNin"
echo "$DIVIDER"
NIN_INSERT=$(curl -s -X POST "$BASE_URL/insertNin" \
  -H "Content-Type: application/json" \
  -d '{
    "nin": "20930819374",
    "firstName": "Emeka",
    "lastName": "Okafor",
    "dob": "1998-11-22"
  }')
echo "$NIN_INSERT" | python3 -m json.tool 2>/dev/null || echo "$NIN_INSERT"
echo ""

# ── STEP 5: Validate BVN ──────────────────────────────────────
echo "[$DIVIDER]"
echo "[5] POST /api/validateBvn"
echo "$DIVIDER"
curl -s -X POST "$BASE_URL/validateBvn" \
  -H "Content-Type: application/json" \
  -d '{"bvn":"10840712847"}' | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 6: Validate NIN ──────────────────────────────────────
echo "[$DIVIDER]"
echo "[6] POST /api/validateNin"
echo "$DIVIDER"
curl -s -X POST "$BASE_URL/validateNin" \
  -H "Content-Type: application/json" \
  -d '{"nin":"20930819374"}' | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 7: Create Account (BVN) — Sender ────────────────────
echo "[$DIVIDER]"
echo "[7] POST /api/account/create (BVN — Sender)"
echo "$DIVIDER"
CREATE_SENDER=$(curl -s -X POST "$BASE_URL/account/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"kycType":"bvn","kycID":"10840712847","dob":"2000-05-15"}')
echo "$CREATE_SENDER" | python3 -m json.tool 2>/dev/null || echo "$CREATE_SENDER"

SENDER_ACCOUNT=$(echo "$CREATE_SENDER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('accountNumber',''))" 2>/dev/null)
echo ""
echo "→ Sender Account : $SENDER_ACCOUNT"
echo ""

# ── STEP 8: Create Account (NIN) — Recipient ─────────────────
echo "[$DIVIDER]"
echo "[8] POST /api/account/create (NIN — Recipient)"
echo "$DIVIDER"
CREATE_RECIPIENT=$(curl -s -X POST "$BASE_URL/account/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"kycType":"nin","kycID":"20930819374","dob":"1998-11-22"}')
echo "$CREATE_RECIPIENT" | python3 -m json.tool 2>/dev/null || echo "$CREATE_RECIPIENT"

RECIPIENT_ACCOUNT=$(echo "$CREATE_RECIPIENT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('accountNumber',''))" 2>/dev/null)
echo ""
echo "→ Recipient Account : $RECIPIENT_ACCOUNT"
echo ""

# ── STEP 9: Get All Accounts ──────────────────────────────────
echo "[$DIVIDER]"
echo "[9] GET /api/accounts"
echo "$DIVIDER"
curl -s -X GET "$BASE_URL/accounts" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 10: Name Enquiry ─────────────────────────────────────
echo "[$DIVIDER]"
echo "[10] GET /api/account/name-enquiry/$RECIPIENT_ACCOUNT"
echo "$DIVIDER"
curl -s -X GET "$BASE_URL/account/name-enquiry/$RECIPIENT_ACCOUNT" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 11: Check Sender Balance ─────────────────────────────
echo "[$DIVIDER]"
echo "[11] GET /api/account/balance/$SENDER_ACCOUNT (before transfer)"
echo "$DIVIDER"
curl -s -X GET "$BASE_URL/account/balance/$SENDER_ACCOUNT" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 12: Transfer ─────────────────────────────────────────
echo "[$DIVIDER]"
echo "[12] POST /api/transfer"
echo "$DIVIDER"
TRANSFER_RESPONSE=$(curl -s -X POST "$BASE_URL/transfer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"from\":\"$SENDER_ACCOUNT\",\"to\":\"$RECIPIENT_ACCOUNT\",\"amount\":\"5000\"}")
echo "$TRANSFER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TRANSFER_RESPONSE"

TX_ID=$(echo "$TRANSFER_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('transactionId',''))" 2>/dev/null)
echo ""
echo "→ Transaction ID : $TX_ID"
echo ""

# ── STEP 13: Check Balances After Transfer ────────────────────
echo "[$DIVIDER]"
echo "[13a] GET /api/account/balance/$SENDER_ACCOUNT (after transfer)"
echo "$DIVIDER"
curl -s -X GET "$BASE_URL/account/balance/$SENDER_ACCOUNT" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 14: Transaction Status ───────────────────────────────
echo "[$DIVIDER]"
echo "[14] GET /api/transaction/$TX_ID"
echo "$DIVIDER"
curl -s -X GET "$BASE_URL/transaction/$TX_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
echo ""

# ── STEP 15: Error Cases ──────────────────────────────────────
echo "[$DIVIDER]"
echo "[15] ERROR CASES"
echo "$DIVIDER"

echo "→ 15a. No token on protected route:"
curl -s -X GET "$BASE_URL/accounts" | python3 -m json.tool 2>/dev/null
echo ""

echo "→ 15b. Duplicate BVN:"
curl -s -X POST "$BASE_URL/insertBvn" \
  -H "Content-Type: application/json" \
  -d '{"bvn":"10840712847","firstName":"Prosper","lastName":"Alex","dob":"2000-05-15","phone":"08012345678"}' | python3 -m json.tool 2>/dev/null
echo ""

echo "→ 15c. Insufficient funds (transfer 999999):"
curl -s -X POST "$BASE_URL/transfer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"from\":\"$SENDER_ACCOUNT\",\"to\":\"$RECIPIENT_ACCOUNT\",\"amount\":\"999999\"}" | python3 -m json.tool 2>/dev/null
echo ""

echo "→ 15d. Invalid transaction ID:"
curl -s -X GET "$BASE_URL/transaction/TX-DOES-NOT-EXIST" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║  Test complete.                          ║"
echo "╚══════════════════════════════════════════╝"
