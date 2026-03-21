# 👁️ Open CV

A real-time dashboard for visualizing face recognition data. I built this to turn raw backend detection logs into a clean, easy-to-read "Command Center." 

---

## 🚀 Overview

Think of this as the front-end face for your face recognition system. Instead of watching logs scroll by in a terminal, this hooks into your backend via WebSockets to give you live, instant updates as people are detected—no page refreshing required.

### 🎨 Design: "Stealth Mode"
I wanted to step away from the boring, bright-white admin panels. The UI uses a dark, slightly cyberpunk-inspired theme:
* **Glassmorphism:** Frosted glass effects and subtle borders give the dashboard some depth.
* **Quick Scanning:** Names pop in **Cyan**, and detection counts are highlighted in **Gold** so you can read the data at a glance.
* **It feels alive:** I added a pulsing "Live System" indicator and smooth row animations so the dashboard actually feels active when data is flowing.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Custom Variables), Bootstrap 5.3 |
| **Real-Time** | [Socket.io](https://socket.io/) (Bi-directional WebSocket Client) |
| **Typography** | Inter (UI), JetBrains Mono (Data/Monospace) |
| **Icons/UI** | Custom CSS Animations & SVG Pulsers |

---

## 📡 How It Works

The data flow is pretty straightforward:

1. **Detect:** Your AI engine spots a face on the camera stream.
2. **Ping:** The backend server (running on `localhost:3000`) fires off a `dashboard_update` Socket event with the data payload.
3. **Update:** The frontend catches the event, clears the old view, and injects the new counts instantly.

---

## ✨ Features

* **Live Frequency Tracking:** Automatically tracks and displays how many times a specific person has been recognized.
* **Responsive:** Looks just as good on your phone as it does on a massive 4K security monitor.
* **Graceful Waiting:** Shows a clean loading spinner if the camera stream drops or the server is still booting up.
* **Easy Theming:** All aesthetics are tied to CSS variables in `style.css`. Want to swap the cyberpunk cyan for an alert red? You can do it in one line.

---

## 📂 Project Structure

```text
├── index.html      # Structural layout and Socket.io logic
├── style.css       # Custom "Stealth Mode" styles and animations
└── README.md       # Project documentation
