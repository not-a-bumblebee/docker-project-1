const express = require('express');
const mysql = require('mysql2/promise');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const app = express();
app.use(express.json());

const JWT_SECRET = process.env.AUTH_TOKEN_SECRET || 'super-secret-jwt-key-change-me';

async function getPool() {
    return mysql.createPool({
        host: process.env.DB_HOST || 'mysql',
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || 'rootpassword',
        database: process.env.DB_NAME || 'analytics_db',
        waitForConnections: true,
        connectionLimit: 5
    });
}

async function initDbWithRetry(retries = 15, delay = 3000) {
    for (let i = 0; i < retries; i++) {
        try {
            const pool = await getPool();
            const [rows] = await pool.query('SELECT * FROM users WHERE username = ?', ['admin']);
            if (rows.length === 0) {
                const hashed = await bcrypt.hash('password123', 10);
                await pool.query('INSERT INTO users (username, password) VALUES (?, ?)', ['admin', hashed]);
            }
            console.log('Auth service database ready and admin seeded.');
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