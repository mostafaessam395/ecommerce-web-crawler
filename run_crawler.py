import os
import subprocess
import sys
import argparse

def main():
    """
    Main entry point for running the crawler
    """
    parser = argparse.ArgumentParser(description="Run the web crawler with different options")
    parser.add_argument("--mode", choices=["standard", "ecommerce"], default="standard",
                       help="Crawler mode: 'standard' for general websites, 'ecommerce' for e-commerce specific crawler")
    parser.add_argument("--install", action="store_true",
                       help="Install dependencies before running")

    args = parser.parse_args()

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Install dependencies if requested
    if args.install:
        print(f"Installing dependencies for {args.mode} crawler...")

        if args.mode == "ecommerce":
            # Install E-commerce crawler dependencies
            install_script = os.path.join(current_dir, "install_ecommerce_crawler.py")
            if os.path.exists(install_script):
                subprocess.check_call([sys.executable, install_script])
            else:
                print(f"Error: Installation script not found at {install_script}")
                return
        else:
            # Install standard crawler dependencies
            install_script = os.path.join(current_dir, "install_dependencies.py")
            if os.path.exists(install_script):
                subprocess.check_call([sys.executable, install_script])
            else:
                print(f"Error: Installation script not found at {install_script}")
                return

    # Run the selected crawler
    if args.mode == "ecommerce":
        # Run E-commerce crawler
        print("Starting Enhanced E-commerce crawler...")

        # Try to use the enhanced dashboard first, fall back to the standard one if not found
        enhanced_dashboard_path = os.path.join(current_dir, "web_analyzer_dashboard.py")
        standard_dashboard_path = os.path.join(current_dir, "product_crawler_dashboard.py")

        if os.path.exists(enhanced_dashboard_path):
            dashboard_path = enhanced_dashboard_path
            print("Using enhanced E-commerce dashboard")
        elif os.path.exists(standard_dashboard_path):
            dashboard_path = standard_dashboard_path
            print("Using standard E-commerce dashboard")
        else:
            print(f"Error: E-commerce dashboard not found at {enhanced_dashboard_path} or {standard_dashboard_path}")
            return

        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]
    else:
        # Run standard crawler
        print("Starting standard crawler...")
        dashboard_path = os.path.join(current_dir, "graph-streamlit.py")

        if not os.path.exists(dashboard_path):
            print(f"Error: Standard dashboard not found at {dashboard_path}")
            return

        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]

    print(f"Running command: {' '.join(cmd)}")

    try:
        # Run the dashboard
        process = subprocess.Popen(cmd)

        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        print("Crawler stopped by user.")
    except Exception as e:
        print(f"Error running crawler: {str(e)}")

if __name__ == "__main__":
    main()
