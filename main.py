import cv2
import face_recognition
import requests
import time
import threading

class FullStackFaceTracker:
    def __init__(self, knownImagePath, personName, serverUrl):
        """Initialize the recognition model and server details."""
        print(f"Loading biometric data for {personName}...")
        
        # Load reference image and extract the facial map (encoding)
        knownImage = face_recognition.load_image_file(knownImagePath)
        self.knownEncoding = face_recognition.face_encodings(knownImage)[0]
        self.knownName = personName
        
        # Server config
        self.serverUrl = serverUrl
        self.lastSightingTime = 0
        self.cooldownPeriod = 5.0  # Seconds between server pings
        self.prevTime = 0

    def sendSightingToServer(self, name):
        """Sends the HTTP request in the background to avoid freezing the video."""
        try:
            requests.post(self.serverUrl, json={"name": name}, timeout=2)
            print(f"[{time.strftime('%X')}] Successfully logged sighting of {name}")
        except requests.exceptions.RequestException as e:
            print(f"Server connection failed: {e}")

    def processFrame(self, frame):
        """Processes a frame for recognition, HUD drawing, and server pinging."""
        # Shrink the frame to 1/4 size for much faster AI processing
        smallFrame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgbSmallFrame = cv2.cvtColor(smallFrame, cv2.COLOR_BGR2RGB)

        # Find all faces and encodings in the current frame
        faceLocations = face_recognition.face_locations(rgbSmallFrame)
        faceEncodings = face_recognition.face_encodings(rgbSmallFrame, faceLocations)

        for (top, right, bottom, left), faceEncoding in zip(faceLocations, faceEncodings):
            # Scale the bounding box back up (since we processed at 0.25x)
            top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
            
            # See if the face matches our known encoding
            matches = face_recognition.compare_faces([self.knownEncoding], faceEncoding, tolerance=0.6)
            name = "Unknown Subject"
            hudColor = (0, 0, 255) # Red for unknown

            if True in matches:
                name = self.knownName
                hudColor = (0, 255, 255) # Yellow/Cyan for known target
                
                # Check if enough time has passed to ping the server again
                currentTime = time.time()
                if currentTime - self.lastSightingTime > self.cooldownPeriod:
                    self.lastSightingTime = currentTime
                    # Fire-and-forget thread for the API call
                    threading.Thread(target=self.sendSightingToServer, args=(name,)).start()

            # Draw the sci-fi HUD brackets
            self.drawHud(frame, left, top, right - left, bottom - top, hudColor)
            
            # Label the face
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, hudColor, 2)

        # Calculate and render FPS
        currentTime = time.time()
        fps = int(1 / (currentTime - self.prevTime)) if self.prevTime else 0
        self.prevTime = currentTime

        cv2.putText(frame, f"FPS: {fps}", (15, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (15, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame

    def drawHud(self, img, x, y, w, h, color):
        """Draws sci-fi style corner brackets."""
        thickness = 3
        length = 25

        # Top Left
        cv2.line(img, (x, y), (x + length, y), color, thickness)
        cv2.line(img, (x, y), (x, y + length), color, thickness)
        # Top Right
        cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
        # Bottom Left
        cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
        # Bottom Right
        cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)

def main():
    # Configuration
    imageFilename = "my_face.jpg"
    userName = "Your Name"
    nodeServerUrl = "http://localhost:3000/api/sighting"

    tracker = FullStackFaceTracker(imageFilename, userName, nodeServerUrl)
    videoCapture = cv2.VideoCapture(0)

    while videoCapture.isOpened():
        success, currentFrame = videoCapture.read()
        if not success:
            break

        processedFrame = tracker.processFrame(currentFrame)
        cv2.imshow("AI Biometric Scanner", processedFrame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    videoCapture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()