import os
import shutil
from pathlib import Path

def setup_model_directory():
    """Set up the model directory structure"""
    print("Setting up model directory structure...")
    
    # Create necessary directories
    directories = [
        "runs/detect/train4/weights",
        "models",
        "test_images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check if model file exists
    model_path = "runs/detect/train4/weights/best.pt"
    if os.path.exists(model_path):
        print(f"✅ Model file found at: {model_path}")
    else:
        print(f"❌ Model file not found at: {model_path}")
        print("Please copy your trained model file to this location")
    
    # Create environment file template
    env_content = """# Chess Vision Model Configuration
CHESS_MODEL_PATH=runs/detect/train4/weights/best.pt
STOCKFISH_PATH=/usr/local/bin/stockfish
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with default configuration")
    
    print("\nSetup completed!")
    print("\nNext steps:")
    print("1. Copy your trained model (best.pt) to: runs/detect/train4/weights/")
    print("2. Install Stockfish: python scripts/install_stockfish.py")
    print("3. Start the server: python scripts/integrated_backend_server.py")

if __name__ == "__main__":
    setup_model_directory()
