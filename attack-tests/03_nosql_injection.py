"""
03_nosql_injection.py — MongoDB Operator Injection 測試

測試 email / password / token 欄位是否接受 MongoDB 查詢運算子。

若回應 200/201 代表注入成功繞過防禦 → ⚠️ VULNERABLE
若回應 400/401/422/500/503 代表防禦有效 → ✓ DEFENDED

已知狀況（探索結果）：
  - 兩個實作都沒有明確過濾 $gt / $ne 等運算子
  - Node.js 直接 req.body → MongoDB query
  - Python 直接 data.get("email") → MongoDB query
"""

import requests
from config import NODE_URL, PYTHON_URL

RESULTS = []
SAFE_CODES  = {400, 401, 403, 422, 500, 503}
VULN_CODES  = {200, 201}


def _check(label, server, status):
    if status in VULN_CODES:
        mark = "⚠ VULNERABLE"
        ok = False
    elif status in SAFE_CODES:
        mark = "✓ DEFENDED"
        ok = True
    else:
        mark = f"? HTTP {status}"
        ok = False
    print(f"  {mark}  [{server}] {label} → {status}")
    RESULTS.append(ok)


def test_login_email_injection(base_url, server_name):
    url = f"{base_url}/api/auth/login"
    payloads = [
        ("email $gt injection",   {"email": {"$gt": ""},     "password": "anything"}),
        ("email $ne injection",   {"email": {"$ne": "none"}, "password": "anything"}),
        ("email $regex injection",{"email": {"$regex": ".*"},"password": "anything"}),
    ]
    for label, body in payloads:
        try:
            r = requests.post(url, json=body, timeout=5)
            _check(label, server_name, r.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"  ！{server_name} 無法連線或逾時")
            return


def test_login_password_injection(base_url, server_name):
    url = f"{base_url}/api/auth/login"
    payloads = [
        ("password $gt injection", {"email": "test@example.com", "password": {"$gt": ""}}),
        ("password $ne injection", {"email": "test@example.com", "password": {"$ne": "x"}}),
    ]
    for label, body in payloads:
        try:
            r = requests.post(url, json=body, timeout=5)
            _check(label, server_name, r.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"  ！{server_name} 無法連線或逾時")
            return


def test_reset_token_injection(base_url, server_name):
    url = f"{base_url}/api/auth/reset-password"
    payloads = [
        ("token $gt injection",  {"token": {"$gt": ""},     "new_password": "NewP@ss2026!XyZ"}),
        ("token $exists inject", {"token": {"$exists": True},"new_password": "NewP@ss2026!XyZ"}),
    ]
    for label, body in payloads:
        try:
            r = requests.post(url, json=body, timeout=5)
            _check(label, server_name, r.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print(f"  ！{server_name} 無法連線或逾時")
            return


if __name__ == "__main__":
    print("=" * 55)
    print("03 NoSQL Injection 攻擊測試")
    print("=" * 55)
    print("（✓ DEFENDED = 防禦有效；⚠ VULNERABLE = 可能被繞過）\n")

    for url, name in [(NODE_URL, "Node.js"), (PYTHON_URL, "Python")]:
        print(f"── {name} Login Email Injection ──")
        test_login_email_injection(url, name)
        print(f"\n── {name} Login Password Injection ──")
        test_login_password_injection(url, name)
        print(f"\n── {name} Reset Token Injection ──")
        test_reset_token_injection(url, name)
        print()

    passed = sum(RESULTS)
    total  = len(RESULTS)
    vuln   = total - passed
    print(f"結果：{passed}/{total} 防禦有效，{vuln} 個潛在弱點")
    if vuln:
        print("建議：在 server 端驗證欄位型別（typeof email !== 'string' → 400）")
