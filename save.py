import cv2
import numpy as np
from ultralytics import YOLO

# Object classes for chess pieces
classNames = ["B", "K", "N", "P", "Q", "R", "b", "k", "n", "p", "q", "r"]

# Load the YOLOv8 model
model = YOLO("runs/detect/train6/weights/best.pt")


def detect_chess_pieces(frame):
    results = model(frame, stream=True)
    piece_positions = {}  # Dictionary to store piece positions

    for r in results:
        boxes = r.boxes

        for box in boxes:
            # Bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Calculate the center coordinates of the bounding box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Draw bounding box on the original frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Class name
            cls = int(box.cls[0])
            piece_name = classNames[cls]

            # Object details
            org = (x1, y1 - 5)
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 0.7
            color = (255, 0, 0)
            thickness = 2

            # Draw the piece name on the original frame
            cv2.putText(frame, piece_name, org, font, fontScale, color, thickness)

            # Store the piece position
            square_position = chr(ord('a') + (center_x // 75)) + str(8 - (center_y // 75))  # Approximation
            piece_positions[square_position] = piece_name

    return frame, piece_positions


def detect_chess_board(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Canny edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Use morphology to remove noise and fill gaps
    kernel = np.ones((5, 5), np.uint8)
    morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find contours in the morphed image
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize variables for chess board dimensions
    board_contour = None
    board_area = 0

    # Loop through the contours to find the largest quadrilateral (the chess board)
    for cnt in contours:
        # Approximate the contour to a polygon
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)

        # Check if the approximated contour has 4 vertices (quadrilateral)
        if len(approx) == 4:
            # Calculate the area of the contour
            area = cv2.contourArea(cnt)

            # Update the board contour and area if the current contour is larger
            if area > board_area:
                board_contour = approx
                board_area = area

    return board_contour


# Load the video
cap = cv2.VideoCapture("Video/16.mp4")

# Get the original video dimensions and define the codec
new_width = 600
new_height = 600
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('Video/output_video.mp4', fourcc, 30.0, (new_width, new_height))

while True:
    ret, frame = cap.read()

    if not ret:
        break
    frame = cv2.resize(frame, (new_width, new_height))

    # Detect the chessboard in the current frame
    board_contour = detect_chess_board(frame)

    if board_contour is not None:
        # Draw the detected chessboard contour on the frame
        cv2.drawContours(frame, [board_contour], -1, (0, 255, 0), 3)

    # Detect chess pieces on the current frame
    frame, piece_positions = detect_chess_pieces(frame)

    # Write the frame to the output video
    out.write(frame)

    # Display the frame
    cv2.imshow('Chess Pieces and Board Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
