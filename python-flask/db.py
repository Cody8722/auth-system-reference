"""
db.py — MongoDB 連線模組（精簡版）

只連接 accounting_db.users（與會計系統、排班系統共用）。
"""

import logging
import os

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

load_dotenv()

logger = logging.getLogger(__name__)

# Module-level globals
client = None
users_collection = None


def init_db():
    """建立 MongoDB 連線並初始化 users_collection。"""
    global client, users_collection

    MONGO_URI = os.getenv("MONGODB_URI")

    if not MONGO_URI:
        logger.warning("⚠️ 未設定 MONGODB_URI，資料庫功能無法使用")
        return

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxPoolSize=10,
            minPoolSize=0,
            retryWrites=True,
            retryReads=True,
        )
        client.admin.command("ping")

        # 共用 accounting_db.users（與會計系統、排班系統帳號互通）
        users_collection = client["accounting_db"]["users"]

        # 建立必要索引
        users_collection.create_index([("email", ASCENDING)], unique=True, background=True)
        users_collection.create_index([("password_reset_token", ASCENDING)], background=True)

        logger.info("✅ 已連接到 accounting_db.users")
    except Exception as e:
        logger.error(f"❌ MongoDB 連線失敗: {e}")
        client = None
        users_collection = None
