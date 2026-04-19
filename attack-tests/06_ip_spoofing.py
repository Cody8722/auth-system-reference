"""
06 X-Forwarded-For IP 偽造攻擊測試

攻擊原理：
  兩個實作都信任 X-Forwarded-For header 作為 rate limit key。
  攻擊者每次請求偽造不同 IP，繞過 IP-based rate limit，實現無限暴力破解。
"""
import requests
from config import NODE_URL, PYTHON_URL, EXISTING_EMAIL

WRONG_PASSWORD = "WrongPassword!999"
LOGIN_PATH = "/api/auth/login"
PAYLOAD = {"email": EXISTING_EMAIL, "password": WRONG_PASSWORD}

PASS = 0
FAIL = 0

print("=" * 55)
print("06 X-Forwarded-For IP 偽造 / Rate Limit 繞過測試")
print("=" * 55)


def test_xff_bypass(base_url, name, trigger_limit):
    global PASS, FAIL
    url = base_url + LOGIN_PATH
    print(f"\n[{name}] IP 偽造繞過測試")

    # 步驟一：打到被封
    print(f"  步驟一：正常打到 rate limit...")
    last_status = None
    for i in range(trigger_limit + 2):
        try:
            r = requests.post(url, json=PAYLOAD, timeout=5)
            last_status = r.status_code
        except Exception as e:
            print(f"    Request {i+1}: ERROR {e}")
            return

    if last_status == 429:
        print(f"  Rate limit 觸發確認：{last_status} ✓")
        PASS += 1
    else:
        print(f"  Rate limit 未觸發：{last_status} ✗ (跳過後續測試)")
        FAIL += 1
        return

    # 步驟二：XFF 偽造繞過
    print(f"  步驟二：使用假 X-Forwarded-For 繞過...")
    bypassed = 0
    for i in range(1, 6):
        fake_ip = f"203.{i}.{i}.{i}"
        headers = {"X-Forwarded-For": fake_ip}
        try:
            r = requests.post(url, json=PAYLOAD, headers=headers, timeout=5)
            if r.status_code == 401:
                print(f"    Fake IP {fake_ip} → {r.status_code} ⚠ VULNERABLE (rate limit bypassed)")
                bypassed += 1
                FAIL += 1
            elif r.status_code == 429:
                print(f"    Fake IP {fake_ip} → {r.status_code} ✓ DEFENDED")
                PASS += 1
            else:
                print(f"    Fake IP {fake_ip} → {r.status_code} ?")
        except Exception as e:
            print(f"    Fake IP {fake_ip} → ERROR {e}")

    if bypassed == 0:
        print(f"  結論：IP 偽造無效，rate limit 防禦有效 ✓")
    else:
        print(f"  結論：{bypassed}/5 次成功繞過 ⚠ VULNERABLE")
        print(f"  修補建議：")
        if "3001" in base_url:
            print(f"    Node.js — 移除 app.set('trust proxy', 1)")
            print(f"             或改用 keyGenerator: (req) => req.socket.remoteAddress")
        else:
            print(f"    Python  — 移除 get_rate_limit_key() 中的 X-Forwarded-For 信任")
            print(f"             改為直接使用 get_remote_address()")


# Node.js: authLimiter = 10 次/15分，打 11 次觸發
test_xff_bypass(NODE_URL, "Node.js", trigger_limit=11)

# Python: 10 次/分，打 11 次觸發
test_xff_bypass(PYTHON_URL, "Python", trigger_limit=11)

print()
print(f"結果：{PASS} 個防禦有效，{FAIL} 個可被繞過")
