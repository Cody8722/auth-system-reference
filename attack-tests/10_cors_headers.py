"""
10 CORS Headers — Wildcard CORS 設定

兩版 CORS_ORIGIN 預設 '*'，任意 origin 都能發跨域請求。
credentials 未啟用（降低 CSRF 風險），但寬鬆設定仍值得記錄。

測試：
  - 帶 Origin: https://evil-site.com 請求 /api/status
  - 帶 Origin: null（data: URL / file:// 場景）
  - 檢查 Access-Control-Allow-Origin 是否為 *
"""
import requests
from config import NODE_URL, PYTHON_URL

PASS = 0
FAIL = 0

print("=" * 55)
print("10 CORS Headers — Wildcard CORS 測試")
print("=" * 55)


def test_cors(base_url, name):
    global PASS, FAIL
    print(f"\n[{name}] CORS 設定檢查")

    cases = [
        ("https://evil-site.com", "惡意 origin"),
        ("null",                  "null origin（file:// / data: URL）"),
    ]

    for origin, label in cases:
        try:
            r = requests.get(
                base_url + "/api/status",
                headers={"Origin": origin},
                timeout=5,
            )
            acao = r.headers.get("Access-Control-Allow-Origin", "（無此 header）")
            allow_creds = r.headers.get("Access-Control-Allow-Credentials", "false")
            print(f"\n  Origin: {origin}  ({label})")
            print(f"    Access-Control-Allow-Origin      : {acao}")
            print(f"    Access-Control-Allow-Credentials : {allow_creds}")

            if acao == "*":
                if allow_creds.lower() == "true":
                    print(f"    => Wildcard + credentials=true ⚠ CRITICAL（瀏覽器實際會阻擋，但設定矛盾）")
                    FAIL += 1
                else:
                    print(f"    => Wildcard，credentials 未啟用 ⚠ NOTED（開發用預設，正式環境請收窄）")
                    FAIL += 1
            elif acao in ("", "（無此 header）"):
                print(f"    => 無 CORS header，跨域請求會被瀏覽器阻擋 ✓")
                PASS += 1
            else:
                print(f"    => 限定 origin ✓ DEFENDED")
                PASS += 1

        except Exception as e:
            print(f"  {label}：錯誤 {e}")

    print(f"\n  修補建議：")
    print(f"    設定 CORS_ORIGIN 為正式前端 origin（例如 https://your-app.com）")
    print(f"    Node.js : CORS_ORIGIN=https://your-app.com（server.js 已讀取此變數）")
    print(f"    Flask   : CORS_ORIGIN=https://your-app.com（app.py 已讀取此變數）")


test_cors(NODE_URL, "Node.js")
test_cors(PYTHON_URL, "Python")

print()
print(f"結果：{PASS} 個設定收窄，{FAIL} 個使用 wildcard（含 NOTED）")
