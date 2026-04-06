# Auth System Reference — 登入系統知識庫

同一套登入功能，用兩種語言 / 框架實作，共用同一個 MongoDB。

```
auth-system-reference/
├── docs/
│   └── db-schema.md        # users collection schema + hash 格式說明
├── node-express/           # Node.js + Express 實作（Port 3001）
└── python-flask/           # Python + Flask 實作（Port 3002）
```

## 兩種實作對照

| 項目 | Node.js + Express | Python + Flask |
|------|-------------------|----------------|
| **語言** | JavaScript (Node.js 18+) | Python 3.10+ |
| **框架** | Express 4 | Flask 3 |
| **密碼雜湊** | `crypto.pbkdf2Sync`（手動實作 passlib 格式） | `passlib.pbkdf2_sha256` |
| **JWT** | `jsonwebtoken` | `PyJWT` |
| **Email** | `nodemailer` | `smtplib`（標準函式庫） |
| **速率限制** | `express-rate-limit` | `Flask-Limiter` |
| **資料庫** | `mongodb`（官方 Node.js 驅動） | `pymongo` |
| **共用 DB** | `accounting_db.users` | `accounting_db["users"]` |

## 功能端點

| 端點 | 說明 | 需要 Token |
|------|------|-----------|
| `POST /api/auth/login` | 登入，回傳 JWT | 否 |
| `POST /api/auth/logout` | 登出（client-side） | 是 |
| `POST /api/auth/forgot-password` | 寄送密碼重設信 | 否 |
| `POST /api/auth/reset-password` | 用 token 重設密碼 | 否 |
| `POST /api/auth/register` | 新用戶註冊（僅 Python 版） | 否 |
| `GET /api/auth/verify` | 驗證 JWT token | 是 |
| `POST /api/auth/validate-password` | 即時密碼強度驗證（僅 Python 版） | 否 |
| `GET /api/status` | 系統狀態 | 否 |

## 快速啟動

### Node.js 版

```bash
cd node-express
npm install
cp .env.example .env   # 填入 MONGODB_URI、JWT_SECRET
node server.js
# 瀏覽 http://localhost:3001
```

### Python 版

```bash
cd python-flask
pip install -r requirements.txt
cp .env.example .env   # 填入 MONGODB_URI、JWT_SECRET
python app.py
# 瀏覽 http://localhost:3002
```

## 帳號互通

兩種實作共用 `accounting_db.users`，同一組帳號可以登入兩邊。  
只要 `JWT_SECRET` 設定相同，任一系統發出的 JWT 也可在另一系統驗證。

詳細 schema 說明見 [`docs/db-schema.md`](docs/db-schema.md)。

## 關鍵實作差異

### 密碼 Hash

**Node.js**（手動實作 ab64 編解碼，相容 passlib 格式）：
```javascript
const ab64decode = s => {
    s = s.replace(/\./g, '+');   // ab64 → base64
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
};
// crypto.pbkdf2Sync(password, salt, 29000, 32, 'sha256')
```

**Python**（直接用 passlib，一行搞定）：
```python
from passlib.hash import pbkdf2_sha256
hash = pbkdf2_sha256.hash(password)        # 雜湊
ok   = pbkdf2_sha256.verify(password, hash) # 驗證
```

### 速率限制

**Node.js**：
```javascript
const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 10 });
app.post('/api/auth/login', authLimiter, handler);
```

**Python**：
```python
@bp.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login(): ...
```

### JWT 驗證

**Node.js**（middleware 形式）：
```javascript
function requireAuth(req, res, next) {
    const token = req.headers.authorization?.slice(7);
    req.user = jwt.verify(token, JWT_SECRET, { algorithms: ['HS256'] });
    next();
}
```

**Python**（decorator 形式）：
```python
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")[7:]
        payload = auth.verify_jwt(token)
        request.user_id = payload["user_id"]
        return f(*args, **kwargs)
    return decorated
```
