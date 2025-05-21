import subprocess
import sys
import platform

def install_dependencies():
    """Install required dependencies for the E-commerce crawler"""
    print("Installing dependencies for E-commerce crawler...")

    # Required packages
    packages = [
        "streamlit",
        "pandas",
        "networkx",
        "matplotlib",
        "plotly",
        "playwright",
        "tenacity",
        "beautifulsoup4",
        "langdetect",
        "pycountry",
        "scipy",
        "requests"
    ]

    # Install Python packages
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except Exception as e:
            print(f"Error installing {package}: {str(e)}")

    # Install Playwright browsers
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("Playwright browsers installed successfully.")
    except Exception as e:
        print(f"Error installing Playwright browsers: {str(e)}")
        print("You may need to install them manually with: python -m playwright install chromium")

    print("\nDependencies installed successfully.")
    print("\nYou can now run the E-commerce crawler with:")
    print("python start_crawler.py --mode ecommerce")

if __name__ == "__main__":
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")

    # Check operating system
    os_name = platform.system()
    print(f"Operating system: {os_name}")

    # Install dependencies
    install_dependencies()
