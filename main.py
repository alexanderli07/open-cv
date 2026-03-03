import cv2
import face_recognition
import requests
import time
import threading

class FullStackFaceTracker:
    def __init__(self, known_image_path, person_name, server_url):
        """Initialize the recognition model and server details."""
        print(f"Loading biometric data for {person_name}...")
        
        # Load your reference image and extract the facial map (encoding)
        known_image = face_recognition.load_image_file(known_image_path)
        self.known_encoding = face_recognition.face_encodings(known_image)[0]
        self.known_name = person_name
        
        # Server config
        self.server_url = server_url
        self.last_sighting_time = 0
        self.cooldown = 5.0  # Only ping the server once every 5 seconds per person
        self.prev_time = 0

    def send_sighting_to_server(self, name):
        """Sends the HTTP request in the background to avoid freezing the video."""
        try:
            requests.post(self.server_url, json={"name": name}, timeout=2)
            print(f"[{time.strftime('%X')}] Successfully logged sighting of {name}")
        except requests.exceptions.RequestException as e:
            print(f"Server connection failed: {e}")

    def process_frame(self, frame):
        """Processes a frame for recognition, HUD drawing, and server pinging."""
        # Shrink the frame to 1/4 size for much faster AI processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all faces and encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale the bounding box back up since we shrunk the image for the AI
            top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
            
            # See if the face matches our known encoding
            matches = face_recognition.compare_faces([self.known_encoding], face_encoding, tolerance=0.6)
            name = "Unknown Subject"
            color = (0, 0, 255) # Red for unknown

            if True in matches:
                name = self.known_name
                color = (0, 255, 255) # Yellow/Cyan for known target
                
                # Check if enough time has passed to ping the server again
                current_time = time.time()
                if current_time - self.last_sighting_time > self.cooldown:
                    self.last_sighting_time = current_time
                    # Run the web request in a separate thread so the camera doesn't lag!
                    threading.Thread(target=self.send_sighting_to_server, args=(name,)).start()

            # Draw the sci-fi HUD brackets
            self._draw_hud(frame, left, top, right - left, bottom - top, color)
            
            # Label the face
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Calculate and render FPS
        curr_time = time.time()
        fps = int(1 / (curr_time - self.prev_time)) if self.prev_time else 0
        self.prev_time = curr_time

        cv2.putText(frame, f"FPS: {fps}", (15, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (15, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame

    def _draw_hud(self, img, x, y, w, h, color):
        """Draws sci-fi style corner brackets."""
        thickness = 3
        length = 25

        # Top Left corner
        cv2.line(img, (x, y), (x + length, y), color, thickness)
        cv2.line(img, (x, y), (x, y + length), color, thickness)
        # Top Right corner
        cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
        # Bottom Left corner
        cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
        # Bottom Right corner
        cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)

def main():
    # SETUP: Put a picture of yourself in the same folder as this script
    # and change 'my_face.jpg' and 'Your Name' below.
    IMAGE_FILENAME = "my_face.jpg"
    YOUR_NAME = "Your Name"
    NODE_SERVER = "http://localhost:3000/api/sighting"

    tracker = FullStackFaceTracker(IMAGE_FILENAME, YOUR_NAME, NODE_SERVER)
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        processed_frame = tracker.process_frame(frame)
        cv2.imshow("AI Biometric Scanner", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()