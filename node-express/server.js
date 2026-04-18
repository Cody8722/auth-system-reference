/**
 * Auth System Reference — Node.js + Express 實作
 *
 * 端點：
 *   POST /api/auth/register
 *   POST /api/auth/login
 *   POST /api/auth/logout
 *   POST /api/auth/forgot-password
 *   POST /api/auth/reset-password
 *   GET  /api/auth/verify
 *   GET  /api/status
 *   GET  /  （前端）
 *
 * 共用 accounting_db.users（與會計系統、排班系統帳號互通）
 * 密碼格式：PBKDF2-SHA256（相容 Python passlib）
 */

const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const path = require('path');
const jwt = require('jsonwebtoken');
const nodemailer = require('nodemailer');
const { MongoClient, ServerApiVersion } = require('mongodb');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

// ── 設定 ──────────────────────────────────────────────────────
const app = express();
const PORT = process.env.PORT || 3001;
const MONGODB_URI = process.env.MONGODB_URI;

// ── MongoDB ───────────────────────────────────────────────────
let client;
let usersCollection = null;
let isDbConnected = false;

if (MONGODB_URI) {
    client = new MongoClient(MONGODB_URI, {
        serverApi: { version: ServerApiVersion.v1, strict: true, deprecationErrors: true },
        connectTimeoutMS: 30000,
        socketTimeoutMS: 30000,
        retryWrites: true,
        retryReads: true,
        maxPoolSize: 10,
    });
} else {
    console.warn('警告: 未提供 MONGODB_URI，資料庫功能將被禁用。');
}

// ── 中介軟體 ──────────────────────────────────────────────────
app.set('trust proxy', 1);
app.use(cors({
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
}));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ── 速率限制 ──────────────────────────────────────────────────
const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10,
    standardHeaders: true,
    legacyHeaders: false,
    message: '登入嘗試次數過多，請於 15 分鐘後再試。',
});

const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    message: '請求次數過多，請稍後再試。',
});

const registerLimiter = rateLimit({
    windowMs: 60 * 60 * 1000,
    max: 5,
    standardHeaders: true,
    legacyHeaders: false,
    message: '註冊嘗試次數過多，請於 1 小時後再試。',
});

// ── 身份驗證中介軟體 ──────────────────────────────────────────
// 不需要 token 的 auth 端點（登入、登出、忘記/重設密碼）
const AUTH_PUBLIC_PATHS = new Set([
    '/auth/register', '/auth/login', '/auth/logout',
    '/auth/forgot-password', '/auth/reset-password',
    '/auth/validate-password',
]);

function requireAuth(req, res, next) {
    if (!process.env.JWT_SECRET) return next();
    if (AUTH_PUBLIC_PATHS.has(req.path)) return next();
    if (req.path === '/status' && req.method === 'GET') return next();

    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ message: '請先登入' });
    }
    const token = authHeader.slice(7);
    try {
        req.user = jwt.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] });
        next();
    } catch {
        return res.status(401).json({ message: '登入已過期，請重新登入' });
    }
}

app.use('/api/', requireAuth);

// ── PBKDF2-SHA256（相容 Python passlib 格式）─────────────────
// 格式：$pbkdf2-sha256$<rounds>$<ab64_salt>$<ab64_hash>
// ab64 = 標準 base64，但 '+' 換成 '.'，無 '=' padding
const ab64decode = s => {
    s = s.replace(/\./g, '+');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
};
const ab64encode = buf => buf.toString('base64').replace(/\+/g, '.').replace(/=/g, '');

function verifyPasslibPbkdf2(password, storedHash) {
    try {
        const parts = storedHash.split('$');
        if (parts.length < 5 || parts[1] !== 'pbkdf2-sha256') return false;
        const rounds = parseInt(parts[2]);
        const salt = ab64decode(parts[3]);
        const expected = ab64decode(parts[4]);
        const derived = crypto.pbkdf2Sync(password, salt, rounds, expected.length, 'sha256');
        return crypto.timingSafeEqual(derived, expected);
    } catch { return false; }
}

function hashPasslibPbkdf2(password) {
    const salt = crypto.randomBytes(16);
    const hash = crypto.pbkdf2Sync(password, salt, 29000, 32, 'sha256');
    return `$pbkdf2-sha256$29000$${ab64encode(salt)}$${ab64encode(hash)}`;
}

// ── 輸入驗證 ──────────────────────────────────────────────────
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validatePasswordStrength(password, email = '', name = '') {
    if (!password || password.length < 12)
        return { valid: false, message: '密碼長度至少需要 12 個字元' };
    if (!/[A-Z]/.test(password))
        return { valid: false, message: '密碼需包含至少一個大寫字母' };
    if (!/[a-z]/.test(password))
        return { valid: false, message: '密碼需包含至少一個小寫字母' };
    if (!/[0-9]/.test(password))
        return { valid: false, message: '密碼需包含至少一個數字' };
    if (!/[^A-Za-z0-9]/.test(password))
        return { valid: false, message: '密碼需包含至少一個特殊字元' };
    const lp = password.toLowerCase();
    if (email && lp.includes(email.split('@')[0].toLowerCase()))
        return { valid: false, message: '密碼不能包含 Email 帳號部分' };
    if (name && name.length >= 3 && lp.includes(name.toLowerCase()))
        return { valid: false, message: '密碼不能包含姓名' };
    return { valid: true, message: '密碼強度足夠' };
}

// ── Email（忘記密碼）─────────────────────────────────────────
function createMailTransporter() {
    if (!process.env.SMTP_USERNAME || !process.env.SMTP_PASSWORD) return null;
    return nodemailer.createTransport({
        host: 'smtp.gmail.com',
        port: 587,
        secure: false,
        auth: { user: process.env.SMTP_USERNAME, pass: process.env.SMTP_PASSWORD },
    });
}

async function sendResetEmail(toEmail, resetUrl) {
    const transporter = createMailTransporter();
    if (!transporter) { console.warn('SMTP 未設定，無法寄送密碼重設信'); return false; }
    const fromName = process.env.SMTP_FROM_NAME || 'Auth 參考系統';
    try {
        await transporter.sendMail({
            from: `"${fromName}" <${process.env.SMTP_USERNAME}>`,
            to: toEmail,
            subject: 'Auth 系統 — 密碼重設',
            html: `
            <div style="font-family:sans-serif;max-width:480px;margin:0 auto;">
                <h2 style="color:#0284c7;">密碼重設</h2>
                <p>我們收到了您的密碼重設請求。請點擊下方按鈕重設密碼：</p>
                <a href="${resetUrl}"
                   style="display:inline-block;padding:12px 24px;background:#0284c7;color:#fff;
                          border-radius:8px;text-decoration:none;font-weight:600;margin:16px 0;">
                    重設密碼
                </a>
                <p style="color:#6b7280;font-size:0.875rem;">
                    此連結將在 1 小時後失效。若非您本人操作，請忽略此信件。
                </p>
            </div>`,
        });
        console.log(`密碼重設信已寄送至: ${toEmail}`);
        return true;
    } catch (e) {
        console.error('寄送密碼重設信失敗:', e.message);
        return false;
    }
}

// ── 路由：身份驗證 ────────────────────────────────────────────

// POST /api/auth/register
app.post('/api/auth/register', registerLimiter, async (req, res) => {
    if (!usersCollection) return res.status(503).json({ message: '資料庫未連線' });
    try {
        const { email, password, name } = req.body || {};

        if (!email || !password || !name)
            return res.status(400).json({ message: 'email、password 和 name 不能為空' });

        const normalizedEmail = email.trim().toLowerCase();
        if (!EMAIL_REGEX.test(normalizedEmail))
            return res.status(400).json({ message: 'Email 格式錯誤' });

        const trimmedName = name.trim();
        if (trimmedName.length === 0)
            return res.status(400).json({ message: '名稱不能為空' });
        if (trimmedName.length > 50)
            return res.status(400).json({ message: '名稱過長（最多 50 字元）' });

        const pwCheck = validatePasswordStrength(password, normalizedEmail, trimmedName);
        if (!pwCheck.valid)
            return res.status(400).json({ message: pwCheck.message });

        const existing = await usersCollection.findOne({ email: normalizedEmail });
        if (existing) return res.status(409).json({ message: '此 Email 已被註冊' });

        const passwordHash = hashPasslibPbkdf2(password);
        const now = new Date();
        const result = await usersCollection.insertOne({
            email: normalizedEmail,
            password_hash: passwordHash,
            name: trimmedName,
            created_at: now,
            last_login: null,
            is_active: true,
            email_verified: false,
            password_last_updated: now,
        });
        console.log(`新用戶註冊: ${normalizedEmail}`);
        res.status(201).json({ message: '註冊成功', user_id: String(result.insertedId) });
    } catch (e) {
        console.error('註冊失敗:', e);
        res.status(500).json({ message: '註冊失敗，請稍後再試' });
    }
});

// POST /api/auth/login
app.post('/api/auth/login', authLimiter, async (req, res) => {
    if (!usersCollection) return res.status(503).json({ message: '資料庫未連線' });
    try {
        const { email, password } = req.body;
        if (!email || !password) return res.status(400).json({ message: 'Email 和密碼不能為空' });

        const user = await usersCollection.findOne({ email: email.trim().toLowerCase() });
        if (!user || !user.is_active) return res.status(401).json({ message: 'Email 或密碼錯誤' });

        if (!verifyPasslibPbkdf2(password, user.password_hash))
            return res.status(401).json({ message: 'Email 或密碼錯誤' });

        await usersCollection.updateOne({ _id: user._id }, { $set: { last_login: new Date() } });

        if (!process.env.JWT_SECRET) return res.status(500).json({ message: 'JWT_SECRET 未設定' });

        const token = jwt.sign(
            { user_id: String(user._id), email: user.email, name: user.name || '', type: 'access' },
            process.env.JWT_SECRET,
            { algorithm: 'HS256', expiresIn: '7d' }
        );
        console.log(`用戶登入: ${user.email}`);
        res.json({ token, user: { id: String(user._id), email: user.email, name: user.name || '' } });
    } catch (e) {
        console.error('登入失敗:', e);
        res.status(500).json({ message: '登入失敗，請稍後再試' });
    }
});

// POST /api/auth/forgot-password
app.post('/api/auth/forgot-password', authLimiter, async (req, res) => {
    try {
        const { email } = req.body;
        if (!email) return res.status(400).json({ message: '請提供 Email' });

        if (usersCollection) {
            const user = await usersCollection.findOne({ email: email.trim().toLowerCase() });
            if (user) {
                const token = crypto.randomBytes(32).toString('hex');
                const expires = new Date(Date.now() + 60 * 60 * 1000); // 1 小時
                await usersCollection.updateOne(
                    { _id: user._id },
                    { $set: { password_reset_token: token, password_reset_expires: expires } }
                );
                const origin = req.headers.origin || `http://localhost:${PORT}`;
                const resetUrl = `${origin}?reset_token=${token}`;
                const sent = await sendResetEmail(user.email, resetUrl);
                if (!sent) return res.status(500).json({ message: '郵件服務未設定或發送失敗，請聯繫管理員' });
            }
        }
        // 無論 email 存不存在都回 200（防帳號列舉攻擊）
        res.json({ message: '若此 Email 已註冊，重設連結已寄出' });
    } catch (e) {
        console.error('忘記密碼失敗:', e);
        res.status(500).json({ message: '系統錯誤' });
    }
});

// POST /api/auth/reset-password
app.post('/api/auth/reset-password', async (req, res) => {
    if (!usersCollection) return res.status(503).json({ message: '資料庫未連線' });
    try {
        const { token, new_password } = req.body;
        if (!token || !new_password) return res.status(400).json({ message: '請提供 token 和新密碼' });

        const user = await usersCollection.findOne({ password_reset_token: token });
        if (!user) return res.status(400).json({ message: '連結無效或已過期' });

        const expires = user.password_reset_expires;
        if (!expires || new Date() > new Date(expires))
            return res.status(400).json({ message: '連結已過期，請重新申請' });

        const newHash = hashPasslibPbkdf2(new_password);
        await usersCollection.updateOne(
            { _id: user._id },
            {
                $set: { password_hash: newHash, password_last_updated: new Date() },
                $unset: { password_reset_token: '', password_reset_expires: '' },
            }
        );
        console.log(`用戶已重設密碼: ${user.email}`);
        res.json({ message: '密碼已重設，請重新登入' });
    } catch (e) {
        console.error('重設密碼失敗:', e);
        res.status(500).json({ message: '系統錯誤' });
    }
});

// POST /api/auth/logout
app.post('/api/auth/logout', (req, res) => res.json({ message: '已登出' }));

// GET /api/auth/verify
app.get('/api/auth/verify', apiLimiter, (req, res) => {
    if (!req.user) return res.status(401).json({ message: '未登入' });
    res.json({ valid: true, user: req.user });
});

// GET /api/status
app.get('/api/status', (req, res) => {
    res.json({
        server: 'running',
        database: isDbConnected ? 'connected' : 'disconnected',
        auth_required: !!process.env.JWT_SECRET,
    });
});

// favicon
app.get('/favicon.ico', (req, res) => res.status(204).end());

// ── 啟動 ──────────────────────────────────────────────────────
const startServer = async () => {
    if (!client) {
        app.listen(PORT, () => console.log(`Auth server running at http://localhost:${PORT} (無 DB 模式)`));
        return;
    }
    try {
        await client.connect();
        await client.db('admin').command({ ping: 1 });
        usersCollection = client.db('accounting_db').collection('users');
        isDbConnected = true;
        console.log('✅ 已連接到 accounting_db.users');
        app.listen(PORT, () => console.log(`Auth server running at http://localhost:${PORT}`));
    } catch (err) {
        console.error('❌ MongoDB 連線失敗:', err.message);
        process.exit(1);
    }
};

if (process.env.NODE_ENV !== 'test') {
    startServer();
}

module.exports = app;
