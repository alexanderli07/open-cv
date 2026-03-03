import cv2
import mediapipe as mp
import time

class AdvancedFaceTracker:
    def __init__(self, blur_faces=False):
        """Initialize the deep learning face detection model."""
        self.mp_face_detection = mp.solutions.face_detection
        
        # model_selection=0 is optimized for short-range (webcam) 
        # min_detection_confidence filters out false positives
        self.detector = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.7
        )
        self.blur_faces = blur_faces
        self.prev_time = 0

    def process_frame(self, frame):
        """Processes a single frame for detection, HUD drawing, and manipulation."""
        # OpenCV captures in BGR, but MediaPipe requires RGB color space
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb_frame)

        h, w, _ = frame.shape

        if results.detections:
            for detection in results.detections:
                # Extract normalized bounding box coordinates and scale them to frame size
                bboxC = detection.location_data.relative_bounding_box
                x = int(bboxC.xmin * w)
                y = int(bboxC.ymin * h)
                bw = int(bboxC.width * w)
                bh = int(bboxC.height * h)

                # Clamp coordinates to ensure we don't try to draw outside the frame bounds
                x, y = max(0, x), max(0, y)
                bw, bh = min(w - x, bw), min(h - y, bh)

                if self.blur_faces:
                    # ROI Manipulation: Extract the face region and pixelate it
                    roi = frame[y:y+bh, x:x+bw]
                    if roi.shape[0] > 0 and roi.shape[1] > 0:
                        # Shrink the face drastically, then blow it back up without smoothing (INTER_NEAREST)
                        small = cv2.resize(roi, (12, 12), interpolation=cv2.INTER_LINEAR)
                        pixelated = cv2.resize(small, (bw, bh), interpolation=cv2.INTER_NEAREST)
                        frame[y:y+bh, x:x+bw] = pixelated
                else:
                    # Draw a custom HUD instead of a standard rectangle
                    self._draw_hud(frame, x, y, bw, bh)

        # Calculate and render Frames Per Second (FPS)
        curr_time = time.time()
        fps = int(1 / (curr_time - self.prev_time)) if self.prev_time else 0
        self.prev_time = curr_time

        cv2.putText(frame, f"FPS: {fps}", (15, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
        
        # Display instructions
        cv2.putText(frame, "Press 'b' to toggle blur | 'q' to quit", (15, h - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame

    def _draw_hud(self, img, x, y, w, h):
        """Draws sci-fi style corner brackets instead of a full square."""
        color = (0, 255, 255)  # Cyan/Yellow
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
    cap = cv2.VideoCapture(0)
    
    # Instantiate our tracker
    tracker = AdvancedFaceTracker(blur_faces=False)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to grab frame from camera. Exiting...")
            break

        # Pass the frame through our custom class
        processed_frame = tracker.process_frame(frame)

        cv2.imshow("Advanced Vision System", processed_frame)

        # Keyboard listeners
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('b'):
            # Dynamically toggle the pixelation effect
            tracker.blur_faces = not tracker.blur_faces

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()