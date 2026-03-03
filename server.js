const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(cors());
app.use(express.json());

// In-memory database to store our face counts
let faceCounts = {};

// Python will hit this endpoint when it recognizes a face
app.post('/api/sighting', (req, res) => {
    const { name } = req.body;
    
    if (name) {
        // Increment the count or start at 1
        faceCounts[name] = (faceCounts[name] || 0) + 1;
        
        // Broadcast the updated data to the Bootstrap frontend immediately
        io.emit('dashboard_update', faceCounts);
        console.log(`Sighting logged: ${name} (Total: ${faceCounts[name]})`);
        
        res.status(200).send({ success: true, counts: faceCounts });
    } else {
        res.status(400).send({ error: "No name provided" });
    }
});

server.listen(3000, () => {
    console.log('Server running on http://localhost:3000');
});