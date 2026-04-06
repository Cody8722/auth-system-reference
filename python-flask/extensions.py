"""
extensions.py — 共用工具（精簡版）

包含：limiter、require_auth 裝飾器、登入鎖定機制。

來源：accounting-system/backend/extensions.py（只保留 auth 所需部分）
"""

import os
import time
import logging
from collections import defaultdict
from functools import wraps

import jwt as pyjwt
from flask import jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import auth  # auth.py

logger = logging.getLogger(__name__)

# ── Rate Limiter ───────────────────────────────────────────────
def get_rate_limit_key():
    """優先用 JWT user_id 作為 rate limit key。"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            jwt_secret = os.getenv("JWT_SECRET")
            if jwt_secret:
                payload = pyjwt.decode(auth_header[7:], jwt_secret, algorithms=["HS256"])
                return f"user:{payload.get('user_id', 'unknown')}"
        except Exception:
            pass
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address()


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    enabled=os.getenv("TESTING", "false").lower() != "true",
)

# ── require_auth 裝飾器 ────────────────────────────────────────
def require_auth(f):
    """驗證 JWT token，成功後在 request 注入 user_id、email、name。"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            parts = auth_header.split(" ")
            if len(parts) == 2:
                payload = auth.verify_jwt(parts[1])
                if payload:
                    request.user_id = payload.get("user_id")
                    request.email = payload.get("email")
                    request.name = payload.get("name", "")
                    return f(*args, **kwargs)
                return jsonify({"error": "Token 無效或已過期"}), 401
            return jsonify({"error": "Authorization header 格式錯誤"}), 401
        return jsonify({"error": "未授權"}), 401
    return decorated_function

# ── 登入失敗鎖定 ───────────────────────────────────────────────
_login_failures: dict = defaultdict(list)
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION = 15 * 60  # 15 分鐘


def _is_locked_out(email: str) -> bool:
    if os.getenv("TESTING", "false").lower() == "true":
        return False
    now = time.time()
    _login_failures[email] = [t for t in _login_failures[email] if now - t < LOCKOUT_DURATION]
    return len(_login_failures[email]) >= LOCKOUT_THRESHOLD


def _record_login_failure(email: str) -> None:
    _login_failures[email].append(time.time())


def _clear_login_failures(email: str) -> None:
    _login_failures.pop(email, None)
