const express = require('express')
const http = require('http')
const cors = require('cors')
const jwt = require('jsonwebtoken')
const bcrypt = require('bcrypt')
const mongoose = require('mongoose')
const sqlite3 = require('sqlite3').verbose()
const { Server } = require('socket.io')
const rateLimit = require('express-rate-limit')
const path = require('path')

const app = express()
const server = http.createServer(app)

const io = new Server(server, {
    cors: { origin: "*" }
})

app.use(cors())
app.use(express.json())

// Serve dashboard files
app.use(express.static(path.join(__dirname, 'public')))

// Rate limiting
const limiter = rateLimit({
    windowMs: 60 * 1000,
    max: 200
})

app.use('/api', limiter)

const JWT_SECRET = "replace_with_secure_key"


// MongoDB (Sightings)
mongoose.connect('mongodb://127.0.0.1:27017/ai_tracker')
.then(() => {
    console.log("Connected to MongoDB (Sightings)")
})
.catch(err => {
    console.error("MongoDB connection error:", err)
})

const sightingSchema = new mongoose.Schema({
    subjectName: String,
    confidence: Number,
    timestamp: { type: Date, default: Date.now }
})

const Sighting = mongoose.model('Sighting', sightingSchema)


// SQLite (User Accounts)

const sqlDb = new sqlite3.Database('./users.db')

sqlDb.run(`
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT
)
`)


// Service Layer

class SightingService {

    async record(name, confidence){

        const sight = new Sighting({
            subjectName: name,
            confidence: confidence
        })

        await sight.save()

        return await Sighting.countDocuments({
            subjectName: name
        })
    }

}

const sightingService = new SightingService()


// API: Receive face detection events from Python

app.post('/api/sighting', async (req,res)=>{

    try{

        const { name, confidence } = req.body

        if(!name) return res.status(400).send()

        const count = await sightingService.record(name, confidence)

        io.emit("face_event", {
            subject: name,
            confidence: confidence,
            total: count
        })

        res.send({success:true})

    }
    catch(err){

        console.error("Sighting error:", err)
        res.status(500).send()

    }

})


// User Registration

app.post('/register', async (req,res)=>{

    const {username,password} = req.body

    try{

        const hash = await bcrypt.hash(password,10)

        sqlDb.run(
            `INSERT INTO users(username,password) VALUES(?,?)`,
            [username,hash],
            function(err){

                if(err){
                    return res.status(400).send({error:"Username may already exist"})
                }

                res.send({userId:this.lastID})

            }
        )

    }
    catch(err){

        res.status(500).send()

    }

})


// Login

app.post('/login',(req,res)=>{

    const {username,password} = req.body

    sqlDb.get(`SELECT * FROM users WHERE username=?`,[username], async(err,user)=>{

        if(err || !user) return res.status(401).send()

        const match = await bcrypt.compare(password,user.password)

        if(!match) return res.status(401).send()

        const token = jwt.sign(
            {id:user.id},
            JWT_SECRET,
            {expiresIn:"2h"}
        )

        res.send({token})

    })

})


// Start server

server.listen(3000,()=>{

    console.log("Server running on:")
    console.log("http://localhost:3000")
    console.log("Dashboard: http://localhost:3000/dashboard.html")

})