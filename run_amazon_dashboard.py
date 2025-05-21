import os
import subprocess
import sys

def main():
    """
    Run the Amazon dashboard
    """
    print("Starting Amazon Dashboard...")

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if required packages are installed
    try:
        import streamlit
        import pandas
        import plotly
        import networkx
        import playwright
        import tenacity
        import graphistry
        import streamlit_echarts
        import streamlit_apexjs
    except ImportError as e:
        print(f"Missing required package: {str(e)}")
        print("Installing required packages...")

        # Install required packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly", "tenacity", "graphistry>=0.28.0", "streamlit-echarts>=0.4.0", "streamlit-apexjs>=0.0.3"])

        # Install Playwright browsers
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            print("Playwright browsers installed successfully.")
        except Exception as e:
            print(f"Error installing Playwright browsers: {str(e)}")
            print("You may need to install them manually with: python -m playwright install chromium")

    # Run the dashboard
    dashboard_path = os.path.join(current_dir, "amazon_dashboard.py")

    # Check if the dashboard file exists
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard file not found at {dashboard_path}")
        return

    # Run the dashboard
    cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]

    print(f"Running command: {' '.join(cmd)}")

    try:
        # Run the dashboard
        process = subprocess.Popen(cmd)

        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        print("Dashboard stopped by user.")
    except Exception as e:
        print(f"Error running dashboard: {str(e)}")

if __name__ == "__main__":
    main()
