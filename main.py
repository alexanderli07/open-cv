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

logging.basicConfig(level=logging.INFO)

@dataclass
class DetectionEvent:
    name: str
    confidence: float
    timestamp: float


class VisionSystem:

    def __init__(self, face_folder, server_url):

        self.server_url = server_url
        self.executor = ThreadPoolExecutor(max_workers=4)

        self.prev_frame = None
        self.prev_time = 0

        self.cooldown = 5
        self.last_seen = {}

        self.known_names = []
        self.encodings = []

        self.load_database(face_folder)

        self.init_vector_index()

        os.makedirs("sightings", exist_ok=True)

    def load_database(self, folder):

        logging.info("Loading face database...")

        for file in os.listdir(folder):

            path = os.path.join(folder, file)

            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)

            if encoding:

                self.encodings.append(encoding[0])
                self.known_names.append(os.path.splitext(file)[0])

        logging.info(f"Loaded {len(self.known_names)} identities")

    def init_vector_index(self):

        dimension = 128

        self.index = faiss.IndexFlatL2(dimension)

        if len(self.encodings) > 0:

            vectors = np.array(self.encodings).astype("float32")

            self.index.add(vectors)

    def detect_motion(self, frame):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_frame is None:
            self.prev_frame = gray
            return True

        diff = cv2.absdiff(self.prev_frame, gray)
        motion = diff.mean()

        self.prev_frame = gray

        return motion > 2

    def match_face(self, encoding):

        if len(self.encodings) == 0:
            return "Unknown", 0

        D, I = self.index.search(np.array([encoding]).astype("float32"), 1)

        distance = D[0][0]
        idx = I[0][0]

        confidence = 1 - distance

        if distance < 0.6:
            return self.known_names[idx], confidence

        return "Unknown", confidence

    def send_event(self, event: DetectionEvent):

        try:

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

            logging.warning("Server unreachable")

    def save_face(self, frame, name):

        filename = f"sightings/{name}_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)

    def process_frame(self, frame):

        start = time.perf_counter()

        if not self.detect_motion(frame):
            return frame

        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for (top, right, bottom, left), encoding in zip(locations, encodings):

            name, confidence = self.match_face(encoding)

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 255) if name != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

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

                if name not in self.last_seen or now - self.last_seen[name] > self.cooldown:

                    self.last_seen[name] = now

                    event = DetectionEvent(name, confidence, now)

                    self.executor.submit(self.send_event, event)

                    self.save_face(frame, name)

                    logging.info(f"Detected {name}")

        latency = (time.perf_counter() - start) * 1000

        now = time.time()
        fps = int(1 / (now - self.prev_time)) if self.prev_time else 0
        self.prev_time = now

        cv2.putText(frame, f"FPS: {fps}", (10, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,255,0),2)
        cv2.putText(frame, f"Latency: {latency:.1f}ms", (10,70), cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,255),1)

        return frame


def main():

    tracker = VisionSystem(
        face_folder="faces",
        server_url="http://localhost:3000/api/sighting"
    )

    cam = cv2.VideoCapture(0)

    while cam.isOpened():

        ret, frame = cam.read()

        if not ret:
            break

        frame = tracker.process_frame(frame)

        cv2.imshow("AI Face Recognition System", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()