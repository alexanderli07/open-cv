const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const mongoose = require('mongoose');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(cors());
app.use(express.json());

const JWT_SECRET = "super_secret_ai_key_change_this_later";

// ==========================================
// 1. SQL DATABASE SETUP (Users & Auth)
// ==========================================
const sqlDb = new sqlite3.Database('./users.db');

sqlDb.serialize(() => {
    // Create a users table if it doesn't exist
    sqlDb.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )`);
});

// ==========================================
// 2. MONGODB SETUP (Face Sightings Logs)
// ==========================================
// Make sure MongoDB is running locally, or replace with a MongoDB Atlas URI
mongoose.connect('mongodb://127.0.0.1:27017/ai_tracker')
    .then(() => console.log('Connected to MongoDB (Sightings Database)'))
    .catch(err => console.error('MongoDB connection error:', err));

const sightingSchema = new mongoose.Schema({
    subjectName: String,
    timestamp: { type: Date, default: Date.now },
    cameraLocation: { type: String, default: "Main Webcam" }
});
const Sighting = mongoose.model('Sighting', sightingSchema);

// ==========================================
// 3. AUTHENTICATION ROUTES (Using SQL)
// ==========================================
app.post('/register', async (req, res) => {
    const { username, password } = req.body;
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        sqlDb.run(`INSERT INTO users (username, password) VALUES (?, ?)`, [username, hashedPassword], function(err) {
            if (err) return res.status(400).json({ error: "Username might already exist." });
            res.json({ message: "User registered successfully!", userId: this.lastID });
        });
    } catch (err) {
        res.status(500).json({ error: "Server error during registration." });
    }
});

app.post('/login', (req, res) => {
    const { username, password } = req.body;
    sqlDb.get(`SELECT * FROM users WHERE username = ?`, [username], async (err, user) => {
        if (err || !user) return res.status(401).json({ error: "Invalid credentials." });
        
        const match = await bcrypt.compare(password, user.password);
        if (!match) return res.status(401).json({ error: "Invalid credentials." });

        // Give the user a secure token valid for 2 hours
        const token = jwt.sign({ userId: user.id, username: user.username }, JWT_SECRET, { expiresIn: '2h' });
        res.json({ message: "Login successful", token });
    });
});

// Middleware to protect routes (ensure user is logged in)
const authenticateToken = (req, res, next) => {
    const token = req.headers['authorization']?.split(' ')[1];
    if (!token) return res.status(403).json({ error: "Access denied. No token provided." });

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) return res.status(403).json({ error: "Invalid or expired token." });
        req.user = user;
        next();
    });
};

// ==========================================
// 4. AI TRACKER API (Using MongoDB)
// ==========================================
// Python will hit this endpoint to log faces. (We can protect this with tokens later!)
app.post('/api/sighting', async (req, res) => {
    const { name } = req.body;
    if (!name) return res.status(400).send({ error: "No name provided" });

    try {
        // Save the event permanently in MongoDB
        const newSighting = new Sighting({ subjectName: name });
        await newSighting.save();

        // Get the total count of times this specific person was seen
        const count = await Sighting.countDocuments({ subjectName: name });

        // Broadcast the update to the frontend dashboard
        io.emit('dashboard_update', { name: name, totalSighted: count });
        console.log(`[MongoDB Logged] ${name} spotted! Total: ${count}`);

        res.status(200).send({ success: true, count });
    } catch (err) {
        res.status(500).send({ error: "Failed to save sighting to database." });
    }
});

// Secure endpoint to pull historical data (Requires Login)
app.get('/api/history', authenticateToken, async (req, res) => {
    try {
        const history = await Sighting.find().sort({ timestamp: -1 }).limit(50);
        res.json({ user: req.user.username, data: history });
    } catch (err) {
        res.status(500).send({ error: "Failed to fetch history." });
    }
});

server.listen(3000, () => {
    console.log('Polyglot Server running on http://localhost:3000');
});