import os
import platform
import subprocess
import urllib.request
import zipfile
import tarfile

def install_stockfish():
    """Install Stockfish chess engine"""
    system = platform.system().lower()
    
    if system == "linux":
        install_stockfish_linux()
    elif system == "darwin":  # macOS
        install_stockfish_macos()
    elif system == "windows":
        install_stockfish_windows()
    else:
        print(f"Unsupported system: {system}")

def install_stockfish_linux():
    """Install Stockfish on Linux"""
    try:
        # Try package manager first
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "stockfish"], check=True)
        print("Stockfish installed successfully via apt-get")
    except subprocess.CalledProcessError:
        try:
            # Try snap
            subprocess.run(["sudo", "snap", "install", "stockfish"], check=True)
            print("Stockfish installed successfully via snap")
        except subprocess.CalledProcessError:
            print("Failed to install Stockfish via package manager")
            install_stockfish_from_source()

def install_stockfish_macos():
    """Install Stockfish on macOS"""
    try:
        # Try Homebrew
        subprocess.run(["brew", "install", "stockfish"], check=True)
        print("Stockfish installed successfully via Homebrew")
    except subprocess.CalledProcessError:
        print("Failed to install Stockfish via Homebrew")
        print("Please install Homebrew first: https://brew.sh/")

def install_stockfish_windows():
    """Install Stockfish on Windows"""
    print("Downloading Stockfish for Windows...")
    
    # Create engines directory
    engines_dir = "engines"
    os.makedirs(engines_dir, exist_ok=True)
    
    # Download Stockfish
    url = "https://stockfishchess.org/files/stockfish_15_win_x64_avx2.zip"
    zip_path = os.path.join(engines_dir, "stockfish.zip")
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(engines_dir)
        
        # Clean up
        os.remove(zip_path)
        
        print("Stockfish downloaded and extracted to engines/ directory")
        print("Update your engine path in the backend to point to the extracted executable")
        
    except Exception as e:
        print(f"Failed to download Stockfish: {e}")

def install_stockfish_from_source():
    """Install Stockfish from source (Linux fallback)"""
    print("Installing Stockfish from source...")
    
    try:
        # Clone repository
        subprocess.run(["git", "clone", "https://github.com/official-stockfish/Stockfish.git"], check=True)
        
        # Build
        os.chdir("Stockfish/src")
        subprocess.run(["make", "build", "ARCH=x86-64"], check=True)
        
        # Copy to system path
        subprocess.run(["sudo", "cp", "stockfish", "/usr/local/bin/"], check=True)
        
        print("Stockfish built and installed successfully")
        
    except Exception as e:
        print(f"Failed to build Stockfish from source: {e}")

if __name__ == "__main__":
    install_stockfish()
