#!/usr/bin/env python3
"""Live NIBSS-by-Phoenix API investigation. Uses synthetic test data only."""

from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

BASE = "https://nibssbyphoenix.onrender.com"
OUT = os.path.dirname(os.path.abspath(__file__))
ERROR_ROWS: list[dict[str, Any]] = []
LOG: list[dict[str, Any]] = []

CTX = ssl.create_default_context()


def b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def decode_jwt(token: str) -> dict[str, Any]:
    header_b64, payload_b64, signature_b64 = token.split(".")
    return {
        "header_raw": header_b64,
        "payload_raw": payload_b64,
        "signature_raw": signature_b64,
        "header": json.loads(b64url_decode(header_b64)),
        "payload": json.loads(b64url_decode(payload_b64)),
        "signature_bytes_len": len(b64url_decode(signature_b64)),
    }


def save(name: str, data: Any) -> None:
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, indent=2, default=str)
        else:
            f.write(str(data))


def redact(obj: Any) -> Any:
    sensitive = {
        "apiKey",
        "apiSecret",
        "token",
        "authorization",
        "Authorization",
    }
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in sensitive or k.lower() in {"apisecret", "apikey"}:
                out[k] = "<redacted>"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    if isinstance(obj, str) and obj.count(".") == 2 and len(obj) > 40:
        return "<redacted-jwt>"
    return obj


def request(
    method: str,
    path: str,
    *,
    body: Optional[dict] = None,
    token: Optional[str] = None,
    extra_headers: Optional[dict] = None,
    save_as: Optional[str] = None,
    label: Optional[str] = None,
    error_test: Optional[str] = None,
    raw_body: Optional[bytes] = None,
    content_type: Optional[str] = "application/json",
) -> dict[str, Any]:
    url = path if path.startswith("http") else BASE + path
    headers = {"Accept": "application/json"}
    data = None
    if raw_body is not None:
        data = raw_body
        if content_type:
            headers["Content-Type"] = content_type
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.time()
    status = None
    resp_headers: dict[str, str] = {}
    raw = b""
    parsed: Any = None
    error = None
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=45) as resp:
            status = resp.status
            resp_headers = dict(resp.headers.items())
            raw = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        resp_headers = dict(e.headers.items()) if e.headers else {}
        raw = e.read()
        error = f"HTTPError {e.code}"
    except Exception as e:
        error = f"{type(e).__name__}: {e}"

    text = raw.decode("utf-8", errors="replace") if raw else ""
    ctype = resp_headers.get("Content-Type") or resp_headers.get("content-type") or ""
    if "json" in ctype.lower() or (text.startswith("{") or text.startswith("[")):
        try:
            parsed = json.loads(text) if text else None
        except json.JSONDecodeError:
            parsed = None

    record = {
        "label": label or save_as or f"{method} {path}",
        "method": method,
        "url": url,
        "path": path,
        "request_body": body,
        "request_headers": {k: ("<redacted>" if k.lower() == "authorization" else v) for k, v in headers.items()},
        "status": status,
        "response_headers": resp_headers,
        "response_text": text[:4000],
        "response_json": parsed,
        "elapsed_s": round(time.time() - started, 3),
        "error": error,
    }
    LOG.append(record)

    if save_as:
        payload = parsed if parsed is not None else {"_raw": text, "_status": status}
        save(save_as, payload)
        save("redacted/" + save_as, redact(payload))

    if error_test:
        ERROR_ROWS.append(
            {
                "endpoint": f"{method} {path}",
                "test": error_test,
                "status": status,
                "response": parsed if parsed is not None else text[:300],
            }
        )

    print(f"[{status}] {method} {path}  ({record['elapsed_s']}s)  {label or ''}")
    if parsed is not None:
        preview = json.dumps(redact(parsed), default=str)
        print("   ", preview[:240])
    elif text:
        print("   ", text[:180].replace("\n", " "))
    return record


def main() -> None:
    ts = int(time.time())
    # 11-digit synthetic IDs derived from timestamp; not real BVN/NIN values.
    bvn_sender = f"9{ts}"[:11]
    bvn_recv = f"8{ts}"[:11]
    nin_a = f"7{ts}"[:11]
    nin_b = f"6{ts}"[:11]
    if len(bvn_sender) < 11:
        bvn_sender = (bvn_sender + "00000000000")[:11]
        bvn_recv = (bvn_recv + "00000000000")[:11]
        nin_a = (nin_a + "00000000000")[:11]
        nin_b = (nin_b + "00000000000")[:11]

    email_a = f"phoenix.test.fintech.{ts}@example.test"
    email_b = f"phoenix.test.fintech.b.{ts}@example.test"
    name_a = "Phoenix Test Fintech"
    name_b = "Phoenix Test Fintech B"
    dob_sender = "1995-06-15"
    dob_recv = "1992-03-20"
    dob_nin = "1990-01-01"
    phone_sender = "08000000001"
    phone_recv = "08000000002"

    meta = {
        "investigated_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "synthetic": {
            "name_a": name_a,
            "email_a": email_a,
            "name_b": name_b,
            "email_b": email_b,
            "bvn_sender": bvn_sender,
            "bvn_recv": bvn_recv,
            "nin_a": nin_a,
            "nin_b": nin_b,
            "dob_sender": dob_sender,
            "dob_recv": dob_recv,
            "dob_nin": dob_nin,
            "note": "All identity values are synthetic test data, not real people.",
        },
    }
    save("run-meta.json", meta)
    print("Synthetic IDs:", json.dumps(meta["synthetic"], indent=2))

    # ------------------------------------------------------------------
    # 1. Base URL / discovery already done; cheap reconfirm + method mixups
    # ------------------------------------------------------------------
    request("GET", "/", save_as="base.json", label="base url")
    request("GET", "/api/docs/", label="swagger ui")
    request(
        "GET",
        "/api/fintech/onboard",
        error_test="GET on POST-only onboard",
        label="wrong method onboard",
    )
    request(
        "POST",
        "/api/accounts",
        body={},
        error_test="POST on GET-only accounts",
        label="wrong method accounts",
    )

    # ------------------------------------------------------------------
    # 2. Onboard Fintech A
    # ------------------------------------------------------------------
    request(
        "POST",
        "/api/fintech/onboard",
        body={},
        error_test="onboard missing all fields",
        label="onboard empty",
        save_as="errors/onboard-empty.json",
    )
    request(
        "POST",
        "/api/fintech/onboard",
        body={"name": name_a, "email": "not-an-email"},
        error_test="onboard invalid email",
        label="onboard bad email",
        save_as="errors/onboard-bad-email.json",
    )
    onboard_a = request(
        "POST",
        "/api/fintech/onboard",
        body={"name": name_a, "email": email_a},
        save_as="onboarding.json",
        label="onboard fintech A",
    )
    oa = onboard_a.get("response_json") or {}
    api_key = oa.get("apiKey")
    api_secret = oa.get("apiSecret")
    bank_code = oa.get("bankCode")
    bank_name = oa.get("bankName")

    dup_onboard = request(
        "POST",
        "/api/fintech/onboard",
        body={"name": name_a, "email": email_a},
        error_test="duplicate fintech email",
        save_as="errors/onboard-duplicate.json",
        label="duplicate onboard email",
    )

    onboard_b = request(
        "POST",
        "/api/fintech/onboard",
        body={"name": name_b, "email": email_b},
        save_as="onboarding-b.json",
        label="onboard fintech B",
    )
    ob = onboard_b.get("response_json") or {}

    # ------------------------------------------------------------------
    # 3. Login / JWT
    # ------------------------------------------------------------------
    request(
        "POST",
        "/api/auth/token",
        body={},
        error_test="login missing credentials",
        save_as="errors/login-empty.json",
    )
    request(
        "POST",
        "/api/auth/token",
        body={"apiKey": "deadbeef", "apiSecret": "cafebabe"},
        error_test="login invalid API credentials",
        save_as="errors/login-invalid.json",
    )
    login_a = request(
        "POST",
        "/api/auth/token",
        body={"apiKey": api_key, "apiSecret": api_secret},
        save_as="login.json",
        label="login fintech A",
    )
    token_a = (login_a.get("response_json") or {}).get("token")
    login_b = request(
        "POST",
        "/api/auth/token",
        body={"apiKey": ob.get("apiKey"), "apiSecret": ob.get("apiSecret")},
        save_as="login-b.json",
        label="login fintech B",
    )
    token_b = (login_b.get("response_json") or {}).get("token")

    jwt_info = None
    if token_a:
        jwt_info = decode_jwt(token_a)
        payload = dict(jwt_info["payload"])
        save("jwt-decoded.json", jwt_info)
        save("redacted/jwt-decoded.json", redact(jwt_info))
        print("JWT header:", json.dumps(jwt_info["header"]))
        print("JWT payload keys:", list(payload.keys()))
        print("JWT payload (no secret):", json.dumps({k: payload[k] for k in payload}))

    request(
        "GET",
        "/api/accounts",
        error_test="missing Authorization header",
        save_as="errors/accounts-no-auth.json",
    )
    request(
        "GET",
        "/api/accounts",
        extra_headers={"Authorization": "Bearer not-a-real-jwt"},
        error_test="invalid JWT",
        save_as="errors/accounts-invalid-jwt.json",
    )
    if token_a:
        request(
            "GET",
            "/api/accounts",
            extra_headers={"Authorization": token_a},
            error_test="Authorization without Bearer prefix",
            save_as="errors/accounts-no-bearer-prefix.json",
        )

    # ------------------------------------------------------------------
    # 4. BVN / NIN insert + validate (auth vs no-auth)
    # ------------------------------------------------------------------
    insert_bvn_body = {
        "bvn": bvn_sender,
        "firstName": "Ada",
        "lastName": "Testperson",
        "dob": dob_sender,
        "phone": phone_sender,
    }
    request(
        "POST",
        "/api/insertBvn",
        body={"bvn": "123", "firstName": "Ada", "lastName": "Testperson", "dob": dob_sender, "phone": phone_sender},
        error_test="insertBvn invalid format",
        save_as="errors/insertBvn-bad-format.json",
    )
    request(
        "POST",
        "/api/insertBvn",
        body={},
        error_test="insertBvn missing fields",
        save_as="errors/insertBvn-empty.json",
    )
    bvn_noauth = request(
        "POST",
        "/api/insertBvn",
        body=insert_bvn_body,
        save_as="insertBvn.json",
        label="insertBvn WITHOUT auth",
    )
    bvn_withauth = request(
        "POST",
        "/api/insertBvn",
        body={
            "bvn": bvn_recv,
            "firstName": "Chidi",
            "lastName": "Testperson",
            "dob": dob_recv,
            "phone": phone_recv,
        },
        token=token_a,
        save_as="insertBvn-with-auth.json",
        label="insertBvn WITH auth (second identity)",
    )
    request(
        "POST",
        "/api/insertBvn",
        body=insert_bvn_body,
        error_test="duplicate BVN identity",
        save_as="errors/insertBvn-duplicate.json",
    )

    nin_body = {
        "nin": nin_a,
        "firstName": "Bola",
        "lastName": "Testperson",
        "dob": dob_nin,
    }
    nin_noauth = request(
        "POST",
        "/api/insertNin",
        body=nin_body,
        save_as="insertNin.json",
        label="insertNin WITHOUT auth",
    )
    request(
        "POST",
        "/api/insertNin",
        body={
            "nin": nin_b,
            "firstName": "Emeka",
            "lastName": "Testperson",
            "dob": dob_nin,
        },
        token=token_a,
        save_as="insertNin-with-auth.json",
        label="insertNin WITH auth",
    )
    request(
        "POST",
        "/api/insertNin",
        body={},
        error_test="insertNin missing fields",
        save_as="errors/insertNin-empty.json",
    )
    request(
        "POST",
        "/api/insertNin",
        body=nin_body,
        error_test="duplicate NIN identity",
        save_as="errors/insertNin-duplicate.json",
    )
    request(
        "POST",
        "/api/insertNin",
        body={"nin": "12", "firstName": "X", "lastName": "Y", "dob": dob_nin},
        error_test="insertNin invalid format",
        save_as="errors/insertNin-bad-format.json",
    )

    val_bvn_noauth = request(
        "POST",
        "/api/validateBvn",
        body={"bvn": bvn_sender},
        save_as="bvn-validation.json",
        label="validateBvn WITHOUT auth",
    )
    val_bvn_auth = request(
        "POST",
        "/api/validateBvn",
        body={"bvn": bvn_sender},
        token=token_a,
        save_as="bvn-validation-with-auth.json",
        label="validateBvn WITH auth",
    )
    request(
        "POST",
        "/api/validateBvn",
        body={"bvn": "00000000000"},
        error_test="validateBvn nonexistent",
        save_as="errors/validateBvn-missing.json",
    )
    request(
        "POST",
        "/api/validateBvn",
        body={"bvn": "abc"},
        error_test="validateBvn invalid format",
        save_as="errors/validateBvn-bad-format.json",
    )

    val_nin_noauth = request(
        "POST",
        "/api/validateNin",
        body={"nin": nin_a},
        save_as="nin-validation.json",
        label="validateNin WITHOUT auth",
    )
    request(
        "POST",
        "/api/validateNin",
        body={"nin": nin_a},
        token=token_a,
        save_as="nin-validation-with-auth.json",
        label="validateNin WITH auth",
    )
    request(
        "POST",
        "/api/validateNin",
        body={"nin": "00000000000"},
        error_test="validateNin unregistered",
        save_as="errors/validateNin-missing.json",
    )
    request(
        "POST",
        "/api/validateNin",
        body={},
        error_test="validateNin missing field",
        save_as="errors/validateNin-empty.json",
    )

    # ------------------------------------------------------------------
    # 5. Account creation
    # ------------------------------------------------------------------
    request(
        "POST",
        "/api/account/create",
        body={"kycType": "bvn", "kycID": bvn_sender, "dob": dob_sender},
        error_test="account create missing Authorization",
        save_as="errors/account-create-no-auth.json",
    )
    request(
        "POST",
        "/api/account/create",
        body={},
        token=token_a,
        error_test="account create missing required fields",
        save_as="errors/account-create-empty.json",
    )
    request(
        "POST",
        "/api/account/create",
        body={"kycType": "passport", "kycID": bvn_sender, "dob": dob_sender},
        token=token_a,
        error_test="account create invalid kycType",
        save_as="errors/account-create-bad-kyctype.json",
    )
    request(
        "POST",
        "/api/account/create",
        body={"kycType": "bvn", "kycID": "00000000000", "dob": dob_sender},
        token=token_a,
        error_test="account create unknown BVN",
        save_as="errors/account-create-unknown-bvn.json",
    )
    request(
        "POST",
        "/api/account/create",
        body={"kycType": "bvn", "kycID": bvn_sender, "dob": "1980-01-01"},
        token=token_a,
        error_test="account create DOB mismatch",
        save_as="errors/account-create-dob-mismatch.json",
    )

    # Swagger example uses uppercase BVN; schema enum in source is lowercase.
    kyc_upper = request(
        "POST",
        "/api/account/create",
        body={"kycType": "BVN", "kycID": bvn_sender, "dob": dob_sender},
        token=token_a,
        save_as="account-create-kyctype-BVN.json",
        label="create account kycType=BVN (swagger example)",
    )
    acct_a1 = None
    if kyc_upper.get("status") == 200:
        acct_a1 = (kyc_upper.get("response_json") or {}).get("account")
        save("account-create.json", kyc_upper.get("response_json"))
        save("redacted/account-create.json", redact(kyc_upper.get("response_json")))
    else:
        kyc_lower = request(
            "POST",
            "/api/account/create",
            body={"kycType": "bvn", "kycID": bvn_sender, "dob": dob_sender},
            token=token_a,
            save_as="account-create.json",
            label="create account kycType=bvn (lowercase)",
        )
        acct_a1 = (kyc_lower.get("response_json") or {}).get("account")

    acct_a2_resp = request(
        "POST",
        "/api/account/create",
        body={"kycType": "bvn", "kycID": bvn_recv, "dob": dob_recv},
        token=token_a,
        save_as="account-create-2.json",
        label="create second account for transfer recipient",
    )
    acct_a2 = (acct_a2_resp.get("response_json") or {}).get("account")

    # If uppercase BVN succeeded, lowercase duplicate of same identity should fail.
    request(
        "POST",
        "/api/account/create",
        body={"kycType": "bvn", "kycID": bvn_sender, "dob": dob_sender},
        token=token_a,
        error_test="duplicate KYC identity on same fintech",
        save_as="errors/account-create-duplicate-kyc.json",
    )

    # NIN-backed account on Fintech B
    nin_acct = request(
        "POST",
        "/api/account/create",
        body={"kycType": "nin", "kycID": nin_a, "dob": dob_nin},
        token=token_b,
        save_as="account-create-nin-b.json",
        label="create NIN account on fintech B",
    )
    acct_b1 = (nin_acct.get("response_json") or {}).get("account")

    # Also try uppercase NIN
    request(
        "POST",
        "/api/account/create",
        body={"kycType": "NIN", "kycID": nin_b, "dob": dob_nin},
        token=token_b,
        save_as="account-create-kyctype-NIN.json",
        label="create account kycType=NIN uppercase",
    )

    acc_no_a1 = (acct_a1 or {}).get("accountNumber")
    acc_no_a2 = (acct_a2 or {}).get("accountNumber")
    acc_no_b1 = (acct_b1 or {}).get("accountNumber")

    # ------------------------------------------------------------------
    # 6. Account list / name enquiry / balance
    # ------------------------------------------------------------------
    accounts_a = request(
        "GET",
        "/api/accounts",
        token=token_a,
        save_as="accounts.json",
        label="list accounts fintech A",
    )
    request(
        "GET",
        "/api/accounts",
        token=token_b,
        save_as="accounts-b.json",
        label="list accounts fintech B",
    )

    if acc_no_a1:
        name_enq = request(
            "GET",
            f"/api/account/name-enquiry/{acc_no_a1}",
            token=token_a,
            save_as="name-enquiry.json",
            label="name enquiry own account",
        )
        # user-documented path variant {accountNo} is the same path if value is the number
        bal_before_a1 = request(
            "GET",
            f"/api/account/balance/{acc_no_a1}",
            token=token_a,
            save_as="balance.json",
            label="balance sender before transfer",
        )
        if acc_no_a2:
            bal_before_a2 = request(
                "GET",
                f"/api/account/balance/{acc_no_a2}",
                token=token_a,
                save_as="balance-recipient-before.json",
                label="balance recipient before transfer",
            )
        else:
            bal_before_a2 = None

        request(
            "GET",
            "/api/account/name-enquiry/0000000000",
            token=token_a,
            error_test="name enquiry nonexistent account",
            save_as="errors/name-enquiry-missing.json",
        )
        request(
            "GET",
            "/api/account/balance/0000000000",
            token=token_a,
            error_test="balance nonexistent account",
            save_as="errors/balance-missing.json",
        )

        # ownership tests
        if acc_no_b1:
            request(
                "GET",
                f"/api/account/name-enquiry/{acc_no_b1}",
                token=token_a,
                save_as="name-enquiry-other-fintech.json",
                label="name enquiry OTHER fintech account (A looking up B)",
            )
            request(
                "GET",
                f"/api/account/balance/{acc_no_b1}",
                token=token_a,
                save_as="balance-other-fintech.json",
                label="balance OTHER fintech account (A looking up B)",
            )
            request(
                "GET",
                f"/api/account/name-enquiry/{acc_no_a1}",
                token=token_b,
                save_as="name-enquiry-b-lookup-a.json",
                label="name enquiry B looking up A",
            )
            request(
                "GET",
                f"/api/account/balance/{acc_no_a1}",
                token=token_b,
                save_as="balance-b-lookup-a.json",
                label="balance B looking up A",
            )
    else:
        name_enq = None
        bal_before_a1 = None
        bal_before_a2 = None

    # ------------------------------------------------------------------
    # 7. Transfer
    # ------------------------------------------------------------------
    request(
        "POST",
        "/api/transfer",
        body={"from": acc_no_a1, "to": acc_no_a2, "amount": 2500},
        error_test="transfer missing Authorization",
        save_as="errors/transfer-no-auth.json",
    )
    request(
        "POST",
        "/api/transfer",
        body={},
        token=token_a,
        error_test="transfer missing required fields",
        save_as="errors/transfer-empty.json",
    )
    request(
        "POST",
        "/api/transfer",
        body={"from": acc_no_a1, "to": acc_no_a2, "amount": -50},
        token=token_a,
        error_test="transfer invalid negative amount",
        save_as="errors/transfer-negative.json",
    )
    request(
        "POST",
        "/api/transfer",
        body={"from": acc_no_a1, "to": acc_no_a2, "amount": "abc"},
        token=token_a,
        error_test="transfer non-numeric amount",
        save_as="errors/transfer-non-numeric.json",
    )
    request(
        "POST",
        "/api/transfer",
        body={"from": acc_no_a1, "to": acc_no_a1, "amount": 100},
        token=token_a,
        error_test="transfer to same account",
        save_as="errors/transfer-same-account.json",
    )
    request(
        "POST",
        "/api/transfer",
        body={"from": "0000000000", "to": acc_no_a2, "amount": 100},
        token=token_a,
        error_test="transfer nonexistent sender",
        save_as="errors/transfer-bad-sender.json",
    )
    if acc_no_a1 and acc_no_a2:
        request(
            "POST",
            "/api/transfer",
            body={"from": acc_no_a1, "to": acc_no_a2, "amount": 20000},
            token=token_a,
            error_test="insufficient funds",
            save_as="errors/transfer-insufficient.json",
        )
        # Fintech B trying to send from A's account
        request(
            "POST",
            "/api/transfer",
            body={"from": acc_no_a1, "to": acc_no_a2, "amount": 100},
            token=token_b,
            error_test="transfer sender not owned by authenticated fintech",
            save_as="errors/transfer-not-owner.json",
        )

        amount = 2500
        before_sender = ((bal_before_a1 or {}).get("response_json") or {}).get("balance")
        before_recv = ((bal_before_a2 or {}).get("response_json") or {}).get("balance")

        transfer = request(
            "POST",
            "/api/transfer",
            body={"from": acc_no_a1, "to": acc_no_a2, "amount": amount},
            token=token_a,
            save_as="transfer.json",
            label="controlled transfer A1 -> A2",
        )
        tx = transfer.get("response_json") or {}
        tx_ref = tx.get("reference") or tx.get("transactionId") or tx.get("_id")

        bal_after_a1 = request(
            "GET",
            f"/api/account/balance/{acc_no_a1}",
            token=token_a,
            save_as="balance-sender-after.json",
            label="balance sender after transfer",
        )
        bal_after_a2 = request(
            "GET",
            f"/api/account/balance/{acc_no_a2}",
            token=token_a,
            save_as="balance-recipient-after.json",
            label="balance recipient after transfer",
        )
        after_sender = (bal_after_a1.get("response_json") or {}).get("balance")
        after_recv = (bal_after_a2.get("response_json") or {}).get("balance")

        math_check = {
            "amount": amount,
            "before_sender": before_sender,
            "after_sender": after_sender,
            "expected_sender": None if before_sender is None else before_sender - amount,
            "sender_ok": (
                before_sender is not None
                and after_sender is not None
                and after_sender == before_sender - amount
            ),
            "before_recipient": before_recv,
            "after_recipient": after_recv,
            "expected_recipient": None if before_recv is None else before_recv + amount,
            "recipient_ok": (
                before_recv is not None
                and after_recv is not None
                and after_recv == before_recv + amount
            ),
            "balance_types": {
                "before_sender": type(before_sender).__name__,
                "after_sender": type(after_sender).__name__,
            },
        }
        save("transfer-math.json", math_check)
        print("TRANSFER MATH:", json.dumps(math_check))

        # Cross-fintech transfer A1 -> B1
        cross = None
        if acc_no_b1:
            bal_b_before = request(
                "GET",
                f"/api/account/balance/{acc_no_b1}",
                token=token_b,
                save_as="balance-b-before-cross.json",
            )
            cross = request(
                "POST",
                "/api/transfer",
                body={"from": acc_no_a1, "to": acc_no_b1, "amount": 500},
                token=token_a,
                save_as="transfer-cross-fintech.json",
                label="cross-fintech transfer A1 -> B1",
            )
            request(
                "GET",
                f"/api/account/balance/{acc_no_a1}",
                token=token_a,
                save_as="balance-a1-after-cross.json",
            )
            request(
                "GET",
                f"/api/account/balance/{acc_no_b1}",
                token=token_b,
                save_as="balance-b-after-cross.json",
            )

        # ------------------------------------------------------------------
        # 8. Transaction tracking
        # ------------------------------------------------------------------
        request(
            "GET",
            "/api/transaction/TX-DOES-NOT-EXIST",
            token=token_a,
            error_test="invalid/nonexistent transaction ID",
            save_as="errors/transaction-missing.json",
        )
        request(
            "GET",
            "/api/transaction/TX-DOES-NOT-EXIST",
            error_test="transaction lookup missing Authorization",
            save_as="errors/transaction-no-auth.json",
        )
        if tx_ref:
            request(
                "GET",
                f"/api/transaction/{tx_ref}",
                token=token_a,
                save_as="transaction.json",
                label="transaction status by reference",
            )
            # Try Mongo _id if present and different
            if tx.get("_id") and tx.get("_id") != tx_ref:
                request(
                    "GET",
                    f"/api/transaction/{tx.get('_id')}",
                    token=token_a,
                    save_as="transaction-by-mongo-id.json",
                    label="transaction lookup by Mongo _id",
                )
            # Can fintech B read A's transaction?
            request(
                "GET",
                f"/api/transaction/{tx_ref}",
                token=token_b,
                save_as="transaction-other-fintech.json",
                label="transaction lookup by other fintech",
            )

    # Amount as string "1000" — type coercion
    if acc_no_a1 and acc_no_a2:
        request(
            "POST",
            "/api/transfer",
            body={"from": acc_no_a1, "to": acc_no_a2, "amount": "100"},
            token=token_a,
            save_as="transfer-amount-string.json",
            label="transfer amount as string",
        )

    # ------------------------------------------------------------------
    # Persist logs
    # ------------------------------------------------------------------
    save("error-table.json", ERROR_ROWS)
    save("request-log.json", redact(LOG))
    save(
        "observed-ids.json",
        redact(
            {
                "fintech_a": {
                    "email": email_a,
                    "apiKey": api_key,
                    "bankCode": bank_code,
                    "bankName": bank_name,
                    "jwt_claims": (jwt_info or {}).get("payload"),
                },
                "fintech_b": {
                    "email": email_b,
                    "bankCode": ob.get("bankCode"),
                    "bankName": ob.get("bankName"),
                },
                "accounts": {
                    "a1": acct_a1,
                    "a2": acct_a2,
                    "b1": acct_b1,
                },
                "identities": meta["synthetic"],
                "duplicate_onboard": dup_onboard.get("response_json"),
                "bvn_insert_noauth_status": bvn_noauth.get("status"),
                "bvn_insert_withauth_status": bvn_withauth.get("status"),
                "nin_insert_noauth_status": nin_noauth.get("status"),
                "validateBvn_noauth_status": val_bvn_noauth.get("status"),
                "validateBvn_withauth_status": val_bvn_auth.get("status"),
                "validateNin_noauth_status": val_nin_noauth.get("status"),
            }
        ),
    )

    # Local secrets file — do not commit
    secrets = {
        "warning": "Synthetic sandbox credentials. Do not commit. Do not reuse outside this investigation.",
        "fintech_a": {
            "email": email_a,
            "apiKey": api_key,
            "apiSecret": api_secret,
            "token": token_a,
            "bankCode": bank_code,
            "bankName": bank_name,
        },
        "fintech_b": {
            "email": email_b,
            "apiKey": ob.get("apiKey"),
            "apiSecret": ob.get("apiSecret"),
            "token": token_b,
            "bankCode": ob.get("bankCode"),
            "bankName": ob.get("bankName"),
        },
    }
    save(".secrets.json", secrets)
    print("\nDone. Responses saved under", OUT)
    print("Error tests:", len(ERROR_ROWS))


if __name__ == "__main__":
    main()
