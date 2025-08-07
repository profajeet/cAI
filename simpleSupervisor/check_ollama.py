#!/usr/bin/env python3
"""
Ollama setup verification script for Simple Supervisor AI Agent System
"""

import os
import sys
import requests
import json
from pathlib import Path

def check_ollama_installation():
    """Check if Ollama is installed and accessible"""
    print("🔍 Checking Ollama installation...")
    
    try:
        # Try to connect to Ollama server
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            return True
        else:
            print(f"❌ Ollama server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama server")
        print("💡 Please ensure Ollama is running:")
        print("   ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False

def check_model_availability():
    """Check if the required model is available"""
    print("\n🔍 Checking model availability...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            
            # Look for llama3.2 model
            llama32_found = False
            for model in models:
                if "llama3.2" in model.get("name", ""):
                    llama32_found = True
                    print(f"✅ Found model: {model['name']}")
                    print(f"   Size: {model.get('size', 'Unknown')} bytes")
                    print(f"   Modified: {model.get('modified_at', 'Unknown')}")
                    break
            
            if not llama32_found:
                print("❌ llama3.2 model not found")
                print("💡 To install the model, run:")
                print("   ollama pull llama3.2")
                return False
            
            return True
        else:
            print(f"❌ Failed to get model list: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def test_model_inference():
    """Test basic model inference"""
    print("\n🔍 Testing model inference...")
    
    try:
        # Simple test prompt
        test_data = {
            "model": "llama3.2",
            "prompt": "What is 2 + 2?",
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "response" in result:
                print("✅ Model inference test successful")
                print(f"   Response: {result['response'][:100]}...")
                return True
            else:
                print("❌ No response in model output")
                return False
        else:
            print(f"❌ Model inference failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing model inference: {e}")
        return False

def check_environment_config():
    """Check environment configuration"""
    print("\n🔍 Checking environment configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    print(f"🔗 Ollama URL: {ollama_base_url}")
    print(f"🤖 Model: {ollama_model}")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found (using defaults)")
    
    return True

def main():
    """Main verification function"""
    print("🧪 Ollama Setup Verification")
    print("=" * 50)
    
    # Check environment
    check_environment_config()
    
    # Check Ollama installation
    if not check_ollama_installation():
        print("\n❌ Ollama installation check failed")
        print("\n📋 Installation steps:")
        print("1. Download Ollama from: https://ollama.ai/download")
        print("2. Install and start Ollama")
        print("3. Run: ollama serve")
        sys.exit(1)
    
    # Check model availability
    if not check_model_availability():
        print("\n❌ Model availability check failed")
        print("\n📋 Model installation steps:")
        print("1. Ensure Ollama is running: ollama serve")
        print("2. Pull the model: ollama pull llama3.2")
        print("3. Wait for download to complete")
        sys.exit(1)
    
    # Test model inference
    if not test_model_inference():
        print("\n❌ Model inference test failed")
        print("💡 The model might be corrupted or not properly loaded")
        print("💡 Try: ollama pull llama3.2 --force")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Ollama setup is complete and working!")
    print("=" * 50)
    print("\n💡 You can now:")
    print("1. Start the backend: python start_backend.py")
    print("2. Start the frontend: python start_frontend.py")
    print("3. Test the system: python test_system.py")

if __name__ == "__main__":
    main() 