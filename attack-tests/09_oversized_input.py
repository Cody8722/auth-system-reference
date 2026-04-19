"""
09 Oversized Input — 超大輸入 / 無請求大小限制

Flask 預設無 MAX_CONTENT_LENGTH，攻擊者可送超大 body 消耗伺服器資源。
Node.js express.json() 預設限制 100kb，相對安全。

測試：送 200KB body（> Flask 16KB 限制，> Node.js 100KB 限制）。
200KB 在 loopback 傳輸 < 1ms，不會造成連線殘留問題。
  回應 413 = 有保護；400/422 = 解析失敗但接收了；200 = 完全無保護；timeout = 最糟
"""
import requests
from config import NODE_URL, PYTHON_URL

PASS = 0
FAIL = 0

# 200 KB — 超過 Flask 16 KB 限制和 Node.js 100 KB 限制
BODY_SIZE = 200 * 1024

print("=" * 55)
print("09 Oversized Input — 超大輸入限制測試")
print("=" * 55)


def test_oversized_login(base_url, name, timeout=8):
    global PASS, FAIL
    print(f"\n[{name}] 超大 password（200 KB）— /api/auth/login")
    payload = {"email": "test@example.com", "password": "A" * BODY_SIZE}
    try:
        r = requests.post(base_url + "/api/auth/login", json=payload, timeout=timeout)
        code = r.status_code
        if code == 413:
            print(f"  回應 {code} — 請求被拒絕 ✓ DEFENDED")
            PASS += 1
        elif code in (400, 422):
            print(f"  回應 {code} — 解析失敗（仍接收到 body）⚠ PARTIAL")
            FAIL += 1
        else:
            print(f"  回應 {code} — 伺服器完全接受超大輸入 ⚠ VULNERABLE")
            FAIL += 1
    except requests.exceptions.Timeout:
        print(f"  Timeout — 伺服器掛起，無大小限制 ⚠ VULNERABLE")
        FAIL += 1
    except Exception as e:
        print(f"  錯誤：{e}")


def test_oversized_register(base_url, name, timeout=8):
    global PASS, FAIL
    print(f"\n[{name}] 超大 body（200 KB）— /api/auth/register")
    payload = {"email": "big@example.com", "password": "B" * BODY_SIZE, "name": "Test"}
    try:
        r = requests.post(base_url + "/api/auth/register", json=payload, timeout=timeout)
        code = r.status_code
        if code == 413:
            print(f"  回應 {code} — 請求被拒絕 ✓ DEFENDED")
            PASS += 1
        elif code == 404:
            print(f"  回應 {code} — 端點不存在（跳過）")
        elif code in (400, 422):
            print(f"  回應 {code} — 解析失敗（仍接收到 body）⚠ PARTIAL")
            FAIL += 1
        else:
            print(f"  回應 {code} — 伺服器完全接受超大輸入 ⚠ VULNERABLE")
            FAIL += 1
    except requests.exceptions.Timeout:
        print(f"  Timeout — 伺服器掛起，無大小限制 ⚠ VULNERABLE")
        FAIL += 1
    except Exception as e:
        print(f"  錯誤：{e}")


print("\n修補建議：")
print("  Node.js : app.use(express.json({ limit: '10kb' }))")
print("  Flask   : app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # 16 KB")

test_oversized_login(NODE_URL, "Node.js")
test_oversized_login(PYTHON_URL, "Python")
test_oversized_register(NODE_URL, "Node.js")
test_oversized_register(PYTHON_URL, "Python")

print()
print(f"結果：{PASS} 個有保護，{FAIL} 個無限制（含 timeout）")
