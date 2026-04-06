# MongoDB Schema — accounting_db.users

兩個實作（Node.js 和 Python）共用同一個 collection。

## Collection 位置

```
MongoDB Atlas cluster
└── accounting_db
    └── users
```

## 欄位定義

| 欄位 | 類型 | 說明 |
|------|------|------|
| `_id` | ObjectId | MongoDB 自動產生 |
| `email` | String | 唯一，小寫儲存（`email.trim().lower()`） |
| `password_hash` | String | PBKDF2-SHA256 hash（見下方格式說明） |
| `name` | String | 顯示名稱，最長 50 字元 |
| `is_active` | Boolean | `false` 時禁止登入 |
| `email_verified` | Boolean | 預留欄位，目前未啟用 |
| `created_at` | DateTime | 帳號建立時間 |
| `last_login` | DateTime | 最後成功登入時間 |
| `password_last_updated` | DateTime | 密碼最後更新時間 |
| `password_reset_token` | String | 忘記密碼 token（臨時欄位） |
| `password_reset_expires` | DateTime | Token 過期時間（臨時欄位） |

## 索引

```javascript
users.createIndex({ email: 1 }, { unique: true })
users.createIndex({ password_reset_token: 1 }, { background: true })
```

## 密碼 Hash 格式

### 格式：passlib PBKDF2-SHA256（ab64 編碼）

```
$pbkdf2-sha256$<rounds>$<ab64_salt>$<ab64_hash>
```

- **rounds**：29000（NIST 推薦）
- **salt**：16 bytes，隨機生成
- **hash**：32 bytes（HMAC-SHA256 衍生金鑰）
- **ab64**：標準 base64，但 `+` 換成 `.`，無 `=` padding

### 範例

```
$pbkdf2-sha256$29000$aQ1BaE0pBaBUyrlXqtUaQw$7.iInVASvlIZIuo/XmNN8RFrM/3HT8KKnCIDekEZRM8
```

### Node.js 實作

```javascript
// 驗證
const ab64decode = s => {
    s = s.replace(/\./g, '+');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
};
function verifyPasslibPbkdf2(password, storedHash) {
    const parts = storedHash.split('$');
    const rounds = parseInt(parts[2]);
    const salt = ab64decode(parts[3]);
    const expected = ab64decode(parts[4]);
    const derived = crypto.pbkdf2Sync(password, salt, rounds, expected.length, 'sha256');
    return crypto.timingSafeEqual(derived, expected);
}
```

### Python 實作

```python
from passlib.hash import pbkdf2_sha256

# 雜湊
hash = pbkdf2_sha256.hash(password)

# 驗證
is_valid = pbkdf2_sha256.verify(password, stored_hash)
```

### 跨語言相容性

Node.js 的 `crypto.pbkdf2Sync` 和 Python 的 `passlib.pbkdf2_sha256` 產生相同格式的 hash。  
兩者都可以驗證對方產生的 hash，帳號在兩個系統間完全互通。

## JWT Token 格式

```json
{
  "user_id": "<MongoDB ObjectId string>",
  "email": "user@example.com",
  "name": "使用者名稱",
  "type": "access",
  "iat": 1234567890,
  "exp": 1234567890
}
```

- **Algorithm**：HS256
- **Expiry**：7 天
- **Secret**：`JWT_SECRET` 環境變數（兩個系統必須使用同一個值）

## 跨系統帳號互通

| 系統 | 登入端點 | 帳號來源 |
|------|----------|----------|
| 會計系統（Python/Flask） | `POST /api/auth/login` | `accounting_db.users` |
| 排班系統（Node.js/Express） | `POST /api/auth/login` | `accounting_db.users` |
| Auth 參考—Node.js | `POST /api/auth/login` | `accounting_db.users` |
| Auth 參考—Python | `POST /api/auth/login` | `accounting_db.users` |

同一組 `email` / `password` 在所有系統皆可登入。  
只要 `JWT_SECRET` 相同，任一系統發出的 JWT 也可在其他系統驗證。
