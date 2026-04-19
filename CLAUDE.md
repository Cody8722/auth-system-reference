# CLAUDE.md

This file provides guidance to Claude when working with code in this repository.

## 專案概述

**Auth System Reference（登入系統知識庫）** — 同一套登入功能，以多種語言 / 框架實作，共用同一個 MongoDB。  
目前有 Node.js + Express（Port 3001）和 Python + Flask（Port 3002）兩版，未來持續新增其他語言實作。

---

## 操作規則

- 禁止單獨使用 `cd`，優先使用相對路徑。
- 禁止使用 `cd ... && <指令>`，直接用 `<指令> path/to/target`。
- 避免複雜 Bash 組合：如需複雜操作，請分開多次執行。
- 每個 bash 呼叫是獨立 session，不依賴上一條指令的環境變數。
- 禁止使用 `sleep` 等待非同步任務；等待 GitHub Action 應改用 `gh run watch`。
- 使用者明確要求刪除或移動檔案時，直接執行即可，無需再反問確認一次。
- 修改檔案前必須先完整讀過，不靠假設。
- 不刪除未觸及的程式碼、注解、TODO。
- 不主動重構超出需求範圍的程式碼。
- 遇到不確定的需求先問，不自行假設後執行。
- 失敗時回報具體錯誤訊息與指令，不要空泛說「發生錯誤」。
- 不可覆寫或修改現有的 `.env` 檔案；但可以新增 `.env.example` 或 `.env.template`。
- 不可為了讓測試通過而修改測試邏輯，應修正程式碼本身。

## 向下兼容原則

這是多語言共用同一資料庫的參考實作，兼容性極為重要：

- **密碼 Hash**：必須維持 passlib PBKDF2-SHA256 格式（`$pbkdf2-sha256$29000$<ab64_salt>$<ab64_hash>`），任何語言的實作都必須能驗證彼此產生的 hash
- **JWT**：Payload 欄位（`user_id`、`email`、`name`、`type`）不可更改；演算法固定 HS256；有效期固定 7 天
- **資料庫 Schema**：`accounting_db.users` 現有欄位不可刪除或重命名；新增欄位必須有預設值或允許 null
- **API 端點**：現有端點的路徑、參數、回應格式不可破壞；新增參數必須有預設值
- **Port 分配**：各語言實作的 Port 不可更改（Node.js=3001, Python=3002，其他見 `docs/roadmap.md`）

如需破壞性變更，必須先與使用者確認，並同步更新所有受影響的語言實作。

## Commit 規範

格式：`<類型>(<實作>): <簡短描述>`

| 類型 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修復 |
| `refactor` | 重構（非新功能、非 bug）|
| `docs` | 文件變更 |
| `test` | 測試相關 |
| `perf` | 效能優化 |
| `chore` | 建置工具或雜項變更 |

範例：`feat(python-flask): 新增 validate-password 端點`、`fix(node-express): 修正 ab64 解碼邊界條件`

每約 5 個相關變更，或一個功能階段完成後才 commit。**commit 完成後必須立即推送到遠端。**

## Git 分支策略

```
feature/* → develop → release
```

- `feature/<n>`：所有新功能與 bug 修復在此開發
- `develop`：整合分支；直接 push 到 `develop` 僅限小修（文件、設定）
- `release`：穩定版，禁止直接 push，必須從 `develop` 開 PR

---

## 架構總覽

```
node-express/（Node.js + Express，Port 3001）
    ↕ HTTP REST (JWT Bearer Token, HS256)
    ↕
python-flask/（Python + Flask，Port 3002）
    ↕ HTTP REST (JWT Bearer Token, HS256)
    ↕
MongoDB Atlas（accounting_db.users）← 所有實作共用同一個 collection
```

前端（各實作各自的 `public/index.html` 或 `templates/index.html`）由同一個伺服器提供，透過 Fetch API 呼叫自身的 `/api/` 端點。

### Node.js 實作（`node-express/`）

單一檔案 `server.js`，含所有路由與邏輯：

- **認證**：`requireAuth` middleware，讀取 `Authorization: Bearer <token>`，`AUTH_PUBLIC_PATHS` 白名單排除不需要驗證的端點
- **密碼 Hash**：手動實作 ab64 編解碼，`verifyPasslibPbkdf2()` + `hashPasslibPbkdf2()`，與 Python passlib 完全相容
- **速率限制**：`express-rate-limit`，登入端點 10 次/15 分鐘（IP）
- **Email**：`nodemailer`，Gmail SMTP

API 路由：
- `POST /api/auth/login` — 登入
- `POST /api/auth/logout` — 登出（client-side，回傳 200 即可）
- `POST /api/auth/forgot-password` — 寄送密碼重設信
- `POST /api/auth/reset-password` — 用 token 重設密碼
- `GET  /api/auth/verify` — 驗證 JWT（不查 DB，只驗 token）
- `GET  /api/status` — 伺服器狀態

### Python 實作（`python-flask/`）

Blueprint 架構，`app.py` 為主程式，`routes/auth_routes.py` 為路由：

- **認證**：`require_auth` decorator（`auth.py`）
- **密碼 Hash**：直接使用 `passlib.pbkdf2_sha256`
- **速率限制**：`Flask-Limiter`，登入 10 次/分鐘（IP）+ 帳號鎖定（5 次失敗 → 15 分鐘）
- **Email**：`smtplib`（標準函式庫）
- **額外功能**：`POST /api/auth/register`、`POST /api/auth/validate-password`（含詳細密碼強度逐項檢查）

驗證行為與 Node.js 版的差異：`/api/auth/verify` 除了驗 JWT，還會查 DB 確認用戶仍存在。

### 資料庫（MongoDB `accounting_db.users`）

| 欄位 | 類型 | 說明 |
|------|------|------|
| `_id` | ObjectId | 主鍵 |
| `email` | String | 唯一索引，小寫儲存 |
| `password_hash` | String | PBKDF2-SHA256，passlib 格式 |
| `name` | String | 最長 50 字元 |
| `is_active` | Boolean | false 時禁止登入 |
| `created_at` | DateTime | |
| `last_login` | DateTime | |
| `password_last_updated` | DateTime | |
| `password_reset_token` | String | 臨時欄位，重設後刪除 |
| `password_reset_expires` | DateTime | 臨時欄位，1 小時後過期 |

索引：`{ email: 1 }` (unique)、`{ password_reset_token: 1 }`

---

## 常用指令

### Node.js 版

```bash
# 啟動（開發模式，自動重啟）
node-express/node_modules/.bin/nodemon node-express/server.js

# 啟動（一般）
node node-express/server.js            # http://localhost:3001

# 安裝依賴
npm install --prefix node-express
```

### Python 版

```bash
# 啟動
python python-flask/app.py             # http://localhost:3002

# 安裝依賴
pip install -r python-flask/requirements.txt

# 語法檢查（無 linter 設定，手動確認）
python -m py_compile python-flask/app.py python-flask/auth.py python-flask/db.py
```

## push 前必須執行

目前兩個實作均無自動化測試，push 前請手動確認：

```bash
# Node.js：確認可正常啟動
node -e "require('./node-express/server.js')" 2>&1 | head -5

# Python：確認語法無誤
python -m py_compile python-flask/app.py python-flask/auth.py python-flask/db.py python-flask/routes/auth_routes.py

# 手動測試（啟動後 curl 確認）
curl http://localhost:3001/api/status
curl http://localhost:3002/api/status
```

---

## 程式碼風格

### Node.js（`node-express/server.js`）

- **縮排**：4 空格
- **引號**：單引號
- **Section 分隔線**：`// ── 標題 ────────────────────────────────────────`
- **格式化工具**：無（PEP 8 by convention，不強制）
- 禁止 `from module import *`；async/await 優先，不用 callback

### Python（`python-flask/`）

- **縮排**：4 空格
- **引號**：字串優先雙引號
- **命名**：函數/變數 `snake_case`、類別 `PascalCase`、常數 `UPPER_CASE`
- **格式化工具**：無（PEP 8 by convention，不強制）
- 禁止裸 `except:`，必須指定例外類型

---

## 環境變數

兩個實作各有獨立的 `.env`，分別在各自目錄下。

### 必填

| 變數 | 說明 |
|------|------|
| `MONGODB_URI` | MongoDB Atlas 連線字串（`mongodb+srv://...`） |
| `JWT_SECRET` | JWT 簽章金鑰。**所有實作必須使用同一個值，token 才能跨系統互通** |

### 選填

| 變數 | Node.js 預設 | Python 預設 | 說明 |
|------|------------|------------|------|
| `PORT` | `3001` | `3002` | 監聽 Port |
| `CORS_ORIGIN` | `*` | `*` | 允許的 CORS 來源 |
| `SMTP_USERNAME` | — | — | Gmail 地址（忘記密碼功能必填） |
| `SMTP_PASSWORD` | — | — | Gmail App 密碼（16 字元） |
| `SMTP_FROM_NAME` | `Auth 參考系統` | `Auth 參考系統` | 寄件者名稱 |
| `TESTING` | — | `false` | 設為 `true` 停用速率限制 |

Python 版另支援 `PASSWORD_MIN_LENGTH`、`PASSWORD_REQUIRE_UPPERCASE` 等密碼強度設定變數（詳見 `docs/usage.md` 第 3 節）。

---

## 已知地雷 / 歷史包袱

### 🔴 高危（踩到立刻出錯）

- **ab64 ≠ 標準 base64**：passlib 使用的 ab64 格式把 `+` 換成 `.`，且無 `=` padding。Node.js 版的 `ab64decode()` 必須先 `.replace(/\./g, '+')` 再補 padding 才能 base64 decode。直接用 `Buffer.from(s, 'base64')` 會靜默解碼錯誤，密碼驗證永遠失敗。

- **Node.js 版 `/api/auth/verify` 不查 DB**：只驗 JWT 簽章與有效期，不確認用戶是否仍存在於資料庫。若用戶被刪除，token 在 7 天內仍會通過驗證。Python 版會查 DB，行為不同，整合時要注意。

- **忘記密碼 token 格式不同**：Node.js 產生 64 字元 hex（`crypto.randomBytes(32).toString('hex')`），Python 產生約 43 字元 base64url（`secrets.token_urlsafe(32)`）。兩者都存在 `password_reset_token` 欄位，但格式不互通——Node.js 發出的 token 無法用 Python 端點重設，反之亦然。

- **兩版錯誤回應的 key 不同**：Node.js 用 `{ "message": "..." }`，Python 用 `{ "error": "..." }`。前端整合兩個版本時必須分別處理。

### 🟡 中危（埋雷，不一定立刻爆）

- **帳號停用的 HTTP 狀態碼不同**：Node.js 回 401（跟帳密錯誤一樣），Python 回 403（`帳號已被停用`）。前端若只判斷 401 就認為帳密錯，無法區分「帳號被停用」的情況。

- **帳號鎖定機制僅 Python 版有**：登入失敗 5 次後，Python 版會以 email 為單位鎖定 15 分鐘，回 429。Node.js 版只有 IP 速率限制，不會鎖帳號。同一 MongoDB 帳號，兩版的安全行為不一致。

- **`JWT_SECRET` 未設定時 Node.js 版不驗證任何請求**：`requireAuth` middleware 有 `if (!process.env.JWT_SECRET) return next()` 的 fallback，沒有設定 JWT_SECRET 時所有 API 都不需要 token。僅供本地測試，正式環境必須設定。

- **Python 版密碼強度驗證只在 register 和 reset-password 時觸發**：用 `validate-password` 端點測試通過，不代表 register 一定成功（例如 `TESTING=true` 時速率限制關閉，但密碼驗證規則仍然生效）。

### 🟢 低危（容易誤解但不會立刻 crash）

- **`email_verified` 欄位預留但未啟用**：schema 中有此欄位，但兩個實作目前都不檢查它，也不提供驗證 email 的流程。

- **新增語言實作時，Port 要看 `docs/roadmap.md` 的分配表**：Port 3001-3010 都已預先分配給特定語言，不可隨意使用。

---

## 相關文件

| 文件 | 說明 |
|------|------|
| [`docs/db-schema.md`](docs/db-schema.md) | MongoDB schema 完整定義、密碼 hash 格式、JWT payload 格式、跨系統互通說明 |
| [`docs/usage.md`](docs/usage.md) | 完整 API 端點文件（請求/回應範例、錯誤代碼速查表、各版差異對照） |
| [`docs/roadmap.md`](docs/roadmap.md) | 新增語言實作指南、Port 分配表、最小合約、各語言 hash 實作參考 |
| [`node-express/.env.example`](node-express/.env.example) | Node.js 版環境變數範本 |
| [`python-flask/.env.example`](python-flask/.env.example) | Python 版環境變數範本 |
