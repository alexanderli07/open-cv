const socket = io("http://localhost:3000")

const feed = document.getElementById("eventFeed")
const topSubjects = document.getElementById("topSubjects")
const totalMetric = document.getElementById("totalDetections")

let counts = {}
let timeline = []

const freqChart = new Chart(
document.getElementById("frequencyChart"),
{
type:"bar",
data:{
labels:[],
datasets:[{
label:"Detections",
data:[]
}]
},
options:{
plugins:{legend:{display:false}},
scales:{y:{beginAtZero:true}}
}
}
)

const timelineChart = new Chart(
document.getElementById("timelineChart"),
{
type:"line",
data:{
labels:[],
datasets:[{
label:"Events",
data:[]
}]
}
}
)

socket.on("face_event",(data)=>{

const {subject,confidence,total} = data

counts[subject] = total

let totalDetections = Object.values(counts).reduce((a,b)=>a+b,0)

totalMetric.innerText = totalDetections

updateSubjects()

addFeed(subject,confidence)

updateCharts()

})

function updateSubjects(){

topSubjects.innerHTML=""

Object.entries(counts)
.sort((a,b)=>b[1]-a[1])
.slice(0,5)
.forEach(([name,count])=>{

topSubjects.innerHTML+=`

<tr>
<td>${name}</td>
<td class="text-end">${count}</td>
</tr>

`

})

}

function addFeed(name,confidence){

const el=document.createElement("div")

el.className="feed-item"

el.innerHTML=`
<span class="subject">${name}</span>
<span class="confidence">(${confidence.toFixed(2)})</span>
<span class="text-muted float-end">${new Date().toLocaleTimeString()}</span>
`

feed.prepend(el)

if(feed.children.length>10){
feed.removeChild(feed.lastChild)
}

}

function updateCharts(){

freqChart.data.labels = Object.keys(counts)
freqChart.data.datasets[0].data = Object.values(counts)
freqChart.update()

timeline.push({
time:new Date().toLocaleTimeString(),
count:Object.values(counts).reduce((a,b)=>a+b,0)
})

if(timeline.length>20) timeline.shift()

timelineChart.data.labels = timeline.map(t=>t.time)
timelineChart.data.datasets[0].data = timeline.map(t=>t.count)
timelineChart.update()

}