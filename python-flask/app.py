"""
Auth System Reference — Python + Flask 實作

端點：
  POST /api/auth/login
  POST /api/auth/logout
  POST /api/auth/forgot-password
  POST /api/auth/reset-password
  POST /api/auth/register
  POST /api/auth/validate-password
  GET  /api/auth/verify
  GET  /api/status
  GET  /  （前端）

共用 accounting_db.users（與會計系統、排班系統帳號互通）
密碼格式：PBKDF2-SHA256（passlib）
"""

import logging
import os

from flask import Flask, jsonify, render_template
from flask_cors import CORS

import db
from extensions import limiter
from routes.auth_routes import bp as auth_bp

# ── 日誌 ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask App ──────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "dev-secret")

CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGIN", "*")}})

# Rate limiter
limiter.init_app(app)

# 初始化 MongoDB
db.init_db()

# 註冊 Blueprint
app.register_blueprint(auth_bp)


# ── 系統狀態 ──────────────────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def status():
    """系統狀態（公開端點）"""
    return jsonify({
        "server": "running",
        "database": "connected" if db.client is not None else "disconnected",
        "auth_required": bool(os.getenv("JWT_SECRET")),
        "framework": "Python + Flask",
    }), 200


# ── 前端 ──────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    """前端頁面"""
    return render_template("index.html")


# ── 啟動 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3002))
    logger.info(f"Auth server (Python) running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
