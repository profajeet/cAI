# Database Interface Agent

A secure, scalable, and flexible Database Interface Agent built with LangGraph, tools, and MCP (Model Context Protocol) integration for connecting to various relational databases.

## Features

- **Multi-Database Support**: PostgreSQL, MySQL (extensible to others)
- **Interactive & Non-Interactive Modes**: CLI interface with structured input support
- **Secure Credential Management**: Encrypted storage with TTL-based sessions
- **MCP Integration**: On-demand database server activation
- **Stateful Workflows**: LangGraph-based agent with persistent session management
- **Real-time Connectivity Testing**: Connection verification with detailed feedback
- **Reference ID System**: Persistent session management with unique identifiers

## Project Structure

```
database_interfaces_Agent/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── database_config.py
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── database_agent.py
│   │   ├── state.py
│   │   └── workflows.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── connection_tools.py
│   │   ├── database_tools.py
│   │   └── security_tools.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── servers/
│   │   │   ├── __init__.py
│   │   │   ├── postgres_server.py
│   │   │   └── mysql_server.py
│   │   └── protocols.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── session_store.py
│   │   └── encryption.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_mcp.py
├── examples/
│   ├── interactive_session.py
│   ├── structured_input.py
│   └── api_usage.py
└── scripts/
    ├── setup.sh
    └── run_agent.py
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd database_interfaces_Agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp config/.env.example config/.env
# Edit config/.env with your configuration
```

## Quick Start

### Test Mode (No Redis Required)
```bash
# Test the agent functionality
python3 run_agent.py --test

# Or simply run (defaults to test mode)
python3 run_agent.py
```

### Full Setup (Requires Redis)
1. **Install Redis** (for full functionality):
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   ```

2. **Run interactive mode**:
   ```bash
   python3 run_agent.py --interactive
   ```

3. **Run API mode**:
   ```bash
   python3 run_agent.py --api --port 8000
   ```

4. **Use structured input**:
   ```bash
   python3 run_agent.py --config examples/connection_config.json
   ```

## Usage

### Interactive Mode
```bash
python3 run_agent.py --interactive
```

### Structured Input Mode
```bash
python3 run_agent.py --config examples/connection_config.json
```

### API Mode
```bash
python3 run_agent.py --api --port 8000
```

### Test Mode
```bash
python3 run_agent.py --test
```

## Configuration

The agent can be configured through:
- Environment variables
- Configuration files
- Command-line arguments

Key configuration options:
- `SESSION_TTL`: Time-to-live for sessions (default: 3600 seconds)
- `ENCRYPTION_KEY`: Encryption key for credential storage
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_TIMEOUT`: MCP server timeout (default: 30 seconds)

## Security

- All credentials are encrypted in transit and storage
- Sessions expire automatically based on TTL
- No sensitive information in logs
- Secure MCP communication protocols

## Extending the Agent

### Adding New Database Support
1. Create a new MCP server in `src/mcp/servers/`
2. Implement the required database interface
3. Register the server in the MCP client
4. Update the agent workflows

### Adding New Tools
1. Create tool functions in `src/tools/`
2. Register tools in the agent
3. Update workflows as needed

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 