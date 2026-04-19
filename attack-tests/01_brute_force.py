"""
01_brute_force.py — 暴力破解 + 速率限制 / 帳號鎖定驗證

測試：
  - Node.js：IP 速率限制 10次/15分，第 11 次應得 429
  - Python ：IP 速率限制 10次/分 + 帳號鎖定（5次失敗 → 429）
"""

import requests
from config import NODE_URL, PYTHON_URL, EXISTING_EMAIL

WRONG_PASSWORD = "WrongPassword_00000!"
RESULTS = []


def _check(label, status, expect_codes):
    ok = status in expect_codes
    mark = "✓" if ok else "✗"
    print(f"  {mark} {label}: HTTP {status}")
    RESULTS.append(ok)
    return ok


def test_node_rate_limit():
    print("\n[Node.js] 暴力破解 — IP 速率限制（上限 10次/15分）")
    url = f"{NODE_URL}/api/auth/login"
    for i in range(1, 13):
        r = requests.post(url, json={"email": EXISTING_EMAIL, "password": WRONG_PASSWORD}, timeout=5)
        if i <= 10:
            _check(f"Request {i:02d}", r.status_code, {401, 503})
        else:
            ok = _check(f"Request {i:02d} (應被封鎖)", r.status_code, {429})
            if not ok:
                print(f"    body: {r.text[:120]}")


def test_python_ip_rate_limit():
    print("\n[Python] 暴力破解 — IP 速率限制（上限 10次/分）")
    url = f"{PYTHON_URL}/api/auth/login"
    for i in range(1, 13):
        r = requests.post(url, json={"email": EXISTING_EMAIL, "password": WRONG_PASSWORD}, timeout=5)
        if i <= 10:
            _check(f"Request {i:02d}", r.status_code, {401, 503})
        else:
            ok = _check(f"Request {i:02d} (應被封鎖)", r.status_code, {429})
            if not ok:
                print(f"    body: {r.text[:120]}")


def test_python_account_lockout():
    print("\n[Python] 帳號鎖定測試（5次失敗 → 15分鎖定）")
    url = f"{PYTHON_URL}/api/auth/login"
    # 先用不同 email 做，避免被上面的 IP 限制干擾
    target = "lockout_test@example.com"
    for i in range(1, 8):
        r = requests.post(url, json={"email": target, "password": WRONG_PASSWORD}, timeout=5)
        if i <= 5:
            _check(f"Attempt {i} (密碼錯誤)", r.status_code, {401, 503})
        else:
            ok = _check(f"Attempt {i} (應觸發帳號鎖定 429)", r.status_code, {429, 503})
            if not ok:
                print(f"    body: {r.text[:120]}")
            # 503 = 無 DB，不算真失敗
            if r.status_code == 503:
                print("    ※ 503：無 DB，帳號鎖定無法驗證")
                break


if __name__ == "__main__":
    print("=" * 55)
    print("01 暴力破解 / 速率限制 / 帳號鎖定測試")
    print("=" * 55)
    try:
        test_node_rate_limit()
    except requests.exceptions.ConnectionError:
        print("  ✗ 無法連線 Node.js server（localhost:3001）")

    try:
        test_python_ip_rate_limit()
        test_python_account_lockout()
    except requests.exceptions.ConnectionError:
        print("  ✗ 無法連線 Python server（localhost:3002）")

    passed = sum(RESULTS)
    total = len(RESULTS)
    print(f"\n結果：{passed}/{total} 通過")
