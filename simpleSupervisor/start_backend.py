#!/usr/bin/env python3
"""
Startup script for the Simple Supervisor FastAPI backend
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import langgraph
        import langchain
        import streamlit
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has Ollama configuration"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Please create a .env file with your Ollama configuration:")
        print("OLLAMA_BASE_URL=http://localhost:11434")
        print("OLLAMA_MODEL=llama3.2")
        return False
    
    # Check if Ollama configuration is set
    from dotenv import load_dotenv
    load_dotenv()
    
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    print(f"✅ Environment configuration found")
    print(f"🔗 Ollama URL: {ollama_base_url}")
    print(f"🤖 Model: {ollama_model}")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Simple Supervisor Backend...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        print("\nTo create a .env file, copy env.example and configure Ollama:")
        print("cp env.example .env")
        print("Then edit .env and configure your Ollama settings")
        sys.exit(1)
    
    print("\n🎯 Starting FastAPI server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Change to backend directory and run the server
        backend_dir = Path("backend")
        if backend_dir.exists():
            os.chdir(backend_dir)
        
        # Run the FastAPI server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 