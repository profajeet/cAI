#!/usr/bin/env python3
"""
Startup script for the Simple Supervisor Streamlit frontend
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import requests
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_backend_connection():
    """Check if the backend API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
            return True
        else:
            print("❌ Backend API returned error status")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API")
        print("Please start the backend server first:")
        print("python start_backend.py")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Simple Supervisor Frontend...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check backend connection
    print("🔍 Checking backend connection...")
    if not check_backend_connection():
        print("\n💡 To start the backend server:")
        print("1. Open a new terminal")
        print("2. Run: python start_backend.py")
        print("3. Wait for the backend to start")
        print("4. Then run this frontend script again")
        sys.exit(1)
    
    print("\n🎯 Starting Streamlit frontend...")
    print("🌐 Frontend will be available at: http://localhost:8501")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 