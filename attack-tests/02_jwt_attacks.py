"""
02_jwt_attacks.py — JWT 偽造攻擊測試

攻擊手法：
  1. Algorithm = none（移除簽章繞過驗證）
  2. 錯誤 secret 偽造合法格式 token
  3. 竄改 payload（不重新簽名）
  4. 過期 token

依賴：pip install requests pyjwt
"""

import base64
import json
import time
import requests
import jwt as pyjwt
from config import NODE_URL, PYTHON_URL, JWT_SECRET

RESULTS = []
VERIFY_PATH = "/api/auth/verify"


def _req(url, token):
    return requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=5)


def _check(label, node_status, python_status, expect=401):
    node_ok   = node_status == expect
    python_ok = python_status == expect
    mark_n = "✓" if node_ok else "✗"
    mark_p = "✓" if python_ok else "✗"
    print(f"  {mark_n} Node   {label}: {node_status}  |  {mark_p} Python: {python_status}")
    RESULTS.extend([node_ok, python_ok])


def make_none_alg_token():
    payload = {"user_id": "000000000000000000000001", "email": "hacker@evil.com",
               "name": "Hacker", "type": "access", "exp": int(time.time()) + 3600}
    header  = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=")
    body    = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    return f"{header.decode()}.{body.decode()}."


def make_wrong_secret_token():
    payload = {"user_id": "000000000000000000000001", "email": "hacker@evil.com",
               "name": "Hacker", "type": "access"}
    return pyjwt.encode(payload, "totally-wrong-secret-key-that-is-long-enough", algorithm="HS256")


def make_tampered_token():
    # 先產生合法結構（用錯 secret，反正目的是竄改 payload）
    payload = {"user_id": "999999999999999999999999", "email": "hacked@evil.com",
               "name": "Admin", "type": "access", "exp": int(time.time()) + 3600}
    body    = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    # 隨便拼一個合法 header + 合法 signature（不匹配 payload）
    header  = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=")
    fake_sig = base64.urlsafe_b64encode(b"fakefakefakefake").rstrip(b"=")
    return f"{header.decode()}.{body.decode()}.{fake_sig.decode()}"


def make_expired_token():
    payload = {"user_id": "000000000000000000000001", "email": "test@example.com",
               "name": "Test", "type": "access",
               "iat": int(time.time()) - 100, "exp": int(time.time()) - 1}
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


def run():
    print("=" * 55)
    print("02 JWT 偽造攻擊測試")
    print("=" * 55)
    print("（所有攻擊預期都應得 401 — 防禦成功）\n")

    node_url   = NODE_URL   + VERIFY_PATH
    python_url = PYTHON_URL + VERIFY_PATH

    try:
        requests.get(node_url, headers={"Authorization": "Bearer test"}, timeout=3)
        node_up = True
    except requests.exceptions.ConnectionError:
        node_up = False
        print("  ！Node.js server 未啟動，跳過\n")

    try:
        requests.get(python_url, headers={"Authorization": "Bearer test"}, timeout=3)
        python_up = True
    except requests.exceptions.ConnectionError:
        python_up = False
        print("  ！Python server 未啟動，跳過\n")

    if not node_up and not python_up:
        return

    def both(token):
        ns = _req(node_url,   token).status_code if node_up   else "N/A"
        ps = _req(python_url, token).status_code if python_up else "N/A"
        return ns, ps

    ns, ps = both(make_none_alg_token())
    _check("None algorithm       ", ns, ps)

    ns, ps = both(make_wrong_secret_token())
    _check("Wrong secret         ", ns, ps)

    ns, ps = both(make_tampered_token())
    _check("Tampered payload     ", ns, ps)

    ns, ps = both(make_expired_token())
    _check("Expired token        ", ns, ps)

    passed = sum(RESULTS)
    total  = len(RESULTS)
    print(f"\n結果：{passed}/{total} 通過")


if __name__ == "__main__":
    run()
