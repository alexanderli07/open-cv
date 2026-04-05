# note to self, import everything lol
import cv2
import face_recognition
import numpy as np
import os
import time
import logging
import requests
import faiss
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Configure logging for debugging and runtime info
logging.basicConfig(level=logging.INFO)

# Data structure to represent a detection event
@dataclass
class DetectionEvent:
    name: str
    confidence: float
    timestamp: float


class VisionSystem:

    def __init__(self, face_folder, server_url):

        # API endpoint to send detection events
        self.server_url = server_url

        # Thread pool for async tasks (network calls, saving images)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Used for motion detection
        self.prev_frame = None
        self.prev_time = 0

        # Cooldown (seconds) before the same person can trigger again
        self.cooldown = 5
        self.last_seen = {}

        # Known face data
        self.known_names = []
        self.encodings = []

        # Load known faces from folder
        self.load_database(face_folder)

        # Initialize FAISS vector index for fast similarity search
        self.init_vector_index()

        # Folder to store captured face images
        os.makedirs("sightings", exist_ok=True)

    def load_database(self, folder):

        logging.info("Loading face database...")

        # Loop through all files in the face folder
        for file in os.listdir(folder):

            path = os.path.join(folder, file)

            # Load image and compute face encodings
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)

            # Only keep images where a face was detected
            if encoding:
                self.encodings.append(encoding[0])
                # Use filename (without extension) as label
                self.known_names.append(os.path.splitext(file)[0])

        logging.info(f"Loaded {len(self.known_names)} identities")

    def init_vector_index(self):

        # Face encodings are 128-dimensional vectors
        dimension = 128

        # FAISS index using L2 (Euclidean distance)
        self.index = faiss.IndexFlatL2(dimension)

        if len(self.encodings) > 0:
            vectors = np.array(self.encodings).astype("float32")
            self.index.add(vectors)  # Add known faces to index

    def detect_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0) # Smooth out the noise
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return True

        diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        motion_sum = np.sum(thresh)
        
        self.prev_frame = gray
        return motion_sum > 5000 # Trigger based on pixel count, not just mean

    def match_face(self, encoding):

        # If no known faces, always return unknown
        if len(self.encodings) == 0:
            return "Unknown", 0

        # Search for closest match in FAISS index
        D, I = self.index.search(np.array([encoding]).astype("float32"), 1)

        distance = D[0][0]
        idx = I[0][0]

        # Convert distance to a rough confidence score
        confidence = 1 - distance

        # Threshold for recognition (lower distance = better match)
        if distance < 0.6:
            return self.known_names[idx], confidence

        return "Unknown", confidence

    def send_event(self, event: DetectionEvent):

        try:
            # Send POST request to server with detection info
            requests.post(
                self.server_url,
                json={
                    "name": event.name,
                    "confidence": event.confidence,
                    "timestamp": event.timestamp
                },
                timeout=2
            )

        except Exception as e:
            # Avoid crashing if server is down
            logging.warning("Server unreachable")

    def save_face(self, frame, name):

        # Save snapshot of detected face with timestamp
        filename = f"sightings/{name}_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)

    def process_frame(self, frame):

        start = time.perf_counter()

        # Skip processing if no motion detected (optimization)
        if not self.detect_motion(frame):
            return frame

        # Downscale frame for faster face detection
        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        # Detect face locations and compute encodings
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for (top, right, bottom, left), encoding in zip(locations, encodings):

            # Match detected face against known database
            name, confidence = self.match_face(encoding)

            # Scale coordinates back to original frame size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Yellow for known, red for unknown
            color = (0, 255, 255) if name != "Unknown" else (0, 0, 255)

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw label text
            cv2.putText(
                frame,
                f"{name} {confidence:.2f}",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            now = time.time()

            if name != "Unknown":

                # Check cooldown to avoid spamming events
                if name not in self.last_seen or now - self.last_seen[name] > self.cooldown:

                    self.last_seen[name] = now

                    event = DetectionEvent(name, confidence, now)

                    # Send event asynchronously
                    self.executor.submit(self.send_event, event)

                    # Save image locally
                    self.save_face(frame, name)

                    logging.info(f"Detected {name}")

        # Measure processing latency
        latency = (time.perf_counter() - start) * 1000

        # Compute FPS
        now = time.time()
        fps = int(1 / (now - self.prev_time)) if self.prev_time else 0
        self.prev_time = now

        # Display FPS and latency on screen
        cv2.putText(frame, f"FPS: {fps}", (10, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,255,0),2)
        cv2.putText(frame, f"Latency: {latency:.1f}ms", (10,70), cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,255),1)

        return frame


def main():

    # Initialize vision system
    tracker = VisionSystem(
        face_folder="faces",
        server_url="http://localhost:3000/api/sighting"
    )

    # Start webcam capture
    cam = cv2.VideoCapture(0)

    while cam.isOpened():

        ret, frame = cam.read()

        if not ret:
            break

        # Process each frame
        frame = tracker.process_frame(frame)

        # Display output window
        cv2.imshow("AI Face Recognition System", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup resources
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
