# Attack Tests — 攻防測試腳本

此目錄已加入 `.gitignore`，不進版控。

## 前置條件

```bash
pip install requests pyjwt
```

在 `config.py` 設定：
- `JWT_SECRET`：與 server `.env` 相同的值（供 JWT 攻擊偽造用）
- `EXISTING_EMAIL` / `EXISTING_PASSWORD`：資料庫中實際存在的帳號

## 啟動 Server

```bash
# Node.js（Port 3001）
node node-express/server.js

# Python（Port 3002）
python python-flask/app.py
```

大部分測試需要真實 MongoDB 連線。若 server 沒有 DB，login/register 等端點會回 503，
NoSQL injection 測試無法真正驗證繞過。

## 執行

```bash
cd attack-tests

python 01_brute_force.py     # 暴力破解 + 速率限制 + 帳號鎖定
python 02_jwt_attacks.py     # JWT 偽造（none alg / 錯 secret / 竄改 payload / 過期）
python 03_nosql_injection.py # MongoDB operator injection
python 04_enumeration.py     # 帳號枚舉（回應訊息 + timing 分析）
python 05_reset_token.py     # Reset token 隨機性靜態分析
```

## 結果說明

| 符號 | 意義 |
|------|------|
| ✓ | 防禦有效 |
| ✗ | 預期防禦但失敗 |
| ⚠ VULNERABLE | 成功繞過防禦（漏洞） |
| ⚠ RISK | 潛在風險，建議改善 |

## 已知弱點摘要

| 類型 | Node.js | Python |
|------|---------|--------|
| NoSQL injection | 無明確過濾 | 無明確過濾 |
| 帳號鎖定 | 缺失（僅 IP 限制） | 有，但 in-memory（重啟清零） |
| Timing oracle | PBKDF2 驗算時間差可能洩漏帳號存在 | 同左 |
