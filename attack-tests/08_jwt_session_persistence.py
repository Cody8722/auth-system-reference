"""
08 JWT Session Persistence — Token 改密碼後不失效

設計限制：
  兩個實作都使用無狀態 JWT，不維護黑名單，不在 DB 記錄密碼版本。
  攻擊者取得 JWT 後，即使受害者改密碼，token 在 7 天到期前仍然有效。

測試：登入取得 token，驗證有效，並分析 /verify 是否有版本檢查。
"""
import requests
import base64
import json
from config import NODE_URL, PYTHON_URL, EXISTING_EMAIL, EXISTING_PASSWORD

PASS = 0
FAIL = 0

print("=" * 55)
print("08 JWT Session Persistence — Token 不失效測試")
print("=" * 55)


def decode_jwt_payload(token):
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    padding = 4 - len(parts[1]) % 4
    padded = parts[1] + "=" * padding
    try:
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}


def test_session_persistence(base_url, name):
    global PASS, FAIL
    print(f"\n[{name}] JWT Session Persistence 測試")

    # 步驟一：登入取得 token
    r = requests.post(
        base_url + "/api/auth/login",
        json={"email": EXISTING_EMAIL, "password": EXISTING_PASSWORD},
        timeout=5,
    )
    if r.status_code != 200:
        print(f"  登入失敗：{r.status_code} — 跳過（帳號可能不存在或密碼錯誤）")
        return

    token = r.json().get("token") or r.json().get("access_token")
    if not token:
        print(f"  無法取得 token，跳過")
        return
    print(f"  登入成功，取得 JWT ✓")

    # 步驟二：解析 JWT payload
    payload = decode_jwt_payload(token)
    has_pwd_version = "pwd_version" in payload or "password_version" in payload
    has_iat = "iat" in payload
    print(f"  JWT payload 欄位：{list(payload.keys())}")
    if has_pwd_version:
        print(f"  JWT 含密碼版本欄位 ✓ DEFENDED")
        PASS += 1
    else:
        print(f"  JWT 不含密碼版本欄位 ⚠ NOTED")
        FAIL += 1

    # 步驟三：呼叫 /verify 確認 token 有效
    rv = requests.get(
        base_url + "/api/auth/verify",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    print(f"  /verify 回應：{rv.status_code}")
    if rv.status_code == 200:
        print(f"  Token 目前有效 ✓")
        PASS += 1
    else:
        print(f"  Token 無效，無法測試")
        return

    # 步驟四：靜態分析
    print(f"\n  靜態分析：")
    if name == "Node.js":
        print(f"    /verify 只驗 JWT 簽章與有效期，不查 DB")
        print(f"    => 密碼更改後舊 token 在 7 天內仍然有效 ⚠ VULNERABLE")
    else:
        print(f"    /verify 查 DB 確認帳號存在，但不比對 password_last_updated vs JWT iat")
        print(f"    => 密碼更改後舊 token 仍然有效 ⚠ VULNERABLE")
    FAIL += 1

    print(f"\n  修補建議（擇一）：")
    print(f"    1. JWT 加入 pwd_version 欄位，改密碼時遞增，/verify 比對")
    print(f"    2. Redis blacklist 存放已失效 token")
    print(f"    3. 縮短 token 有效期（如 15 分鐘）+ refresh token 機制")


test_session_persistence(NODE_URL, "Node.js")
test_session_persistence(PYTHON_URL, "Python")

print()
print(f"結果：{PASS} 個檢查通過，{FAIL} 個問題（含設計限制）")
