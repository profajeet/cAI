#!/bin/bash

# Database Interface Agent Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Database Interface Agent..."

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Make MCP servers executable
echo "🔧 Making MCP servers executable..."
chmod +x src/mcp/servers/postgres_server.py
chmod +x src/mcp/servers/mysql_server.py

# Create .env file if it doesn't exist
if [ ! -f "config/.env" ]; then
    echo "📝 Creating .env file from template..."
    cp config/env.example config/.env
    echo "⚠️  Please edit config/.env and set your encryption keys and other settings"
fi

# Create logs directory
mkdir -p logs

# Generate encryption keys if not set
if ! grep -q "your-32-character-encryption-key-here" config/.env; then
    echo "🔑 Encryption keys are already set"
else
    echo "🔑 Generating encryption keys..."
    python3 -c "
import secrets
import string
import re

# Generate encryption key
encryption_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

# Read .env file
with open('config/.env', 'r') as f:
    content = f.read()

# Replace placeholder keys
content = re.sub(r'your-32-character-encryption-key-here', encryption_key, content)
content = re.sub(r'your-secret-key-for-sessions-here', secret_key, content)

# Write back to .env file
with open('config/.env', 'w') as f:
    f.write(content)

print('✅ Encryption keys generated and saved to config/.env')
"
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Please start Redis server:"
        echo "   brew install redis && brew services start redis  # macOS"
        echo "   sudo systemctl start redis-server               # Ubuntu/Debian"
    fi
else
    echo "⚠️  Redis CLI not found. Please install Redis:"
    echo "   brew install redis  # macOS"
    echo "   sudo apt-get install redis-server  # Ubuntu/Debian"
fi

# Create test database configuration
echo "📝 Creating test configuration..."
cat > examples/test_config.json << EOF
{
  "database_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "username": "postgres",
  "password": "your_password_here",
  "database_name": "testdb",
  "operations": [
    {
      "type": "query",
      "query": "SELECT version()"
    }
  ]
}
EOF

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit config/.env with your database and Redis settings"
echo "2. Start Redis server if not already running"
echo "3. Run the agent:"
echo "   - Interactive mode: python scripts/run_agent.py --interactive"
echo "   - API mode: python scripts/run_agent.py --api"
echo "   - With config: python scripts/run_agent.py --config examples/test_config.json"
echo ""
echo "📚 Examples:"
echo "   - Interactive: python examples/interactive_session.py"
echo "   - API usage: python examples/api_usage.py"
echo ""
echo "🔧 Development:"
echo "   - Install dev dependencies: pip install -r requirements-dev.txt"
echo "   - Run tests: python -m pytest tests/"
echo "   - Format code: black src/ tests/"
echo ""
echo "Happy coding! 🚀" 