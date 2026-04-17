"""
Pytest 配置和共享 fixtures
"""

import os
import sys
from datetime import datetime

import mongomock
import pytest

# 測試環境變數（必須在 import app 之前設定）
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/test_auth_db"
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-testing"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@mongomock.patch(servers=(("localhost", 27017),))
def get_app():
    from app import app
    return app


app = get_app()


@pytest.fixture(scope="session")
def test_app():
    """創建測試應用實例"""
    app.config["TESTING"] = True
    app.url_map.strict_slashes = False
    return app


@pytest.fixture
def client(test_app):
    """創建測試客戶端"""
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def test_user_email():
    """生成唯一的測試用戶 Email"""
    return f"test{datetime.now().timestamp()}@example.com"


@pytest.fixture
def test_user_data(test_user_email):
    """測試用戶資料"""
    return {
        "email": test_user_email,
        "password": "MyS3cur3P@ssw0rd!XyZ",
        "name": "Test User",
    }


@pytest.fixture
def registered_user(client, test_user_data):
    """註冊並回傳用戶資料"""
    response = client.post("/api/auth/register", json=test_user_data)
    if response.status_code in [200, 201]:
        return test_user_data
    return None


@pytest.fixture
def auth_token(client, registered_user):
    """取得認證 token"""
    if not registered_user:
        return None
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    if login_response.status_code == 200:
        data = login_response.get_json()
        return data.get("token")
    return None


@pytest.fixture
def auth_headers(auth_token):
    """回傳含認證 token 的 headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
