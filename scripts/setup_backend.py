import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages"""
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "opencv-python==4.8.1.78",
        "numpy==1.24.3",
        "pillow==10.0.1",
        "python-chess==1.999",
        "torch==2.1.0",
        "torchvision==0.16.0",
        "ultralytics==8.0.196",
        "requests==2.31.0",
        "python-dotenv==1.0.0"
    ]
    
    for package in requirements:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("All packages installed successfully!")

if __name__ == "__main__":
    install_requirements()
