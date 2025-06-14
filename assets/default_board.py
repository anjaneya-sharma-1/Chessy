import numpy as np
import cv2

def create_default_board():
    # Create a blank 800x800 image
    board = np.zeros((800, 800, 3), dtype=np.uint8)
    
    # Define colors
    white = (255, 255, 255)
    black = (128, 128, 128)
    
    # Square size
    square_size = 100
    
    # Draw squares
    for i in range(8):
        for j in range(8):
            x1 = j * square_size
            y1 = i * square_size
            x2 = x1 + square_size
            y2 = y1 + square_size
            
            color = white if (i + j) % 2 == 0 else black
            cv2.rectangle(board, (x1, y1), (x2, y2), color, -1)
    
    # Add coordinates
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    
    # Add file coordinates (a-h)
    for i in range(8):
        x = i * square_size + 5
        y = 790
        cv2.putText(board, chr(ord('a') + i), (x, y), font, font_scale, (0, 0, 0), thickness)
    
    # Add rank coordinates (1-8)
    for i in range(8):
        x = 5
        y = (7-i) * square_size + 20
        cv2.putText(board, str(i + 1), (x, y), font, font_scale, (0, 0, 0), thickness)
    
    # Save the image
    cv2.imwrite('assets/default_board.png', board)

if __name__ == '__main__':
    create_default_board()
