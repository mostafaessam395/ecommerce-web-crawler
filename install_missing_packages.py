import subprocess
import sys
import platform

def install_missing_packages():
    """Install missing packages required for the E-commerce crawler dashboard"""
    print("Installing missing packages for E-commerce crawler dashboard...")

    # Missing packages
    packages = [
        "graphistry>=0.28.0",
        "streamlit-echarts>=0.4.0",
        "streamlit-apexjs>=0.0.3"
    ]

    # Install Python packages
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except Exception as e:
            print(f"Error installing {package}: {str(e)}")

    print("\nMissing packages installed successfully.")
    print("\nYou can now run the E-commerce crawler dashboard with:")
    print("streamlit run web_analyzer_dashboard.py")

if __name__ == "__main__":
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")

    # Check operating system
    os_name = platform.system()
    print(f"Operating system: {os_name}")

    # Install missing packages
    install_missing_packages()
