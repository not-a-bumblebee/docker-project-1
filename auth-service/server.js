const express = require('express');
const mysql = require('mysql2/promise');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const app = express();
app.use(express.json());

// Required settings come from the environment (docker-compose / .env). There are no built-in
// fallbacks: if one is missing the service stops with a clear message instead of silently
// running with a guessable default.
function requireEnv(name) {
    const value = process.env[name];
    if (!value) {
        console.error(`Missing required environment variable: ${name}`);
        process.exit(1);
    }
    return value;
}

const JWT_SECRET = requireEnv('AUTH_TOKEN_SECRET');
const ADMIN_USERNAME = requireEnv('ADMIN_USERNAME');
const ADMIN_PASSWORD = requireEnv('ADMIN_PASSWORD');

// One pool for the whole service (the old getPool() created a brand-new pool on every request).
const pool = mysql.createPool({
    host: process.env.DB_HOST || 'mysql',
    user: requireEnv('DB_USER'),
    password: requireEnv('DB_PASSWORD'),
    database: process.env.DB_NAME || 'analytics_db',
    waitForConnections: true,
    connectionLimit: 5
});

async function getPool() {
    return pool;
}


// Creates the default admin account for the web app login
async function seedAdmin() {
    const [rows] = await pool.query('SELECT * FROM users WHERE username = ?', [ADMIN_USERNAME]);
    if (rows.length === 0) {
        const hashed = await bcrypt.hash(ADMIN_PASSWORD, 10);
        await pool.query('INSERT INTO users (username, password) VALUES (?, ?)', [ADMIN_USERNAME, hashed]);
        console.log(`Created default user "${ADMIN_USERNAME}".`);
    } else if (!(await bcrypt.compare(ADMIN_PASSWORD, rows[0].password))) {
        const hashed = await bcrypt.hash(ADMIN_PASSWORD, 10);
        await pool.query('UPDATE users SET password = ? WHERE username = ?', [hashed, ADMIN_USERNAME]);
        console.log(`Updated the password for "${ADMIN_USERNAME}" to match the environment.`);
    }
}

async function initDbWithRetry(retries = 15, delay = 3000) {
    for (let i = 0; i < retries; i++) {
        try {
            await seedAdmin();
            console.log('Auth service database ready.');
            return;
        } catch (err) {
            console.log(`Attempt ${i + 1}/${retries}: Waiting for MySQL tables... (${err.message})`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    console.error('Failed to connect to MySQL after multiple retries.');
}

initDbWithRetry();

app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const pool = await getPool();
        const [rows] = await pool.query('SELECT * FROM users WHERE username = ?', [username]);
        
        if (rows.length > 0) {
            const match = await bcrypt.compare(password, rows[0].password);
            if (match) {
                const token = jwt.sign({ username: rows[0].username }, JWT_SECRET, { expiresIn: '1h' });
                return res.json({ success: true, token });
            }
        }
        res.status(401).json({ success: false, message: "Invalid credentials" });
    } catch (err) {
        res.status(500).json({ error: "Database error during login" });
    }
});

app.post('/verify', (req, res) => {
    const { token } = req.body;
    if (!token) {
        return res.status(401).json({ valid: false });
    }
    
    jwt.verify(token, JWT_SECRET, (err, decoded) => {
        if (err) {
            return res.status(401).json({ valid: false });
        }
        res.json({ valid: true, user: decoded.username });
    });
});

app.listen(3000, () => console.log('Auth Service running on port 3000'));