#!/usr/bin/env python3
"""
Test script for Simple Supervisor AI Agent System
"""

import os
import sys
import requests
import time
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        import uvicorn
        import langgraph
        import langchain
        import streamlit
        import requests
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_env_config():
    """Test environment configuration"""
    print("\n🔍 Testing environment configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    print(f"🔗 Ollama URL: {ollama_base_url}")
    print(f"🤖 Model: {ollama_model}")
    
    # Test Ollama connection
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is accessible")
            return True
        else:
            print("❌ Ollama server not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("💡 Please ensure Ollama is running and the model is available")
        return False

def test_backend_api():
    """Test backend API endpoints"""
    print("\n🔍 Testing backend API...")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API")
        print("💡 Make sure the backend server is running: python start_backend.py")
        return False
    
    # Test agents endpoint
    try:
        response = requests.get(f"{base_url}/agents", timeout=5)
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Agents endpoint working - Found {len(agents['agents'])} agents")
        else:
            print(f"❌ Agents endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing agents endpoint: {e}")
        return False
    
    return True

def test_query_processing():
    """Test query processing with sample queries"""
    print("\n🔍 Testing query processing...")
    
    base_url = "http://localhost:8000"
    test_queries = [
        {
            "query": "What is 15 + 23?",
            "expected_agent": "math"
        },
        {
            "query": "Write a blog about artificial intelligence",
            "expected_agent": "blog"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n  Testing query {i}: {test_case['query']}")
        
        try:
            response = requests.post(
                f"{base_url}/query",
                json={"query": test_case["query"]},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result["success"]:
                    print(f"    ✅ Query processed successfully")
                    print(f"    🎯 Selected agent: {result['selected_agent']}")
                    print(f"    📝 Result length: {len(result['final_result'])} characters")
                    
                    if result["selected_agent"] == test_case["expected_agent"]:
                        print(f"    ✅ Correct agent selected")
                    else:
                        print(f"    ⚠️  Expected {test_case['expected_agent']}, got {result['selected_agent']}")
                else:
                    print(f"    ❌ Query processing failed: {result.get('error_message', 'Unknown error')}")
                    return False
            else:
                print(f"    ❌ API returned {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error testing query: {e}")
            return False
    
    print("\n✅ All query tests passed")
    return True

def main():
    """Main test function"""
    print("🧪 Simple Supervisor System Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed")
        sys.exit(1)
    
    # Test environment
    if not test_env_config():
        print("\n❌ Environment test failed")
        print("Please ensure Ollama is running with the llama3.2 model")
        sys.exit(1)
    
    # Test backend API
    if not test_backend_api():
        print("\n❌ Backend API test failed")
        print("Please start the backend server first: python start_backend.py")
        sys.exit(1)
    
    # Test query processing
    if not test_query_processing():
        print("\n❌ Query processing test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! System is working correctly.")
    print("=" * 50)
    print("\n💡 You can now:")
    print("1. Open http://localhost:8501 for the web interface")
    print("2. Use the API directly at http://localhost:8000/docs")
    print("3. Try different queries to test the system")

if __name__ == "__main__":
    main() 