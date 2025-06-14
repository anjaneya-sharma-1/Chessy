import cv2
import numpy as np
from integrated_backend_server import IntegratedChessVisionModel
import requests
import json
from PIL import Image
import io

def test_model_locally():
    """Test the integrated model locally without API"""
    print("Testing integrated chess vision model locally...")
    
    # Initialize model
    model = IntegratedChessVisionModel()
    
    if model.model is None:
        print("❌ Model not loaded. Please check the model path.")
        return
    
    print("✅ Model loaded successfully")
    
    # Create a test image (you can replace this with an actual chess board image)
    test_image = np.ones((600, 600, 3), dtype=np.uint8) * 255  # White image
    
    # Process the test image
    result = model.process_image(test_image)
    
    print(f"Processing result: {json.dumps(result, indent=2)}")
    
    if result['success']:
        print("✅ Image processing successful")
        print(f"FEN: {result['fen']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Pieces detected: {result['piecesDetected']}")
    else:
        print("❌ Image processing failed")
        print(f"Error: {result.get('error', 'Unknown error')}")

def test_with_real_image(image_path):
    """Test with a real chess board image"""
    print(f"Testing with real image: {image_path}")
    
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image from {image_path}")
            return
        
        # Initialize model
        model = IntegratedChessVisionModel()
        
        if model.model is None:
            print("❌ Model not loaded")
            return
        
        # Process image
        result = model.process_image(image)
        
        print("Processing result:")
        print(json.dumps(result, indent=2))
        
        if result['success']:
            print("✅ Real image processing successful")
            print(f"FEN: {result['fen']}")
            print(f"Board detected: {result['boardDetected']}")
            print(f"Pieces detected: {result['piecesDetected']}")
            
            # Display piece positions
            if 'piecePositions' in result:
                print("\nDetected pieces:")
                for position, data in result['piecePositions'].items():
                    piece = data['piece'] if isinstance(data, dict) else data
                    confidence = data['confidence'] if isinstance(data, dict) else 'N/A'
                    print(f"  {position}: {piece} (confidence: {confidence})")
        else:
            print("❌ Real image processing failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing with real image: {e}")

def test_api_with_image(image_path, api_url="http://localhost:8000"):
    """Test the API with a real image"""
    print(f"Testing API with image: {image_path}")
    
    try:
        # Load and prepare image
        with open(image_path, 'rb') as f:
            files = {'image': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(f"{api_url}/api/detect-chess-position", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API test successful")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ API test failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"❌ API test error: {e}")

if __name__ == "__main__":
    print("Integrated Chess Vision Model Test Suite")
    print("=" * 50)
    
    # Test 1: Local model test
    test_model_locally()
    
    print("\n" + "=" * 50)
    
    # Test 2: Test with real image (uncomment and provide path)
    # test_with_real_image("path/to/your/chess_board_image.jpg")
    
    # Test 3: Test API (uncomment and provide image path)
    # test_api_with_image("path/to/your/chess_board_image.jpg")
    
    print("\nTest completed!")
