# 👁️ AI Face Recognition Real-Time Dashboard

A sleek, high-performance monitoring interface designed to visualize face recognition data in real-time. This dashboard transforms raw detection events into an actionable "Command Center" view, prioritizing readability and modern "Stealth Mode" aesthetics.

---

## 🚀 Overview

This project provides a front-end visualization layer for face recognition systems. It communicates with a backend server via WebSockets to provide instantaneous updates on subject detections without requiring a page refresh.

### 🎨 Design Philosophy: "Stealth Mode"
The interface moves away from traditional light-mode admin tools, opting for a **Cyberpunk-inspired Dark Theme**:
* **Glassmorphism:** The main dashboard uses semi-transparent layers and subtle borders to create depth.
* **Visual Hierarchy:** Subject names are highlighted in **Cyan badges**, while detection counts use **Gold typography** to ensure critical data points are immediately visible.
* **Micro-Interactions:** Includes a "Live System" pulsing indicator and smooth row-slide animations for an interactive feel.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Custom Variables), Bootstrap 5.3 |
| **Real-Time Engine** | [Socket.io](https://socket.io/) (Bi-directional WebSocket Client) |
| **Typography** | Inter (UI), JetBrains Mono (Data/Monospace) |
| **Icons/UI** | Custom CSS Animations & SVG Pulsers |

---

## 📡 System Architecture & Data Flow

The dashboard operates on a **Push Model**, ensuring high efficiency and low latency:



1.  **Detection Event:** The AI engine identifies a face in the camera stream.
2.  **Socket Emit:** The backend server (running on `localhost:3000`) emits a `dashboard_update` event containing a JSON payload of results.
3.  **DOM Reconstruction:** The frontend listens for the event, clears the current view, and injects updated counts using optimized JavaScript template literals.

---

## ✨ Key Features

* **Live Frequency Tracking:** Automatically increments and displays how many times a specific subject has been spotted.
* **Responsive Layout:** Fully fluid design that scales from mobile monitoring to 4K security displays.
* **State Management:** Includes a "Waiting for Data" spinner and fallback UI for when the camera stream or server is inactive.
* **Theming Engine:** All aesthetics are managed via `style.css` using CSS Variables (`:root`), allowing for "one-line" branding changes (e.g., changing the accent color from Cyan to Red).

---

## 📂 Project Structure

```text
├── index.html      # Structural layout and Socket.io logic
├── style.css       # Custom "Stealth Mode" styles and animations
└── README.md       # Project documentation