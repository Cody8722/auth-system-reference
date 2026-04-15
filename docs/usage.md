# 使用說明 — Auth System Reference

> 本文件涵蓋目前已有的各語言實作（Node.js Port 3001、Python Port 3002）的完整操作說明。  
> 未來新增的實作將以相同的端點設計為基礎，通用章節（JWT、密碼規則、錯誤代碼等）同樣適用。

---

## 目錄

1. [環境需求](#1-環境需求)
2. [快速啟動](#2-快速啟動)
3. [環境變數說明](#3-環境變數說明)
4. [使用流程](#4-使用流程)
5. [API 端點參考](#5-api-端點參考)
   - [POST /api/auth/login](#post-apiauthlogin)
   - [POST /api/auth/logout](#post-apiauthlogout)
   - [GET /api/auth/verify](#get-apiauthverify)
   - [POST /api/auth/forgot-password](#post-apiauthforgot-password)
   - [POST /api/auth/reset-password](#post-apiauthreset-password)
   - [POST /api/auth/register（Python 版）](#post-apiauthregister--python-版)
   - [POST /api/auth/validate-password（Python 版）](#post-apiauthvalidate-password--python-版)
   - [GET /api/status](#get-apistatus)
6. [JWT Token 說明](#6-jwt-token-說明)
7. [密碼規則（Python 版）](#7-密碼規則--python-版)
8. [速率限制與帳號鎖定](#8-速率限制與帳號鎖定)
9. [錯誤代碼速查表](#9-錯誤代碼速查表)
10. [各版實作差異（現有實作對照）](#10-各版實作差異現有實作對照)

---

## 1. 環境需求

| 項目 | Node.js 版 | Python 版 |
|------|-----------|----------|
| 執行環境 | Node.js 18+ | Python 3.10+ |
| 套件管理 | npm | pip |
| 資料庫 | MongoDB Atlas（共用） | MongoDB Atlas（共用） |
| 監聽 Port | 3001 | 3002 |

---

## 2. 快速啟動

### Node.js 版

```bash
cd node-express
npm install
cp .env.example .env   # 填入必要變數（見第 3 節）
node server.js
# 伺服器啟動後：http://localhost:3001
```

開發模式（檔案變更自動重啟）：

```bash
npm run dev
```

### Python 版

```bash
cd python-flask
pip install -r requirements.txt
cp .env.example .env   # 填入必要變數（見第 3 節）
python app.py
# 伺服器啟動後：http://localhost:3002
```

啟動成功訊息範例：

```
✅ 已連接到 accounting_db.users
Auth server running at http://localhost:3001   # Node.js
 * Running on http://0.0.0.0:3002             # Python
```

---

## 3. 環境變數說明

各版實作皆使用各自目錄下的 `.env` 檔。以下為現有實作的完整變數對照：

### 必填

| 變數 | Node.js | Python | 說明 |
|------|:-------:|:------:|------|
| `MONGODB_URI` | 必填 | 必填 | MongoDB Atlas 連線字串，格式：`mongodb+srv://<user>:<password>@<cluster>.mongodb.net/` |
| `JWT_SECRET` | 建議填 | 建議填 | JWT 簽章金鑰，建議使用 64 字元 hex 字串。**各實作若要帳號互通，此值必須全部相同。** 若不填，所有 API 均無需驗證（僅供測試）。 |

### 選填 — 伺服器設定

| 變數 | Node.js 預設 | Python 預設 | 說明 |
|------|------------|------------|------|
| `PORT` | `3001` | `3002` | 監聽 Port |
| `CORS_ORIGIN` | `*` | `*` | 允許的 CORS 來源，正式環境應設為前端網址 |
| `DB_NAME` | `accounting_db` | — | 資料庫名稱（Python 版固定為 accounting_db） |

### 選填 — SMTP（密碼重設信）

若不設定 SMTP，`/api/auth/forgot-password` 呼叫時會回傳 500 錯誤。

| 變數 | 說明 | 範例 |
|------|------|------|
| `SMTP_USERNAME` | Gmail 地址 | `yourname@gmail.com` |
| `SMTP_PASSWORD` | Gmail App 密碼（16 字元，需先開啟兩步驟驗證） | `abcd efgh ijkl mnop` |
| `SMTP_FROM_NAME` | 寄件者顯示名稱 | `Auth 參考系統` |
| `SMTP_HOST` | SMTP 主機（Python 版可設，預設 smtp.gmail.com） | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP Port（Python 版可設，預設 587） | `587` |
| `SMTP_FROM_EMAIL` | 寄件者地址（Python 版，預設同 SMTP_USERNAME） | `noreply@yourapp.com` |

### 選填 — 密碼強度（僅 Python 版）

| 變數 | 預設 | 說明 |
|------|------|------|
| `PASSWORD_MIN_LENGTH` | `12` | 最少字元數 |
| `PASSWORD_REQUIRE_UPPERCASE` | `true` | 必須包含大寫字母 |
| `PASSWORD_REQUIRE_LOWERCASE` | `true` | 必須包含小寫字母 |
| `PASSWORD_REQUIRE_DIGIT` | `true` | 必須包含數字 |
| `PASSWORD_REQUIRE_SPECIAL` | `true` | 必須包含特殊符號 |
| `PASSWORD_CHECK_REPEATING` | `true` | 禁止重複字元超過 2 個 |
| `PASSWORD_MAX_REPEATING` | `2` | 最多允許連續相同字元數 |
| `PASSWORD_CHECK_SEQUENTIAL` | `true` | 禁止連續字元超過 3 個 |
| `PASSWORD_MAX_SEQUENTIAL` | `3` | 最多允許連續遞增/遞減字元數 |
| `PASSWORD_CHECK_KEYBOARD_PATTERN` | `true` | 禁止鍵盤模式（qwerty 等） |
| `PASSWORD_CHECK_COMMON_PASSWORDS` | `true` | 禁止常見弱密碼 |
| `PASSWORD_CHECK_MATH_PATTERNS` | `true` | 禁止數學模式（費波那契數列等） |
| `PASSWORD_CHECK_CHINESE_PINYIN` | `true` | 禁止常見中文拼音 |
| `PASSWORD_CHECK_PERSONAL_INFO` | `true` | 禁止包含個人資訊（email/name） |
| `PASSWORD_MIN_ENTROPY` | `50` | 最低熵值（bits） |
| `TESTING` | `false` | 設為 `true` 時停用速率限制，方便測試 |

---

## 4. 使用流程

### 4.1 一般登入流程

```
1. POST /api/auth/login          → 取得 JWT token
2. GET  /api/auth/verify         → 驗證 token 是否有效（帶 Bearer token）
3. POST /api/auth/logout         → 登出（client 端丟棄 token）
```

### 4.2 密碼重設流程

```
1. POST /api/auth/forgot-password   → 輸入 email，系統寄送重設連結
2. （收信，點擊連結取得 reset_token）
3. POST /api/auth/reset-password    → 帶 token + new_password，完成重設
4. POST /api/auth/login             → 用新密碼重新登入
```

### 4.3 新用戶註冊流程（Python 版）

```
1. POST /api/auth/validate-password → 先確認密碼符合強度要求（選用）
2. POST /api/auth/register          → 建立帳號
3. POST /api/auth/login             → 登入取得 token
```

---

## 5. API 端點參考

> **注意：各實作的錯誤回應 JSON key 可能不同，整合前請確認。**
> - Node.js 版：`{ "message": "..." }`
> - Python 版：`{ "error": "..." }`

---

### POST /api/auth/login

登入並取得 JWT token。

- **需要驗證**：否
- **速率限制**：Node.js 10 次/15 分鐘；Python 10 次/分鐘（IP）

**Request Body**

```json
{
  "email": "user@example.com",
  "password": "YourPassword123!"
}
```

| 欄位 | 型態 | 必填 | 說明 |
|------|------|:----:|------|
| `email` | string | 是 | 自動 trim + 轉小寫 |
| `password` | string | 是 | 區分大小寫 |

**成功回應（HTTP 200）**

Node.js 版：
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "王小明"
  }
}
```

Python 版（多了 `created_at`）：
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "王小明",
    "created_at": "2026-04-15T10:30:00"
  }
}
```

**失敗回應**

| HTTP 狀態碼 | 條件 | Node.js message | Python error |
|------------|------|-----------------|--------------|
| 400 | 缺少 email 或 password | `Email 和密碼不能為空` | `Email 和密碼不能為空` |
| 401 | 帳號/密碼錯誤 | `Email 或密碼錯誤` | `Email 或密碼錯誤` |
| 401 | 帳號停用 | `Email 或密碼錯誤` | — |
| 403 | 帳號停用（Python 版） | — | `帳號已被停用` |
| 429 | 帳號鎖定（Python 版，5 次失敗後） | — | `登入失敗次數過多，請 15 分鐘後再試` |
| 500 | JWT_SECRET 未設定（Node.js） | `JWT_SECRET 未設定` | — |
| 503 | 資料庫未連線 | `資料庫未連線` | `資料庫未連線` |

**cURL 範例**

```bash
# Node.js 版
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"YourPassword123!"}'

# Python 版
curl -X POST http://localhost:3002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"YourPassword123!"}'
```

---

### POST /api/auth/logout

登出（無狀態，由 client 端丟棄 token）。

- **需要驗證**：是（`Authorization: Bearer <token>`）
- **速率限制**：無

**Request Body**：無

**成功回應（HTTP 200）**

```json
{ "message": "已登出" }
```

**失敗回應**

| HTTP 狀態碼 | 條件 | 說明 |
|------------|------|------|
| 401 | token 遺失或無效 | 見 [驗證錯誤](#驗證錯誤通用) |

**cURL 範例**

```bash
curl -X POST http://localhost:3001/api/auth/logout \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### GET /api/auth/verify

驗證 JWT token 是否有效，並取得目前登入者資訊。

- **需要驗證**：是
- **速率限制**：Node.js 100 次/15 分鐘

**Request Body**：無

**成功回應（HTTP 200）**

Node.js 版（回傳完整 payload）：
```json
{
  "valid": true,
  "user": {
    "user_id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "王小明",
    "type": "access",
    "iat": 1744827200,
    "exp": 1745432000
  }
}
```

Python 版（查資料庫確認用戶仍存在）：
```json
{
  "valid": true,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "王小明"
  }
}
```

**失敗回應**

| HTTP 狀態碼 | 條件 | Node.js message | Python error |
|------------|------|-----------------|--------------|
| 401 | 缺少 token | `未登入` | `未授權` |
| 401 | token 無效或過期 | `登入已過期，請重新登入` | `Token 無效或已過期` |
| 404 | 用戶不存在（Python 版查 DB） | — | `用戶不存在` |
| 503 | 資料庫未連線（Python 版） | — | `資料庫未連線` |

**cURL 範例**

```bash
curl http://localhost:3001/api/auth/verify \
  -H "Authorization: Bearer eyJhbGci..."
```

---

### POST /api/auth/forgot-password

寄送密碼重設信。無論 email 是否存在，**一律回傳 200**（防止帳號枚舉攻擊）。

- **需要驗證**：否
- **速率限制**：Node.js 10 次/15 分鐘；Python 5 次/小時

**Request Body**

```json
{
  "email": "user@example.com"
}
```

**成功回應（HTTP 200）**

```json
{ "message": "若此 Email 已註冊，重設連結已寄出" }
```

**失敗回應**

| HTTP 狀態碼 | 條件 | Node.js message | Python error |
|------------|------|-----------------|--------------|
| 400 | 未提供 email | `請提供 Email` | `請提供 Email` |
| 500 | SMTP 未設定或寄信失敗 | `郵件服務未設定或發送失敗，請聯繫管理員` | `郵件服務未配置或發送失敗，請聯繫系統管理員` |
| 503 | 資料庫未連線（Python 版） | — | `資料庫未連線` |

**重設信連結格式**

```
http://<frontend_origin>?reset_token=<hex_token>
```

- token 有效期：**1 小時**
- Node.js token 格式：`crypto.randomBytes(32).toString('hex')`（64 字元 hex）
- Python token 格式：`secrets.token_urlsafe(32)`（~43 字元 base64url）

**cURL 範例**

```bash
curl -X POST http://localhost:3001/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

---

### POST /api/auth/reset-password

使用重設信中的 token 設定新密碼。

- **需要驗證**：否
- **速率限制**：Python 10 次/小時

**Request Body**

```json
{
  "token": "從信件連結取得的 token 字串",
  "new_password": "NewPassword456!@#"
}
```

| 欄位 | 型態 | 必填 | 說明 |
|------|------|:----:|------|
| `token` | string | 是 | 從重設信連結的 `?reset_token=` 取得 |
| `new_password` | string | 是 | 新密碼（Python 版會套用完整密碼強度驗證） |

**成功回應（HTTP 200）**

```json
{ "message": "密碼已重設，請重新登入" }
```

**失敗回應**

| HTTP 狀態碼 | 條件 | Node.js message | Python error |
|------------|------|-----------------|--------------|
| 400 | 缺少 token 或 new_password | `請提供 token 和新密碼` | `請提供 token 和新密碼` |
| 400 | token 無效（找不到） | `連結無效或已過期` | `連結無效或已過期` |
| 400 | token 已過期（超過 1 小時） | `連結已過期，請重新申請` | `連結已過期，請重新申請` |
| 400 | 密碼不符合強度要求（Python 版） | — | `密碼至少需要 12 個字元`（或其他驗證錯誤） |
| 503 | 資料庫未連線 | `資料庫未連線` | — |
| 500 | 系統錯誤 | `系統錯誤` | — |

**cURL 範例**

```bash
curl -X POST http://localhost:3001/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token":"abc123...","new_password":"NewPassword456!@#"}'
```

---

### POST /api/auth/register — Python 版

建立新用戶帳號（Node.js 版無此端點）。

- **需要驗證**：否
- **速率限制**：5 次/小時

**Request Body**

```json
{
  "email": "newuser@example.com",
  "password": "SecurePass123!@#",
  "name": "王小明"
}
```

| 欄位 | 型態 | 必填 | 驗證規則 |
|------|------|:----:|---------|
| `email` | string | 是 | 合法 email 格式；自動轉小寫；不可重複 |
| `password` | string | 是 | 套用完整密碼強度驗證（見第 7 節） |
| `name` | string | 是 | 不可為空；最多 50 字元 |

**成功回應（HTTP 201）**

```json
{
  "message": "註冊成功",
  "user_id": "507f1f77bcf86cd799439011"
}
```

**失敗回應**

| HTTP 狀態碼 | 條件 | error |
|------------|------|-------|
| 400 | Email 格式錯誤 | `Email 格式錯誤：...` |
| 400 | 名稱為空 | `名稱不能為空` |
| 400 | 名稱超過 50 字元 | `名稱不能超過 50 個字元` |
| 400 | 密碼強度不足 | `密碼至少需要 12 個字元`（或對應錯誤） |
| 409 | Email 已被註冊 | `此 Email 已被註冊` |
| 503 | 資料庫未連線 | `資料庫未連線` |

**cURL 範例**

```bash
curl -X POST http://localhost:3002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@example.com","password":"SecurePass123!@#","name":"王小明"}'
```

---

### POST /api/auth/validate-password — Python 版

即時驗證密碼強度，回傳逐項檢查結果（Node.js 版無此端點）。

- **需要驗證**：否
- **速率限制**：200 次/天，50 次/小時（預設）

**Request Body**

```json
{
  "password": "TestPassword123!",
  "email": "user@example.com",
  "name": "王小明"
}
```

| 欄位 | 型態 | 必填 | 說明 |
|------|------|:----:|------|
| `password` | string | 是 | 要驗證的密碼 |
| `email` | string | 否 | 用於「不可包含個人資訊」檢查 |
| `name` | string | 否 | 用於「不可包含個人資訊」檢查 |

**成功回應（HTTP 200）**

```json
{
  "valid": true,
  "errors": [],
  "checks": {
    "length":           { "passed": true,  "required": 12, "actual": 16, "message": "長度符合（16 字元）" },
    "uppercase":        { "passed": true,  "message": "包含大寫字母" },
    "lowercase":        { "passed": true,  "message": "包含小寫字母" },
    "digit":            { "passed": true,  "message": "包含數字" },
    "special":          { "passed": true,  "message": "包含特殊符號" },
    "repeating":        { "passed": true,  "message": "不包含重複字符" },
    "sequential":       { "passed": true,  "message": "不包含連續字符" },
    "keyboard_pattern": { "passed": true,  "message": "不包含鍵盤模式" },
    "math_pattern":     { "passed": true,  "message": "不包含數學模式" },
    "common_password":  { "passed": true,  "message": "不是常見密碼" },
    "chinese_pinyin":   { "passed": true,  "message": "不包含常見拼音" },
    "personal_info":    { "passed": true,  "message": "不包含個人資訊" },
    "entropy":          { "passed": true,  "value": 75.45, "required": 50, "message": "複雜度足夠（75.4 bits）" }
  }
}
```

驗證失敗時（`valid: false`），`errors` 陣列包含所有失敗項目的錯誤訊息，`checks` 中對應項目 `passed: false`。

**失敗回應**

| HTTP 狀態碼 | 條件 | error |
|------------|------|-------|
| 400 | 無效的請求資料 | `無效的請求資料` |

**cURL 範例**

```bash
# 基本驗證
curl -X POST http://localhost:3002/api/auth/validate-password \
  -H "Content-Type: application/json" \
  -d '{"password":"TestPassword123!"}'

# 含個人資訊檢查
curl -X POST http://localhost:3002/api/auth/validate-password \
  -H "Content-Type: application/json" \
  -d '{"password":"TestPassword123!","email":"user@example.com","name":"王小明"}'
```

---

### GET /api/status

檢查伺服器與資料庫連線狀態。

- **需要驗證**：否
- **速率限制**：無

**成功回應（HTTP 200）**

Node.js 版：
```json
{
  "server": "running",
  "database": "connected",
  "auth_required": true
}
```

Python 版（多了 `framework` 欄位）：
```json
{
  "server": "running",
  "database": "connected",
  "auth_required": true,
  "framework": "Python + Flask"
}
```

| 欄位 | 說明 |
|------|------|
| `database` | `"connected"` 或 `"disconnected"` |
| `auth_required` | `true` 表示 JWT_SECRET 已設定，API 需要 token |

**cURL 範例**

```bash
curl http://localhost:3001/api/status
curl http://localhost:3002/api/status
```

---

## 6. JWT Token 說明

### Token 格式

所有受保護的 API 請求須在 Header 帶上：

```
Authorization: Bearer <token>
```

### Token Payload

```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "email":   "user@example.com",
  "name":    "王小明",
  "type":    "access",
  "iat":     1744827200,
  "exp":     1745432000
}
```

| 欄位 | 說明 |
|------|------|
| `user_id` | MongoDB ObjectId 字串 |
| `email` | 用戶 email |
| `name` | 用戶顯示名稱 |
| `type` | 固定為 `"access"` |
| `iat` | 簽發時間（Unix timestamp） |
| `exp` | 到期時間（簽發 + 7 天） |

### 跨系統互通

只要 `JWT_SECRET` 相同，任一系統簽發的 token 均可在其他系統驗證。所有共用 `accounting_db.users` 的系統可以完全互通。

---

## 7. 密碼規則（Python 版）

Python 版在**新增密碼**（register、reset-password）時會套用以下全部規則：

### 基本要求

| 規則 | 預設設定 |
|------|---------|
| 最少長度 | 12 字元 |
| 必須包含大寫字母（A-Z） | 是 |
| 必須包含小寫字母（a-z） | 是 |
| 必須包含數字（0-9） | 是 |
| 必須包含特殊符號（`!@#$%` 等） | 是 |

### 模式檢查

| 規則 | 範例（不通過） | 範例（通過） |
|------|-------------|------------|
| 不可有 >2 個連續相同字元 | `aaa`, `111` | `aa`, `11` |
| 不可有 >3 個連續遞增/遞減字元 | `abcd`, `4321` | `abc`, `432` |
| 不可使用鍵盤模式 | `qwerty`, `1qaz`, `asdfgh` | — |
| 不可使用常見弱密碼 | `password`, `admin123`, `12345678` | — |
| 不可使用數學序列 | `112358`（費波那契）、`1491625`（完全平方） | — |
| 不可使用常見中文拼音 | `woaini`, `beijing`, `zhongguo` | — |
| 不可包含 email 帳號（@ 前段） | email 為 `john@example.com` 時，密碼含 `john` | — |
| 不可包含用戶名稱 | name 為 `王小明` 時，密碼含 `王小明` | — |

### 複雜度（熵值）

最低熵值 50 bits，計算方式：`長度 × log₂(字元集大小)`。字元集大小依密碼使用的字元種類計算。

使用 `/api/auth/validate-password` 端點可即時取得所有規則的逐項檢查結果（見第 5 節）。

---

## 8. 速率限制與帳號鎖定

### Node.js 版

| 端點 | 限制 | 維度 | 超限回應 |
|------|------|------|---------|
| POST /api/auth/login | 10 次 / 15 分鐘 | IP | HTTP 401 |
| POST /api/auth/forgot-password | 10 次 / 15 分鐘 | IP | HTTP 401 |
| GET /api/auth/verify | 100 次 / 15 分鐘 | IP | HTTP 429 |

超限訊息：
- 登入 / forgot-password → `登入嘗試次數過多，請於 15 分鐘後再試。`
- verify → `請求次數過多，請稍後再試。`

### Python 版

| 端點 | 限制 | 維度 |
|------|------|------|
| POST /api/auth/login | 10 次 / 分鐘 | IP |
| POST /api/auth/register | 5 次 / 小時 | IP |
| POST /api/auth/forgot-password | 5 次 / 小時 | IP |
| POST /api/auth/reset-password | 10 次 / 小時 | IP |
| 全域預設 | 200 次 / 天，50 次 / 小時 | IP |

### 帳號鎖定（Python 版專屬）

登入失敗 **5 次** 後，該 email 帳號鎖定 **15 分鐘**（以 email 為單位，非 IP）。

```json
HTTP 429
{ "error": "登入失敗次數過多，請 15 分鐘後再試" }
```

鎖定在成功登入後自動解除。

設定 `TESTING=true` 可停用所有速率限制（僅限開發環境）。

---

## 9. 錯誤代碼速查表

### Node.js 版（error key 為 `message`）

| HTTP 狀態碼 | message | 觸發條件 |
|------------|---------|---------|
| 400 | `Email 和密碼不能為空` | login：缺少欄位 |
| 400 | `請提供 Email` | forgot-password：缺少 email |
| 400 | `請提供 token 和新密碼` | reset-password：缺少欄位 |
| 400 | `連結無效或已過期` | reset-password：token 不存在 |
| 400 | `連結已過期，請重新申請` | reset-password：token 已超過 1 小時 |
| 401 | `Email 或密碼錯誤` | login：帳密錯誤或帳號停用 |
| 401 | `請先登入` | 受保護端點：無 Bearer token |
| 401 | `登入已過期，請重新登入` | 受保護端點：token 無效/過期 |
| 401 | `未登入` | verify：無 token |
| 429 | `請求次數過多，請稍後再試。` | verify 超過速率限制 |
| 500 | `JWT_SECRET 未設定` | login：未設定 JWT_SECRET |
| 500 | `登入失敗，請稍後再試` | login：未預期錯誤 |
| 500 | `郵件服務未設定或發送失敗，請聯繫管理員` | forgot-password：SMTP 問題 |
| 500 | `系統錯誤` | forgot/reset-password：未預期錯誤 |
| 503 | `資料庫未連線` | 任何需要 DB 的操作 |

### Python 版（error key 為 `error`）

| HTTP 狀態碼 | error | 觸發條件 |
|------------|-------|---------|
| 400 | `Email 和密碼不能為空` | login：缺少欄位 |
| 400 | `請提供 Email` | forgot-password：缺少 email |
| 400 | `請提供 token 和新密碼` | reset-password：缺少欄位 |
| 400 | `連結無效或已過期` | reset-password：token 不存在 |
| 400 | `連結已過期，請重新申請` | reset-password：token 已超時 |
| 400 | `Email 格式錯誤：...` | register：email 格式不合法 |
| 400 | `名稱不能為空` | register：name 為空 |
| 400 | `名稱不能超過 50 個字元` | register：name 超長 |
| 400 | `密碼至少需要 12 個字元`（等） | register/reset：密碼強度不足 |
| 400 | `無效的請求資料` | validate-password：請求格式錯誤 |
| 401 | `Email 或密碼錯誤` | login：帳密錯誤 |
| 401 | `未授權` | 受保護端點：無 token |
| 401 | `Token 無效或已過期` | 受保護端點：token 無效 |
| 403 | `帳號已被停用` | login：is_active = false |
| 404 | `用戶不存在` | verify：用戶已從 DB 刪除 |
| 409 | `此 Email 已被註冊` | register：email 重複 |
| 429 | `登入失敗次數過多，請 15 分鐘後再試` | login：帳號鎖定 |
| 500 | `郵件服務未配置或發送失敗，請聯繫系統管理員` | forgot-password：SMTP 問題 |
| 503 | `資料庫未連線` | 任何需要 DB 的操作 |

---

## 10. 各版實作差異（現有實作對照）

| 項目 | Node.js（Port 3001） | Python（Port 3002） |
|------|---------------------|---------------------|
| 錯誤回應 key | `message` | `error` |
| 帳號鎖定機制 | 無 | 5 次失敗 → 鎖定 15 分鐘 |
| 帳號停用 HTTP 碼 | 401 | 403 |
| register 端點 | 無 | 有 |
| validate-password 端點 | 無 | 有 |
| 密碼強度驗證範圍 | 無（僅 hash） | register + reset-password |
| login 回應含 created_at | 無 | 有 |
| verify 端點行為 | 僅驗 JWT（不查 DB） | 驗 JWT + 查 DB 確認用戶存在 |
| reset token 格式 | 64 字元 hex | ~43 字元 base64url |
| 速率限制維度 | IP | IP + email（鎖定） |
| SMTP 設定變數 | 3 個 | 5 個（多 HOST/PORT/FROM_EMAIL） |
