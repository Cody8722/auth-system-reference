"""
07 Password Spraying — 密碼噴灑攻擊測試

攻擊原理：
  1. 帳號鎖定只看單一 email，旋轉多個帳號可永遠不觸發鎖定
  2. IP rate limit 只看總請求數，旋轉帳號不改變計數，但真實攻擊
     中攻擊者有數千帳號可旋轉，每個帳號每 15 分鐘只打 1 次，
     永遠低於 IP 閾值。

測試用的「假帳號」不需要真實存在：server 驗證失敗就算一次嘗試。
"""
import requests
from config import NODE_URL, PYTHON_URL, EXISTING_EMAIL

WRONG_PASSWORDS = [f"WrongPass!{i:03d}" for i in range(1, 5)]
LOGIN_PATH = "/api/auth/login"

# 旋轉用的假帳號（不需要真實存在）
SPRAY_ACCOUNTS = [
    "victim1@company-example.com",
    "victim2@company-example.com",
]

PASS = 0
FAIL = 0

print("=" * 55)
print("07 Password Spraying — 密碼噴灑攻擊測試")
print("=" * 55)


def check_locked(base_url, email):
    """送一次錯誤密碼，回 429 表示帳號已鎖定。"""
    r = requests.post(
        base_url + LOGIN_PATH,
        json={"email": email, "password": "CheckLock!999"},
        timeout=5,
    )
    return r.status_code == 429


def test_lockout_bypass(base_url, name):
    global PASS, FAIL
    url = base_url + LOGIN_PATH
    print(f"\n[{name}] 帳號鎖定繞過測試")
    print(f"  策略：2 帳號 x 4 次 = 8 次（鎖定閾值 5 次，IP 閾值 10 次）")

    attempts = []
    for pw in WRONG_PASSWORDS:
        for email in SPRAY_ACCOUNTS:
            attempts.append((email, pw))

    for i, (email, pw) in enumerate(attempts, 1):
        try:
            r = requests.post(url, json={"email": email, "password": pw}, timeout=5)
            short = email.split("@")[0]
            status = r.status_code
            print(f"  Attempt {i:2d} [{short}]: {status}")
        except Exception as e:
            print(f"  Attempt {i:2d}: ERROR {e}")
            return

    print()
    all_safe = True
    for email in SPRAY_ACCOUNTS:
        locked = check_locked(base_url, email)
        short = email.split("@")[0]
        if locked:
            print(f"  {short} 被鎖定了？ 是 (429)")
            PASS += 1
        else:
            print(f"  {short} 被鎖定了？ 否 ⚠ VULNERABLE (帳號鎖定被繞過)")
            FAIL += 1
            all_safe = False

    if all_safe:
        print(f"  結論：帳號鎖定有效 ✓")
    else:
        print(f"  結論：旋轉帳號可繞過帳號鎖定 ⚠ VULNERABLE")


def test_rate_limit_spray(base_url, name, ip_threshold):
    global PASS, FAIL
    url = base_url + LOGIN_PATH
    print(f"\n[{name}] Rate Limit 低速噴灑測試")
    print(f"  策略：2 帳號旋轉，各 4 次，共 8 次 < IP 閾值 {ip_threshold}")

    passed = 0
    blocked = 0
    attempts = []
    for pw in WRONG_PASSWORDS:
        for email in SPRAY_ACCOUNTS:
            attempts.append((email, pw))

    for i, (email, pw) in enumerate(attempts, 1):
        try:
            r = requests.post(url, json={"email": email, "password": pw}, timeout=5)
            short = email.split("@")[0]
            if r.status_code == 429:
                print(f"  Attempt {i:2d} [{short}]: 429 (blocked)")
                blocked += 1
            else:
                print(f"  Attempt {i:2d} [{short}]: {r.status_code}")
                passed += 1
        except Exception as e:
            print(f"  Attempt {i:2d}: ERROR {e}")

    print()
    if blocked == 0:
        print(f"  全部 {passed} 次通過，rate limit 未觸發 ⚠ VULNERABLE")
        print(f"  真實攻擊中，攻擊者用數千帳號旋轉，每帳號每 15 分鐘打 1 次，永遠不觸發 IP 限制")
        FAIL += 1
    else:
        print(f"  {blocked} 次被封鎖 ✓ DEFENDED")
        PASS += 1

    print(f"  修補建議：")
    print(f"    - 加入全域 IP 失敗計數（不分 email）")
    print(f"    - 或使用 CAPTCHA / 漸進延遲（exponential backoff）")


# Python：測帳號鎖定繞過（Python 有帳號鎖定，Node.js 沒有）
test_lockout_bypass(PYTHON_URL, "Python")

# 兩版：測 rate limit 低速噴灑
test_rate_limit_spray(NODE_URL, "Node.js", ip_threshold=10)
test_rate_limit_spray(PYTHON_URL, "Python", ip_threshold=10)

print()
print(f"結果：{PASS} 個防禦有效，{FAIL} 個可被繞過")
