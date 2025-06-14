import requests
import json
from PIL import Image
import io
import base64

def test_backend_api():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Chess Vision Backend API...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Health check failed")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure the server is running.")
        return
    
    # Test engine info
    try:
        response = requests.get(f"{base_url}/api/engine-info")
        if response.status_code == 200:
            print("✅ Engine info endpoint working")
            info = response.json()
            print(f"   Engine available: {info['engineAvailable']}")
            print(f"   Model loaded: {info['modelLoaded']}")
        else:
            print("❌ Engine info endpoint failed")
    except Exception as e:
        print(f"❌ Engine info test failed: {e}")
    
    # Test position analysis
    try:
        test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        response = requests.post(
            f"{base_url}/api/analyze-position",
            json={"fen": test_fen}
        )
        if response.status_code == 200:
            print("✅ Position analysis working")
            analysis = response.json()
            print(f"   Suggested move: {analysis.get('suggestedMove', 'None')}")
            print(f"   Material balance: {analysis.get('evaluation', {}).get('materialBalance', 'N/A')}")
        else:
            print("❌ Position analysis failed")
    except Exception as e:
        print(f"❌ Position analysis test failed: {e}")
    
    # Test image detection (create a test image)
    try:
        # Create a simple test image
        test_image = Image.new('RGB', (640, 640), color='white')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        files = {'image': ('test.jpg', img_buffer, 'image/jpeg')}
        response = requests.post(f"{base_url}/api/detect-chess-position", files=files)
        
        if response.status_code == 200:
            print("✅ Image detection endpoint working")
            result = response.json()
            print(f"   FEN detected: {result.get('fen', 'None')[:50]}...")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Pieces detected: {result.get('piecesDetected', 'N/A')}")
        else:
            print("❌ Image detection failed")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Image detection test failed: {e}")
    
    print("\nBackend API testing completed!")

if __name__ == "__main__":
    test_backend_api()
