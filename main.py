import cv2

# Load the pre-trained face classifier
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Start video capture
video_capture = cv2.VideoCapture(0)

def detect_bounding_box(vid):
    # Convert the frame to grayscale for face detection
    gray_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    
    # Detect faces in the frame
    faces = face_classifier.detectMultiScale(
        gray_image,
        scaleFactor=1.1,  # Adjust this value to 1.05 for more accurate detections at the cost of speed
        minNeighbors=5,   # Reduce this to 3 or 4 to detect more faces (but may increase false positives)
        minSize=(30, 30)  # Adjust this value to detect smaller faces
    )

    
    # Draw green squares around detected faces
    for (x, y, w, h) in faces:
        # Determine the side length of the square as the larger dimension
        side_length = max(w, h)
        
        # Draw a green square
        cv2.rectangle(vid, (x, y), (x + side_length, y + side_length), (0, 255, 0), 2)
    
    return faces

while True:
    # Read frames from the video
    result, video_frame = video_capture.read()
    if result is False:
        break  # Terminate the loop if the frame is not read successfully

    # Apply the face detection function to the video frame
    faces = detect_bounding_box(video_frame)

    # Display the processed frame in a window
    cv2.imshow("open-cv", video_frame)

    # Exit the loop when 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the video capture object and close all OpenCV windows
video_capture.release()
cv2.destroyAllWindows()
