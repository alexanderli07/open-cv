// Connect to backend Socket.IO server
const socket = io("http://localhost:3000")

// DOM elements for UI updates
const feed = document.getElementById("eventFeed")
const topSubjects = document.getElementById("topSubjects")
const totalMetric = document.getElementById("totalDetections")

// Stores total detections per subject (name -> count)
let counts = {}

// Stores time-series data for timeline chart
let timeline = []

// Bar chart showing frequency of detections per subject
const freqChart = new Chart(
  document.getElementById("frequencyChart"),
  {
    type: "bar",
    data: {
      labels: [], // subject names
      datasets: [{
        label: "Detections",
        data: [] // counts per subject
      }]
    },
    options: {
      plugins: { legend: { display: false } }, // hide legend for cleaner UI
      scales: { y: { beginAtZero: true } } // ensure y-axis starts at 0
    }
  }
)

// Line chart showing detection count over time
const timelineChart = new Chart(
  document.getElementById("timelineChart"),
  {
    type: "line",
    data: {
      labels: [], // timestamps
      datasets: [{
        label: "Events",
        data: [] // total detections over time
      }]
    }
  }
)

// Listen for real-time face detection events from backend
socket.on("face_event", (data) => {

  const { subject, confidence, total } = data

  // Update count for this subject (server sends cumulative total)
  counts[subject] = total

  // Compute total detections across all subjects
  let totalDetections = Object.values(counts).reduce((a, b) => a + b, 0)

  // Update total metric display
  totalMetric.innerText = totalDetections

  // Update UI components
  updateSubjects()
  addFeed(subject, confidence)
  updateCharts()
})

// Updates the "Top Subjects" table
function updateSubjects() {

  // Clear existing rows
  topSubjects.innerHTML = ""

  // Sort subjects by count descending, take top 5
  Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .forEach(([name, count]) => {

      // Append row for each subject
      topSubjects.innerHTML += `
        <tr>
          <td>${name}</td>
          <td class="text-end">${count}</td>
        </tr>
      `
    })
}

// Adds a new event to the live feed
function addFeed(name, confidence) {

  const el = document.createElement("div")
  el.className = "feed-item"

  // Create feed entry with subject, confidence, and timestamp
  el.innerHTML = `
    <span class="subject">${name}</span>
    <span class="confidence">(${confidence.toFixed(2)})</span>
    <span class="text-muted float-end">${new Date().toLocaleTimeString()}</span>
  `

  // Add new event to top of feed
  feed.prepend(el)

  // Keep only latest 10 events to prevent DOM bloat
  if (feed.children.length > 10) {
    feed.removeChild(feed.lastChild)
  }
}

// Updates both charts (frequency + timeline)
function updateCharts() {

  // --- Update frequency bar chart ---
  freqChart.data.labels = Object.keys(counts) // subject names
  freqChart.data.datasets[0].data = Object.values(counts) // counts
  freqChart.update()

  // --- Update timeline data ---
  timeline.push({
    time: new Date().toLocaleTimeString(),
    count: Object.values(counts).reduce((a, b) => a + b, 0) // total detections
  })

  // Keep only last 20 points for readability/performance
  if (timeline.length > 20) timeline.shift()

  // Apply timeline data to chart
  timelineChart.data.labels = timeline.map(t => t.time)
  timelineChart.data.datasets[0].data = timeline.map(t => t.count)
  timelineChart.update()
}