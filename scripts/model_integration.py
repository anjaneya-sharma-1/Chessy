"""
Integration script for chess piece detection model using YOLO
"""

import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import cv2
from typing import List, Dict, Tuple
from ultralytics import YOLO
import os

class ChessVisionModel:
    def __init__(self, model_path: str = "best.pt"):
        """Initialize the chess vision model"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load YOLO model
        try:
            self.model = YOLO(model_path)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
        
        # Class names for chess pieces
        self.class_names = [
            'white_king', 'white_queen', 'white_rook', 'white_bishop', 'white_knight', 'white_pawn',
            'black_king', 'black_queen', 'black_rook', 'black_bishop', 'black_knight', 'black_pawn'
        ]
    
    def detect_pieces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect chess pieces in the image using YOLO model
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detected pieces with format:
            [
                {
                    'piece': 'white_king',
                    'row': 7,
                    'col': 4,
                    'confidence': 0.95,
                    'bbox': [x1, y1, x2, y2]
                },
                ...
            ]
        """
        if self.model is None:
            print("Model not loaded, returning empty list")
            return []
        
        try:
            # Run YOLO inference
            results = self.model(image)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box coordinates and class
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        if confidence > 0.5:  # Confidence threshold
                            # Convert pixel coordinates to board coordinates
                            row, col = self._pixel_to_board_coords(
                                (x1 + x2) / 2, (y1 + y2) / 2, image.shape
                            )
                            
                            detections.append({
                                'piece': self.class_names[class_id],
                                'row': row,
                                'col': col,
                                'confidence': float(confidence),
                                'bbox': [float(x1), float(y1), float(x2), float(y2)]
                            })
            
            return detections
            
        except Exception as e:
            print(f"Error during inference: {e}")
            return []
    
    def _pixel_to_board_coords(self, x: float, y: float, image_shape: Tuple[int, int, int]) -> Tuple[int, int]:
        """Convert pixel coordinates to board square coordinates"""
        h, w = image_shape[:2]
        
        # Assuming the board fills the entire image
        col = int(x / w * 8)
        row = int(y / h * 8)
        
        # Clamp to valid range
        row = max(0, min(7, row))
        col = max(0, min(7, col))
        
        return row, col

if __name__ == "__main__":
    # Test the model
    model = ChessVisionModel()
    print("Model initialized successfully")
