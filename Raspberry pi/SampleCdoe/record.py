import cv2

# 1. Open the default camera
cap = cv2.VideoCapture("http://192.168.5.171/stream")

# 2. Define codec and create VideoWriter object
# FourCC code: 'XVID' for AVI, 'mp4v' for MP4 (check availability per OS)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

# Optional: Get actual camera dimensions
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter('output.avi', fourcc, 5, (frame_width, frame_height))

while True:
    # 3. Read a frame
    ret, frame = cap.read()
    
    if ret:
        # Write the frame to the output file
        out.write(frame)
        
        # Display the frame
        cv2.imshow('Recording', frame)
        
        # Break on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# 4. Release resources
cap.release()
out.release()
cv2.destroyAllWindows()
