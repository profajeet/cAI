# ServiceAgent - LangGraph-based AI Agent

A modular, extensible AI agent built with LangGraph that supports both tool extensions and MCP (Model Context Protocol) integrations. The agent can be configured to enable or disable specific tools and MCP servers through a YAML configuration file.

## Architecture Overview

```
ServiceAgent/
├── config/                 # Configuration files
│   └── agent_config.yaml   # Main agent configuration
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── state.py       # Agent state management
│   │   └── config_manager.py # Configuration management
│   ├── tool_extensions/   # Tool extensions
│   │   ├── base_tool.py   # Base tool class
│   │   ├── tool_registry.py # Tool registry
│   │   ├── calculator.py  # Calculator tool example
│   │   └── file_operations.py # File operations tool
│   ├── mcp_extensions/    # MCP server extensions
│   │   ├── base_mcp.py    # Base MCP server class
│   │   ├── mcp_registry.py # MCP registry
│   │   └── filesystem_server.py # Filesystem MCP server
│   ├── agent/             # Main agent logic
│   │   └── service_agent.py # LangGraph-based agent
│   └── api/               # API server
│       └── server.py      # FastAPI server
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Features

- **Modular Architecture**: Easy to add new tools and MCP servers
- **Configuration-Driven**: Enable/disable features through YAML config
- **Multiple Run Modes**: CLI, API, and test modes
- **LangGraph Integration**: Sophisticated workflow orchestration
- **Tool Extensions**: Pluggable tools for various operations
- **MCP Integration**: Model Context Protocol server support
- **REST API**: FastAPI-based web interface
- **Comprehensive Logging**: Detailed logging and monitoring

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ServiceAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
export OPENAI_API_KEY="your-openai-api-key"
export SERPAPI_API_KEY="your-serpapi-key"  # For web search tool
```

## Configuration

The agent is configured through `config/agent_config.yaml`. Key configuration sections:

### Agent Configuration
```yaml
agent:
  name: "ServiceAgent"
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 2000
```

### Tool Extensions
```yaml
tool_extensions:
  enabled: true
  tools:
    calculator:
      enabled: true
    file_operations:
      enabled: true
      allowed_extensions: [".txt", ".md", ".py", ".json"]
      max_file_size_mb: 10
```

### MCP Extensions
```yaml
mcp_extensions:
  enabled: true
  servers:
    filesystem:
      enabled: true
      path: "./workspace"
```

## Usage

### CLI Mode (Interactive)
```bash
python main.py --mode cli
```

### API Mode (REST Server)
```bash
python main.py --mode api --port 8000
```

### Test Mode (Sample Requests)
```bash
python main.py --mode test
```

## API Endpoints

When running in API mode, the following endpoints are available:

- `POST /process` - Process a user request
- `GET /status` - Get agent status
- `GET /health` - Health check
- `GET /tools` - List available tools
- `GET /mcp-servers` - List available MCP servers

### Example API Usage

```bash
# Process a request
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Calculate 15 * 23 + 7"}'

# Get status
curl "http://localhost:8000/status"
```

## Adding New Tools

1. Create a new tool class in `src/tool_extensions/`:
```python
from .base_tool import BaseTool, ToolSchema, ToolResult

class MyTool(BaseTool):
    description = "Description of my tool"
    
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="MyTool",
            description=self.description,
            input_schema={...},
            output_schema={...},
            required_params=["param1"]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        # Tool implementation
        pass
```

2. Add configuration in `config/agent_config.yaml`:
```yaml
tool_extensions:
  tools:
    my_tool:
      enabled: true
      # Additional configuration
```

## Adding New MCP Servers

1. Create a new MCP server class in `src/mcp_extensions/`:
```python
from .base_mcp import BaseMCPServer, MCPServerSchema, MCPRequest, MCPResponse

class MyMCPServer(BaseMCPServer):
    description = "Description of my MCP server"
    version = "1.0.0"
    
    def _create_schema(self) -> MCPServerSchema:
        return MCPServerSchema(...)
    
    async def connect(self) -> bool:
        # Connection logic
        pass
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        # Request handling logic
        pass
```

2. Add configuration in `config/agent_config.yaml`:
```yaml
mcp_extensions:
  servers:
    my_server:
      enabled: true
      # Additional configuration
```

## LangGraph Workflow

The agent uses LangGraph to orchestrate a sophisticated workflow:

1. **Analyze Input**: Parse user request and determine required tools/MCP calls
2. **Execute Tools**: Run enabled tools with appropriate parameters
3. **Execute MCP**: Make calls to enabled MCP servers
4. **Generate Response**: Create final response based on results
5. **Check Completion**: Determine if workflow should continue or end

## State Management

The agent maintains comprehensive state including:
- Conversation history
- Tool execution results
- MCP server responses
- Iteration tracking
- Performance metrics

## Logging

Logs are written to `logs/agent.log` and can be configured in the YAML config:

```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/agent.log"
```

## Development

### Project Structure
- `src/core/`: Core functionality and state management
- `src/tool_extensions/`: Tool implementations and registry
- `src/mcp_extensions/`: MCP server implementations and registry
- `src/agent/`: Main agent logic with LangGraph workflow
- `src/api/`: FastAPI server implementation

### Adding Features
1. Create new tool/MCP server classes
2. Add configuration options
3. Update documentation
4. Add tests (recommended)

## Environment Variables

The following environment variables can be used in configuration:
- `${OPENAI_API_KEY}` - OpenAI API key
- `${SERPAPI_API_KEY}` - SerpAPI key for web search
- `${GITHUB_TOKEN}` - GitHub token for GitHub MCP server
- `${DATABASE_URL}` - Database connection string

## Troubleshooting

### Common Issues

1. **Configuration not found**: Ensure `config/agent_config.yaml` exists
2. **Tool not enabled**: Check tool configuration in YAML file
3. **API key missing**: Set required environment variables
4. **Import errors**: Ensure all dependencies are installed

### Debug Mode

Enable debug logging by setting log level to DEBUG in configuration:
```yaml
logging:
  level: "DEBUG"
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here] 