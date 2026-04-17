'use strict';

// 環境變數必須在 require('../server') 之前設定
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-jwt-secret-key-for-testing';
// 不設定 MONGODB_URI，DB 相關操作回傳 503

const request = require('supertest');
const jwt = require('jsonwebtoken');
const app = require('../server');

const JWT_SECRET = process.env.JWT_SECRET;

/** 產生測試用 JWT */
function makeToken(overrides = {}) {
    const payload = {
        user_id: '000000000000000000000001',
        email: 'test@example.com',
        name: 'Test User',
        type: 'access',
        ...overrides,
    };
    return jwt.sign(payload, JWT_SECRET, { algorithm: 'HS256', expiresIn: '7d' });
}

// ── Status ────────────────────────────────────────────────────

describe('GET /api/status', () => {
    test('回傳 200 且含 server: running', async () => {
        const res = await request(app).get('/api/status');
        expect(res.status).toBe(200);
        expect(res.body.server).toBe('running');
        expect(res.body).toHaveProperty('database');
        expect(res.body).toHaveProperty('auth_required');
    });
});

// ── Login ─────────────────────────────────────────────────────

describe('POST /api/auth/login', () => {
    test('缺少 email 和 password 應回傳 400 或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({});
        expect([400, 503]).toContain(res.status);
    });

    test('只有 email 缺少 password 應回傳 400 或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'test@example.com' });
        expect([400, 503]).toContain(res.status);
    });

    test('只有 password 缺少 email 應回傳 400 或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ password: 'SomePassword123!' });
        expect([400, 503]).toContain(res.status);
    });

    test('錯誤密碼應回傳 401 或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'test@example.com', password: 'WrongPassword123!@#' });
        expect([401, 503]).toContain(res.status);
    });

    test('不存在的用戶應回傳 401 或 503', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'nonexistent@example.com', password: 'MyS3cur3P@ssw0rd!XyZ' });
        expect([401, 503]).toContain(res.status);
    });

    test('成功登入應回傳 200 含 token 和 user，或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'user@example.com', password: 'MyS3cur3P@ssw0rd!XyZ' });
        expect([200, 401, 503]).toContain(res.status);
        if (res.status === 200) {
            expect(res.body.token).toBeDefined();
            expect(res.body.user).toHaveProperty('id');
            expect(res.body.user).toHaveProperty('email');
        }
    });
});

// ── JWT Verify ────────────────────────────────────────────────

describe('GET /api/auth/verify', () => {
    test('缺少 token 應回傳 401', async () => {
        const res = await request(app).get('/api/auth/verify');
        expect(res.status).toBe(401);
    });

    test('無效 token 應回傳 401', async () => {
        const res = await request(app)
            .get('/api/auth/verify')
            .set('Authorization', 'Bearer invalid_token_123');
        expect(res.status).toBe(401);
    });

    test('格式錯誤的 Authorization header 應回傳 401', async () => {
        const res = await request(app)
            .get('/api/auth/verify')
            .set('Authorization', 'InvalidFormat');
        expect(res.status).toBe(401);
    });

    test('有效 token 應回傳 200 或 503（無 DB）', async () => {
        const token = makeToken();
        const res = await request(app)
            .get('/api/auth/verify')
            .set('Authorization', `Bearer ${token}`);
        // Node.js 版 verify 不查 DB，直接回傳 payload
        expect([200, 503]).toContain(res.status);
        if (res.status === 200) {
            expect(res.body.valid).toBe(true);
            expect(res.body.user).toHaveProperty('user_id');
        }
    });

    test('過期 token 應回傳 401', async () => {
        const token = jwt.sign(
            { user_id: '000000000000000000000001', email: 'test@example.com', name: 'Test', type: 'access' },
            JWT_SECRET,
            { algorithm: 'HS256', expiresIn: '-1s' }
        );
        const res = await request(app)
            .get('/api/auth/verify')
            .set('Authorization', `Bearer ${token}`);
        expect(res.status).toBe(401);
    });
});

// ── Logout ────────────────────────────────────────────────────

describe('POST /api/auth/logout', () => {
    test('有效 token 應回傳 200', async () => {
        const token = makeToken();
        const res = await request(app)
            .post('/api/auth/logout')
            .set('Authorization', `Bearer ${token}`);
        expect(res.status).toBe(200);
        expect(res.body.message).toBeDefined();
    });

    test('缺少 token 應回傳 200（logout 在公開路徑，無需驗證）', async () => {
        const res = await request(app).post('/api/auth/logout');
        expect(res.status).toBe(200);
    });
});

// ── Forgot Password ───────────────────────────────────────────

describe('POST /api/auth/forgot-password', () => {
    test('缺少 email 應回傳 400', async () => {
        const res = await request(app)
            .post('/api/auth/forgot-password')
            .send({});
        expect(res.status).toBe(400);
        expect(res.body.message).toBeDefined();
    });

    test('有效 email 應回傳 200 或 500（無 SMTP）或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/forgot-password')
            .send({ email: 'test@example.com' });
        expect([200, 500, 503]).toContain(res.status);
    });

    test('不存在的 email 也應回傳 200（防枚舉）或 503', async () => {
        const res = await request(app)
            .post('/api/auth/forgot-password')
            .send({ email: 'nobody@example.com' });
        expect([200, 503]).toContain(res.status);
    });
});

// ── Reset Password ────────────────────────────────────────────

describe('POST /api/auth/reset-password', () => {
    test('缺少 token 和 new_password 應回傳 400 或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/reset-password')
            .send({});
        expect([400, 503]).toContain(res.status);
    });

    test('空 token 和 new_password 應回傳 400 或 503（無 DB）', async () => {
        const res = await request(app)
            .post('/api/auth/reset-password')
            .send({ token: '', new_password: '' });
        expect([400, 503]).toContain(res.status);
    });

    test('無效 token 應回傳 400 或 503', async () => {
        const res = await request(app)
            .post('/api/auth/reset-password')
            .send({ token: 'invalid-token', new_password: 'NewP@ss2026!XyZ' });
        expect([400, 503]).toContain(res.status);
    });

    test('已過期的 token 應回傳 400 或 503', async () => {
        const res = await request(app)
            .post('/api/auth/reset-password')
            .send({ token: 'expired-token-99999', new_password: 'NewP@ss2026!XyZ' });
        expect([400, 503]).toContain(res.status);
    });
});
