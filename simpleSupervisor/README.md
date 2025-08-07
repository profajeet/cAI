# Simple Supervisor - LangGraph-based Multi-Agent System

A LangGraph-based supervisor agent that delegates tasks to specialized child agents (Math and Blog Generator) with a FastAPI backend and Streamlit frontend.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   LangGraph     │
│   Frontend      │◄──►│   Backend       │◄──►│   Supervisor    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Child Agents  │
                                              │                 │
                                              │ • Math Agent    │
                                              │ • Blog Agent    │
                                              └─────────────────┘
```

## Features

- **Supervisor Agent**: Routes user queries to appropriate child agents
- **Math Agent**: Handles basic arithmetic operations (+, -, *, /)
- **Blog Generator Agent**: Creates simple blogs on given topics
- **FastAPI Backend**: RESTful API for agent communication
- **Streamlit Frontend**: Interactive chat interface with reasoning display

## System Components

### 1. LangGraph Supervisor Agent
- **Purpose**: Orchestrates workflow and routes queries to appropriate child agents
- **Features**:
  - Query analysis and intent recognition
  - Agent selection based on query type
  - Workflow state management
  - Reasoning step tracking
- **LLM**: Powered by Ollama with llama3.2 model

### 2. Child Agents
- **Math Agent**: Handles arithmetic operations with pattern matching
- **Blog Agent**: Generates structured blog posts on given topics
- **LLM**: Both agents use Ollama with llama3.2 model

### 3. FastAPI Backend
- **Endpoints**:
  - `POST /query`: Process user queries
  - `GET /health`: Health check
  - `GET /agents`: List available agents
- **Features**: CORS support, error handling, structured responses
- **LLM Integration**: Connects to local Ollama server

### 4. Streamlit Frontend
- **Features**:
  - Interactive chat interface
  - Real-time reasoning step display
  - Agent selection visualization
  - Connection testing
  - Example queries

## Prerequisites

Before setting up the system, ensure you have:

1. **Ollama installed and running**:
   ```bash
   # Install Ollama (if not already installed)
   # Visit: https://ollama.ai/download
   
   # Pull the llama3.2 model
   ollama pull llama3.2
   
   # Start Ollama server
   ollama serve
   ```

2. **Verify Ollama setup** (optional but recommended):
   ```bash
   python check_ollama.py
   ```

3. **Python 3.8+ with pip** (for dependency management)

## Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the automated setup script
python setup.py
```

### Option 2: Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env if needed (defaults should work)
   # OLLAMA_BASE_URL=http://localhost:11434
   # OLLAMA_MODEL=llama3.2
   ```

3. **Start the system**:
   ```bash
   # Terminal 1: Start the backend
   python start_backend.py
   
   # Terminal 2: Start the frontend
   python start_frontend.py
   ```

4. **Access the application**:
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:8000/docs

## Usage

1. Open the Streamlit app in your browser (usually http://localhost:8501)
2. Type queries like:
   - Math: "What is 15 + 23?" or "Calculate 8 * 7"
   - Blog: "Write a blog about artificial intelligence" or "Create a blog post on climate change"
3. View the intermediate reasoning steps and final results

## Project Structure

```
simpleSupervisor/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py    # LangGraph supervisor agent
│   │   ├── math_agent.py    # Math operations agent
│   │   └── blog_agent.py    # Blog generation agent
│   └── models/
│       ├── __init__.py
│       └── schemas.py       # Pydantic models
├── frontend/
│   └── app.py              # Streamlit application
├── requirements.txt
└── README.md
``` 