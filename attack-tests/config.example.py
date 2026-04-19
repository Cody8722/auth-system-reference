NODE_URL   = "http://localhost:3001"
PYTHON_URL = "http://localhost:3002"

# 需要是資料庫中實際存在的帳號（複製此檔為 config.py 後填入）
EXISTING_EMAIL    = "your@email.com"
EXISTING_PASSWORD = "your-password"

# 不存在的帳號（用於枚舉測試）
NONEXIST_EMAIL = "ghost_nobody@example.com"

# JWT Secret（需與 server .env 一致，僅供 02_jwt_attacks.py 偽造 token 用）
JWT_SECRET = "your-jwt-secret-here"
