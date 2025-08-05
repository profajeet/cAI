# Agentic AI Orchestration

An intelligent conversational AI agent that dynamically manages tasks by interacting with users, activating MCP servers, and connecting to external tools or services as needed.

## 🧠 Project Overview

This system provides a natural language interface that:
- Accepts user input in natural language
- Asks intelligent follow-up questions to clarify requirements
- Dynamically integrates with MCP servers and external tools
- Maintains session memory and workflow tracing
- Validates inputs and manages service activation

## 🏗️ Architecture

```
agentic-orchestration/
├── core/                    # Core agent functionality
│   ├── agent.py            # Main conversational agent
│   ├── context.py          # Context-aware task understanding
│   ├── session.py          # Session and memory management
│   └── workflow.py         # Workflow tracing and replay
├── mcp/                    # MCP server integration
│   ├── manager.py          # MCP server management
│   ├── adapters/           # Tool adapters
│   └── protocols.py        # MCP protocol handling
├── tools/                  # External tool integrations
│   ├── database.py         # Database client tools
│   ├── filesystem.py       # File system operations
│   └── api_client.py       # API integration tools
├── validation/             # Input validation system
│   ├── validators.py       # Validation rules
│   └── verification.py     # Service verification
├── memory/                 # Memory and storage
│   ├── session_store.py    # Session persistence
│   ├── workflow_store.py   # Workflow storage
│   └── memory_manager.py   # Memory management
├── ui/                     # User interface
│   ├── cli.py             # Command-line interface
│   └── web_ui.py          # Web interface (optional)
├── config/                 # Configuration
│   ├── settings.py         # Application settings
│   └── mcp_config.py       # MCP server configurations
├── tests/                  # Test suite
├── examples/               # Usage examples
├── requirements.txt         # Dependencies
└── main.py                # Application entry point
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MCP servers:**
   ```bash
   cp config/mcp_config.example.py config/mcp_config.py
   # Edit mcp_config.py with your server configurations
   ```

3. **Run the agent:**
   ```bash
   python main.py
   ```

## 🔧 Core Features

### 1. Conversational Agent Interface
- Natural language input processing
- Intelligent follow-up questions
- Conversational feedback and confirmations

### 2. Context-Aware Task Understanding
- Complex task breakdown
- Intent recognition
- Service/tool requirement identification

### 3. Dynamic Service Integration
- MCP server integration
- Plugin-based architecture
- Hot-pluggable modules

### 4. Input Validation & Verification
- Service credential validation
- Schema verification
- API key management

### 5. Server/Tool Activation
- Automatic MCP server management
- Load balancing and optimization
- Connection reuse and pooling

### 6. Session & Memory Handling
- Persistent session storage
- Chat history management
- Task resumption capabilities

### 7. Workflow & Communication Tracing
- Full decision-making logs
- API call tracing
- Workflow replay support

## 📋 Requirements

- Python 3.8+
- AsyncIO support
- MCP server compatibility
- Database support (SQLite/PostgreSQL)
- Web framework (FastAPI/Flask)

## 🔌 MCP Server Integration

The system supports integration with various MCP servers:
- Database servers
- File system servers
- API gateway servers
- Custom tool servers

## 📝 Usage Examples

```python
from core.agent import AgenticAgent

# Initialize the agent
agent = AgenticAgent()

# Start a conversation
response = await agent.process_input("Load the sales data into the analytics database")
# Agent will ask clarifying questions and execute the task

# Resume a session
session = await agent.load_session("user_123")
response = await agent.continue_conversation("What was the result?")
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_agent.py
python -m pytest tests/test_mcp.py
```

## 📄 License

MIT License - see LICENSE file for details. 

## 🎉 Agentic AI Orchestration System - Complete Implementation

### 📋 **Core Features Implemented:**

1. **🗨️ Conversational Agent Interface**
   - Natural language input processing
   - Intelligent follow-up questions
   - Conversational feedback and confirmations
   - Both CLI and Web interfaces

2. **🧠 Context-Aware Task Understanding**
   - Intent recognition (file operations, database operations, API calls, MCP operations)
   - Entity extraction (file paths, database names, URLs, MCP servers)
   - Context analysis and confidence scoring
   - Task breakdown and clarification detection

3. **🧩 Dynamic Service Integration (MCP + Tools)**
   - MCP server management with health checks
   - Dynamic server activation and connection management
   - Plugin-based architecture for tool adapters
   - Load balancing and optimal server selection

4. **🔌 Input Validation and Verification**
   - Service credential validation
   - File path safety checks
   - URL validation and security checks
   - Database query validation
   - API request verification

5. **📡 Server/Tool Activation**
   - Automatic MCP server health monitoring
   - Connection pooling and reuse
   - Server status caching
   - Optimal server selection based on health and load

6. **💾 Session & Memory Handling**
   - Persistent session storage with JSON files
   - Conversation history management
   - Session cleanup and expiration
   - Memory management with access statistics
   - Context caching and knowledge persistence

7. **🔁 Workflow & Communication Tracing**
   - Full decision-making workflow logging
   - API call tracing with timing
   - Tool usage tracking
   - Workflow replay capabilities
   - Performance metrics collection

### 🏗️ **Architecture Overview:**

```
agentic-orchestration/
├── core/                    # Core agent functionality
│   ├── agent.py            # Main conversational agent
│   ├── context.py          # Context-aware task understanding
│   ├── session.py          # Session and memory management
│   └── workflow.py         # Workflow tracing and replay
├── mcp/                    # MCP server integration
│   ├── manager.py          # MCP server management
│   └── adapters/           # Tool adapters (extensible)
├── tools/                  # External tool integrations
├── validation/             # Input validation system
│   └── verification.py     # Service verification
├── memory/                 # Memory and storage
│   ├── session_store.py    # Session persistence
│   ├── workflow_store.py   # Workflow storage
│   └── memory_manager.py   # Memory management
├── ui/                     # User interface
│   ├── cli.py             # Command-line interface
│   └── web_ui.py          # Web interface (FastAPI)
├── config/                 # Configuration
│   ├── settings.py         # Application settings
│   └── settings.example.yaml # Example configuration
├── tests/                  # Test suite
├── examples/               # Usage examples
├── requirements.txt         # Dependencies
├── setup.py               # Setup script
├── main.py                # Application entry point
└── README.md              # Documentation
```

### 🚀 **Getting Started:**

1. **Quick Setup:**
   ```bash
   python setup.py
   ```

2. **Manual Setup:**
   ```bash
   pip install -r requirements.txt
   cp config/settings.example.yaml config/settings.yaml
   # Edit config/settings.yaml and .env with your API keys
   ```

3. **Run the System:**
   ```bash
   # CLI mode
   python main.py chat
   
   # Web interface
   python main.py web
   
   # Run examples
   python examples/basic_usage.py
   ```

### 🔧 **Key Features:**

- **Multi-Interface Support**: CLI and Web interfaces
- **Session Management**: Persistent conversations with history
- **Workflow Tracing**: Complete audit trail of all operations
- **MCP Integration**: Dynamic server management and health monitoring
- **Validation & Security**: Input validation and service verification
- **Memory Management**: Context-aware memory with statistics
- **Extensible Architecture**: Plugin-based design for easy extension

### 📊 **Usage Examples:**

```python
from core.agent import AgenticAgent
from config.settings import Settings

# Initialize agent
settings = Settings.from_yaml("config/settings.yaml")
agent = AgenticAgent(settings)

# Process user input
response = await agent.process_input("Load the sales data into the analytics database")
print(response["response"])

# Get session history
history = await agent.get_session_history(response["session_id"])

# Get workflow trace
workflow = await agent.get_workflow_trace(response["session_id"])
```

### 📝 **Next Steps:**

1. **Configure MCP Servers**: Add your MCP server configurations to `config/settings.yaml`
2. **Set API Keys**: Add your OpenAI API key to the `.env` file
3. **Customize Tools**: Extend the tool adapters in `mcp/adapters/`
4. **Add Tests**: Expand the test suite in `tests/`
5. **Deploy**: Use the web interface for production deployment

The system is now ready for use and can be extended with additional MCP servers, tools, and custom functionality as needed! 