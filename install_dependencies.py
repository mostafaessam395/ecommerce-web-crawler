import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies for the web crawler"""
    print("Installing dependencies...")
    
    # Install Python packages from requirements.txt
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Install Playwright browsers
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("Playwright browsers installed successfully.")
    except Exception as e:
        print(f"Error installing Playwright browsers: {str(e)}")
        print("You may need to install them manually with: python -m playwright install chromium")
    
    print("Dependencies installed successfully.")

if __name__ == "__main__":
    install_dependencies()
