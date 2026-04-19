"""
04_enumeration.py — 帳號枚舉攻擊測試

測試一：Login 回應訊息對比
  存在帳號 vs 不存在帳號送錯誤密碼，回應內容應完全相同

測試二：Forgot-password 回應對比
  存在 email vs 不存在 email，回應內容應完全相同

測試三：Login Timing 分析
  存在帳號需要做 PBKDF2 hash 驗算（慢），不存在帳號直接返回（快）
  若時間差顯著 → timing oracle，可用來枚舉帳號是否存在
"""

import time
import requests
from config import NODE_URL, PYTHON_URL, EXISTING_EMAIL, NONEXIST_EMAIL

RESULTS = []
SAMPLES = 5  # timing 測試取樣次數


def _check(label, ok):
    mark = "✓" if ok else "⚠ RISK"
    print(f"  {mark}  {label}")
    RESULTS.append(ok)


def test_login_message(base_url, server_name):
    url = f"{base_url}/api/auth/login"
    wrong_pw = "WrongPassword_00000!"

    try:
        r_exist   = requests.post(url, json={"email": EXISTING_EMAIL, "password": wrong_pw}, timeout=5)
        r_nonexist= requests.post(url, json={"email": NONEXIST_EMAIL, "password": wrong_pw}, timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"  ！{server_name} 無法連線")
        return

    same_status = r_exist.status_code == r_nonexist.status_code
    same_body   = r_exist.text == r_nonexist.text

    _check(f"[{server_name}] Login 狀態碼相同（{r_exist.status_code} vs {r_nonexist.status_code}）", same_status)
    _check(f"[{server_name}] Login 回應內容相同", same_body)

    if not same_body:
        print(f"    存在帳號回應：{r_exist.text[:80]}")
        print(f"    不存在帳號：  {r_nonexist.text[:80]}")


def test_forgot_password_message(base_url, server_name):
    url = f"{base_url}/api/auth/forgot-password"

    try:
        r_exist   = requests.post(url, json={"email": EXISTING_EMAIL},  timeout=5)
        r_nonexist= requests.post(url, json={"email": NONEXIST_EMAIL},  timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"  ！{server_name} 無法連線")
        return

    same_status = r_exist.status_code == r_nonexist.status_code
    same_body   = r_exist.text == r_nonexist.text

    _check(f"[{server_name}] Forgot-pwd 狀態碼相同（{r_exist.status_code} vs {r_nonexist.status_code}）", same_status)
    _check(f"[{server_name}] Forgot-pwd 回應內容相同", same_body)

    if not same_body:
        print(f"    存在帳號：{r_exist.text[:80]}")
        print(f"    不存在：  {r_nonexist.text[:80]}")


def measure_timing(url, email, password, n):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            requests.post(url, json={"email": email, "password": password}, timeout=5)
        except requests.exceptions.ConnectionError:
            return None
        times.append((time.perf_counter() - t0) * 1000)
    return sum(times) / len(times)


def test_timing(base_url, server_name):
    url = f"{base_url}/api/auth/login"
    wrong_pw = "WrongPassword_00000!"
    print(f"\n  [{server_name}] Timing 分析（各 {SAMPLES} 次平均）")

    t_exist   = measure_timing(url, EXISTING_EMAIL, wrong_pw, SAMPLES)
    t_nonexist= measure_timing(url, NONEXIST_EMAIL, wrong_pw, SAMPLES)

    if t_exist is None or t_nonexist is None:
        print(f"    ！{server_name} 無法連線")
        return

    diff = abs(t_exist - t_nonexist)
    print(f"    存在帳號平均：    {t_exist:.1f} ms")
    print(f"    不存在帳號平均：  {t_nonexist:.1f} ms")
    print(f"    差距：            {diff:.1f} ms")

    # PBKDF2 驗算通常 > 50ms，若差距明顯可用來枚舉
    ok = diff < 80
    _check(f"[{server_name}] Timing 差距 < 80ms（目前 {diff:.0f}ms）", ok)
    if not ok:
        print(f"    ※ 差距顯著，攻擊者可透過回應時間判斷帳號是否存在")


if __name__ == "__main__":
    print("=" * 55)
    print("04 帳號枚舉攻擊測試")
    print("=" * 55)

    for url, name in [(NODE_URL, "Node.js"), (PYTHON_URL, "Python")]:
        print(f"\n── {name} 回應訊息一致性 ──")
        test_login_message(url, name)
        test_forgot_password_message(url, name)

    print()
    for url, name in [(NODE_URL, "Node.js"), (PYTHON_URL, "Python")]:
        test_timing(url, name)

    passed = sum(RESULTS)
    total  = len(RESULTS)
    print(f"\n結果：{passed}/{total} 通過")
