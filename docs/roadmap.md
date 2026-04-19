# 拓展規劃 — 新增語言實作指南

本文件定義此 repo 的擴充規範，任何人新增語言實作時皆以此為依據。

---

## 目錄

1. [最小合約](#1-最小合約)
2. [目錄結構規範](#2-目錄結構規範)
3. [Port 分配表](#3-port-分配表)
4. [候選實作清單](#4-候選實作清單)
5. [各語言密碼 Hash 實作參考](#5-各語言密碼-hash-實作參考)
6. [新增實作 Checklist](#6-新增實作-checklist)

---

## 1. 最小合約

每個語言實作都**必須**實現以下規格，以確保帳號、密碼、Token 在所有系統間互通。

### 必要端點（6 個）

| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/auth/login` | 驗證帳密、回傳 JWT |
| `POST` | `/api/auth/logout` | 登出（無狀態，client 端清除 token） |
| `GET`  | `/api/auth/verify` | 驗證 JWT 有效性 |
| `POST` | `/api/auth/forgot-password` | 寄送密碼重設信 |
| `POST` | `/api/auth/reset-password` | 使用 token 重設密碼 |
| `GET`  | `/api/status` | 伺服器 / 資料庫狀態 |

### 可選端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/auth/register` | 新用戶註冊 |
| `POST` | `/api/auth/validate-password` | 即時密碼強度驗證 |

### 相容性要求

**密碼 Hash：**
- 標準格式：passlib PBKDF2-SHA256（`$pbkdf2-sha256$29000$<ab64_salt>$<ab64_hash>`）
- 若語言生態無法直接支援此格式，須在實作目錄的 README 中說明差異與限制

**JWT：**
- 演算法：HS256
- Payload 必須包含：`user_id`、`email`、`name`、`type`（固定為 `"access"`）、`iat`、`exp`
- 有效期：7 天
- 各實作的 `JWT_SECRET` 必須相同才能互通

**資料庫：**
- MongoDB `accounting_db.users`
- 欄位規格見 [`docs/db-schema.md`](db-schema.md)

---

## 2. 目錄結構規範

### 命名規則

```
<lang>-<framework>/
```

- 全小寫，語言與框架之間用連字符（`-`）
- 範例：`go-gin`、`java-spring`、`ts-nestjs`

### 必要檔案

```
<lang>-<framework>/
├── .env.example       # 必填：列出所有環境變數與說明
└── <source files>     # 依語言慣例組織，無強制規定
```

### `.env.example` 最低要求

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
PORT=<分配的 port>
JWT_SECRET=<64-char hex>
SMTP_USERNAME=
SMTP_PASSWORD=
```

---

## 3. Port 分配表

新增實作時，從此表挑選「候選」狀態的 port，完成後將狀態改為「已完成」。

| Port | 目錄名稱 | 語言 / 框架 | 狀態 |
|------|---------|-----------|------|
| 3001 | `node-express` | Node.js + Express | 已完成 |
| 3002 | `python-flask` | Python + Flask | 已完成 |
| 3003 | `go-gin` | Go + Gin | 候選 |
| 3004 | `java-spring` | Java + Spring Boot | 候選 |
| 3005 | `ts-nestjs` | TypeScript + NestJS | 候選 |
| 3006 | `ruby-sinatra` | Ruby + Sinatra | 候選 |
| 3007 | `rust-axum` | Rust + Axum | 候選 |
| 3008 | `php-slim` | PHP + Slim | 候選 |
| 3009 | `dotnet-aspnet` | C# + ASP.NET Core | 候選 |
| 3010 | `kotlin-ktor` | Kotlin + Ktor | 候選 |

---

## 4. 候選實作清單

### 優先度 High — 學習價值最高

#### `go-gin`（Port 3003）
**學習重點：**
- 靜態型別如何影響 auth 程式碼結構（無法隱式轉型，error 必須顯式處理）
- 原生 `crypto/sha256`、`encoding/base64` 實作 PBKDF2，手動對齊 passlib 格式
- middleware 以函式鏈（`gin.HandlerFunc`）串接，對比 Express 的 `next()`
- goroutine 在並發登入驗證上的優勢

**推薦套件：**`gin-gonic/gin`、`golang-jwt/jwt`、`go.mongodb.org/mongo-driver`

---

#### `ts-nestjs`（Port 3005）
**學習重點：**
- 同一 Node.js 生態，但 decorator（`@Controller`、`@UseGuards`）完全改變架構感
- 依賴注入（DI）如何讓 auth service 與 route 解耦，對比 Express 直接在 route 裡寫邏輯
- `PassportStrategy` + `JwtAuthGuard` vs. 手動 middleware
- TypeScript 嚴格型別在 DTO 驗證上的效果（`class-validator`）

**推薦套件：**`@nestjs/jwt`、`@nestjs/passport`、`class-validator`、`mongoose`

---

#### `java-spring`（Port 3004）
**學習重點：**
- Spring Security filter chain（`OncePerRequestFilter`）vs. 手動 middleware
- `@PreAuthorize` annotation 式權限控制
- Bean 生命週期與 DI 容器概念
- `BCryptPasswordEncoder` vs. PBKDF2（需手動實作 passlib 格式相容）

**推薦套件：**`spring-boot-starter-security`、`jjwt`、`spring-data-mongodb`

---

### 優先度 Medium

#### `rust-axum`（Port 3007）
**學習重點：**
- 型別安全如何在**編譯期**就能抓出 auth 邏輯漏洞（例如忘記驗證 token）
- `tower` middleware 的 `Service` trait 抽象
- `async/await` + `tokio` 的非同步模型
- `ring` crate 實作 PBKDF2

**推薦套件：**`axum`、`jsonwebtoken`、`mongodb`、`ring`

---

#### `ruby-sinatra`（Port 3006）
**學習重點：**
- 和 Flask 結構最像（輕量、DSL 式路由），適合直接對照兩者差異
- Ruby 的 block / proc 在 middleware 上的慣用寫法
- `bcrypt` gem 的介面 vs. passlib（需手動實作 PBKDF2 格式相容）

**推薦套件：**`sinatra`、`jwt`、`mongo`、`dotenv`

---

### 優先度 Low — 特色對比

#### `php-slim`（Port 3008）
**重點：** 現代 PHP（PSR-7 Request/Response、PSR-15 Middleware），打破對 PHP 的舊印象。

#### `dotnet-aspnet`（Port 3009）
**重點：** `Microsoft.AspNetCore.Authentication.JwtBearer` 的設定式 middleware vs. 手動驗證；`AddAuthentication().AddJwtBearer()` 模式。

#### `kotlin-ktor`（Port 3010）
**重點：** JVM 生態但語法比 Java 精簡；coroutine 模型；Exposed ORM。

---

## 5. 各語言密碼 Hash 實作參考

所有實作都需要相容 passlib PBKDF2-SHA256 格式：`$pbkdf2-sha256$29000$<ab64_salt>$<ab64_hash>`

> ab64 = 標準 base64，但 `+` 換成 `.`，無 `=` padding

### 已實作

**Node.js**（手動實作 ab64 編解碼）：

```javascript
const ab64decode = s => {
    s = s.replace(/\./g, '+');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
};
const ab64encode = buf =>
    Buffer.from(buf).toString('base64').replace(/\+/g, '.').replace(/=/g, '');

// 驗證
const parts = storedHash.split('$');
const derived = crypto.pbkdf2Sync(password, salt, rounds, expected.length, 'sha256');
return crypto.timingSafeEqual(derived, expected);
```

**Python**（直接使用 passlib）：

```python
from passlib.hash import pbkdf2_sha256
hash   = pbkdf2_sha256.hash(password)             # 雜湊
valid  = pbkdf2_sha256.verify(password, stored)   # 驗證
```

### 待補充

| 語言 | 推薦方式 |
|------|---------|
| Go | `golang.org/x/crypto/pbkdf2` + 手動 ab64 編解碼（參考 Node.js 版邏輯） |
| Java | `SecretKeyFactory("PBKDF2WithHmacSHA256")` + 手動 ab64 |
| Rust | `ring::pbkdf2` + 手動 ab64 |
| Ruby | `OpenSSL::PKCS5.pbkdf2_hmac` + 手動 ab64 |
| C# | `Rfc2898DeriveBytes`（SHA256）+ 手動 ab64 |
| Kotlin | 同 Java，或使用 `Bouncy Castle` |
| PHP | `hash_pbkdf2('sha256', ...)` + 手動 ab64 |

---

## 6. 已知安全限制（實作前請閱讀）

以下是本 repo 所有實作共有的**設計層面限制**，不屬於 bug，但開發者應知曉，並根據正式環境需求自行補強。

### 密碼噴灑（Password Spraying）

**問題：** Rate limit 與帳號鎖定均以單一 IP 或單一 email 為單位，無跨帳號的全域失敗計數。
攻擊者對 N 個帳號各嘗試 1 次相同密碼，可永遠不觸發任何封鎖。

**為何不在此修：** 最直覺的修法「全域 IP 失敗計數」在 NAT 環境（辦公室、學校、ISP CGNAT）
會誤傷共用 IP 的合法用戶，副作用大於收益。

**開發者可選的補強方案：**

| 方案 | 效果 | 適用場景 |
|------|------|---------|
| CAPTCHA（N 次失敗後） | 高，阻擋自動化攻擊 | 面向一般大眾的服務 |
| 多因子驗證（MFA/TOTP） | 極高，密碼洩漏也無效 | 高安全性需求 |
| 漸進延遲（Exponential Backoff） | 中，拖慢攻擊速度 | 輕量補強 |
| 異常偵測（Anomaly Detection） | 高，可識別噴灑模式 | 有 ML 基礎設施的環境 |

### Rate Limit 使用 In-Memory 儲存

**問題：** 兩個實作的 rate limit 與帳號鎖定均存在記憶體，server 重啟後全部清零。
多進程 / 多實例部署時，各進程計數獨立，有效限制減半。

**開發者補強方案：** 使用 Redis 作為共享儲存（`express-rate-limit` 有 `rate-limit-redis` 套件；
Flask-Limiter 支援 `storage_uri="redis://..."`）。

---

## 7. 新增實作 Checklist

新增一個語言實作時，依序確認以下項目：

### 實作本身

- [ ] 目錄命名遵循 `<lang>-<framework>` 規則
- [ ] Port 使用分配表中對應的號碼
- [ ] 實作全部 6 個必要端點（login / logout / verify / forgot-password / reset-password / status）
- [ ] 密碼格式相容 passlib PBKDF2-SHA256（或說明差異）
- [ ] JWT payload 包含 `user_id / email / name / type / iat / exp`，HS256 演算法，7 天有效期
- [ ] `.env.example` 包含 `MONGODB_URI`、`PORT`、`JWT_SECRET`、SMTP 相關變數

### 文件更新

- [ ] `README.md`：目錄樹加入新目錄；現有實作對照表加一列；快速啟動加一節
- [ ] `docs/roadmap.md`：Port 分配表狀態改為「已完成」
- [ ] `docs/usage.md`（建議）：第 10 節差異對照表加一欄
