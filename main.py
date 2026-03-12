import cv2
import face_recognition
import os
import time
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor


class FullStackFaceTracker:

    def __init__(self, faceFolder, serverUrl):

        print("Loading face database...")

        self.knownEncodings = []
        self.knownNames = []

        self.loadFaceDatabase(faceFolder)

        print(f"Loaded {len(self.knownNames)} known identities")

        self.serverUrl = serverUrl
        self.cooldownPeriod = 5
        self.lastSighting = {}

        self.executor = ThreadPoolExecutor(max_workers=4)

        self.prevTime = 0
        self.previousFrame = None

        os.makedirs("sightings", exist_ok=True)

    def loadFaceDatabase(self, folder):

        for file in os.listdir(folder):

            path = os.path.join(folder, file)

            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:

                self.knownEncodings.append(encodings[0])
                self.knownNames.append(os.path.splitext(file)[0])

    def logEvent(self, name):

        with open("sightings.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {name}\n")

    def saveFace(self, frame, name):

        filename = f"sightings/{name}_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)

    def sendSighting(self, name, confidence):

        try:

            requests.post(
                self.serverUrl,
                json={
                    "name": name,
                    "confidence": float(confidence),
                    "timestamp": time.time()
                },
                timeout=2
            )

            print(f"[{time.strftime('%X')}] Logged {name}")

        except Exception as e:

            print("Server connection failed:", e)

    def drawHud(self, img, x, y, w, h, color):

        length = 25
        thickness = 3

        cv2.line(img, (x, y), (x + length, y), color, thickness)
        cv2.line(img, (x, y), (x, y + length), color, thickness)

        cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)

        cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)

        cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)

    def processFrame(self, frame):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.previousFrame is not None:

            diff = cv2.absdiff(self.previousFrame, gray)
            motion = diff.mean()

            if motion < 2:
                return frame

        self.previousFrame = gray

        smallFrame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgbSmallFrame = cv2.cvtColor(smallFrame, cv2.COLOR_BGR2RGB)

        faceLocations = face_recognition.face_locations(rgbSmallFrame)
        faceEncodings = face_recognition.face_encodings(rgbSmallFrame, faceLocations)

        for (top, right, bottom, left), faceEncoding in zip(faceLocations, faceEncodings):

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            name = "Unknown"
            confidence = 0
            hudColor = (0, 0, 255)

            if len(self.knownEncodings) > 0:

                distances = face_recognition.face_distance(self.knownEncodings, faceEncoding)
                bestMatch = np.argmin(distances)

                confidence = 1 - distances[bestMatch]

                if distances[bestMatch] < 0.6:

                    name = self.knownNames[bestMatch]
                    hudColor = (0, 255, 255)

                    now = time.time()

                    if name not in self.lastSighting or now - self.lastSighting[name] > self.cooldownPeriod:

                        self.lastSighting[name] = now

                        self.executor.submit(self.sendSighting, name, confidence)
                        self.logEvent(name)
                        self.saveFace(frame, name)

            self.drawHud(frame, left, top, right - left, bottom - top, hudColor)

            cv2.putText(
                frame,
                f"{name} {confidence:.2f}",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                hudColor,
                2
            )

        scanY = int(time.time() * 200) % frame.shape[0]

        cv2.line(frame, (0, scanY), (frame.shape[1], scanY), (0, 255, 0), 1)

        currentTime = time.time()

        fps = int(1 / (currentTime - self.prevTime)) if self.prevTime else 0

        self.prevTime = currentTime

        cv2.putText(frame, f"FPS: {fps}", (15, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(frame, "Press 'q' to quit", (15, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        return frame


def main():

    faceFolder = "faces"
    serverUrl = "http://localhost:3000/api/sighting"

    tracker = FullStackFaceTracker(faceFolder, serverUrl)

    video = cv2.VideoCapture(0)

    while video.isOpened():

        success, frame = video.read()

        if not success:
            break

        frame = tracker.processFrame(frame)

        cv2.imshow("AI Biometric Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()