"""Run IVIE with Streamlit interface.

Simple script to launch the Streamlit version of IVIE.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit application."""
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Run streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true"]
    
    print("🚀 Starting IVIE with Streamlit interface...")
    print("🌐 The app will open in your default browser")
    print("📌 Press Ctrl+C to stop the application")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 IVIE application stopped")

if __name__ == "__main__":
    main()
