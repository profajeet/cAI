#!/usr/bin/env python3
"""
Setup script for Agentic AI Orchestration.

This script helps users set up the system by:
1. Creating necessary directories
2. Setting up configuration files
3. Installing dependencies
4. Running initial tests
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def create_directories():
    """Create necessary directories."""
    directories = [
        "data",
        "data/sessions",
        "data/workflows",
        "logs",
        "config",
        "static"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_configuration():
    """Set up configuration files."""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Copy example configuration if it doesn't exist
    example_config = config_dir / "settings.example.yaml"
    target_config = config_dir / "settings.yaml"
    
    if not target_config.exists():
        if example_config.exists():
            shutil.copy(example_config, target_config)
            print("✅ Created config/settings.yaml from example")
        else:
            # Create a basic configuration
            basic_config = """# Agentic AI Orchestration - Basic Configuration
app_name: "Agentic AI Orchestration"
version: "1.0.0"
debug: false

ai:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7
  max_tokens: 4000
  timeout: 60

database:
  url: "sqlite:///./agentic.db"
  echo: false
  pool_size: 10
  max_overflow: 20

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null
  max_size: 10485760
  backup_count: 5

security:
  secret_key: "${SECRET_KEY}"
  algorithm: "HS256"
  access_token_expire_minutes: 30
  session_timeout: 3600

mcp_servers: {}

tools: {}

session_storage: "sqlite"
session_cleanup_interval: 3600

workflow_storage: "sqlite"
workflow_retention_days: 30

validation_enabled: true
verification_enabled: true

max_concurrent_requests: 10
request_timeout: 300
"""
            with open(target_config, "w") as f:
                f.write(basic_config)
            print("✅ Created basic config/settings.yaml")
    else:
        print("ℹ️  Configuration file already exists: config/settings.yaml")


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True


def run_tests():
    """Run basic tests."""
    print("🧪 Running tests...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v"
        ], check=True)
        print("✅ Tests passed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Some tests failed: {e}")
        print("You can still use the system, but some features may not work correctly")
    except FileNotFoundError:
        print("⚠️  pytest not found. Install it with: pip install pytest")


def create_env_file():
    """Create a .env file template."""
    env_file = Path(".env")
    
    if not env_file.exists():
        env_template = """# Agentic AI Orchestration Environment Variables
# Copy this file to .env and fill in your values

# OpenAI API Key (required for AI functionality)
OPENAI_API_KEY=your_openai_api_key_here

# Database credentials (optional)
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password

# Security (optional - will be auto-generated if not set)
SECRET_KEY=your_secret_key_here

# Logging level
LOG_LEVEL=INFO
"""
        with open(env_file, "w") as f:
            f.write(env_template)
        print("✅ Created .env file template")
        print("📝 Please edit .env and add your API keys and credentials")
    else:
        print("ℹ️  .env file already exists")


def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version}")
    return True


def main():
    """Main setup function."""
    print("🚀 Agentic AI Orchestration Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Set up configuration
    print("\n⚙️  Setting up configuration...")
    setup_configuration()
    
    # Create environment file
    print("\n🔐 Setting up environment...")
    create_env_file()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        print("Please install them manually: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run tests
    print("\n🧪 Running tests...")
    run_tests()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Edit config/settings.yaml to customize your configuration")
    print("3. Run the system:")
    print("   - CLI mode: python main.py chat")
    print("   - Web mode: python main.py web")
    print("   - Example: python examples/basic_usage.py")
    
    print("\n📚 Documentation:")
    print("- README.md: Project overview and usage")
    print("- examples/: Usage examples")
    print("- tests/: Test suite")


if __name__ == "__main__":
    main() 