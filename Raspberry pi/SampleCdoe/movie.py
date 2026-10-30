import cv2

# Replace with your ESP32-CAM IP address
rtsp_url = "http://192.168.5.171/stream" # For MJPEG
# rtsp_url = 'rtsp://192.168.1.100:8554/stream' # For RTSP

cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Error: Could not open stream.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Process frame here
        cv2.imshow('ESP32-CAM Stream', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
