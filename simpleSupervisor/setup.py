#!/usr/bin/env python3
"""
Setup script for Simple Supervisor AI Agent System
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print the setup banner"""
    print("=" * 60)
    print("🤖 Simple Supervisor AI Agent System Setup")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        from langgraph.graph import StateGraph, END
        from langchain_ollama import OllamaLLM
        import streamlit
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        print("\n📝 Creating .env file from template...")
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ .env file created")
            print("⚠️  Please ensure Ollama is running with llama3.2 model")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ env.example file not found")
        return False

def verify_structure():
    """Verify the project structure"""
    print("\n📁 Verifying project structure...")
    
    required_files = [
        "requirements.txt",
        "README.md",
        "backend/main.py",
        "backend/agents/supervisor.py",
        "backend/agents/math_agent.py",
        "backend/agents/blog_agent.py",
        "backend/models/schemas.py",
        "frontend/app.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ Project structure verified")
    return True

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Verify project structure
    if not verify_structure():
        print("\n❌ Project structure is incomplete")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Ensure Ollama is running with llama3.2 model")
    print("2. Start the backend server: python start_backend.py")
    print("3. Start the frontend: python start_frontend.py")
    print("4. Open http://localhost:8501 in your browser")
    print("\n💡 Example queries:")
    print("   - Math: 'What is 15 + 23?'")
    print("   - Blog: 'Write a blog about artificial intelligence'")
    print("\n🔗 API Documentation: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    main() 