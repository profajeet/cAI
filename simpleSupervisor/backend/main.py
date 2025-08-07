from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from models.schemas import QueryRequest, QueryResponse, ReasoningStep, HealthResponse
from agents.supervisor import SupervisorAgent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Simple Supervisor API",
    description="LangGraph-based supervisor agent with math and blog generation capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the supervisor agent
supervisor = SupervisorAgent()

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Simple Supervisor API is running"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Simple Supervisor API is running"
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query through the supervisor agent"""
    try:
        # Check if Ollama is configured
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        # Test Ollama connection
        try:
            import requests
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama server not responding at {ollama_base_url}. Please ensure Ollama is running."
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cannot connect to Ollama at {ollama_base_url}. Please ensure Ollama is running and the model '{ollama_model}' is available."
            )
        
        # Process the query
        result = supervisor.process_query(request.query)
        
        # Convert reasoning steps to the expected format
        reasoning_steps = []
        for step in result.get("reasoning_steps", []):
            reasoning_steps.append(ReasoningStep(
                step=step["step"],
                agent=step["agent"],
                input=step["input"],
                output=step["output"],
                timestamp=step["timestamp"]
            ))
        
        return QueryResponse(
            final_result=result["final_result"],
            reasoning_steps=reasoning_steps,
            selected_agent=result["selected_agent"],
            success=result["success"],
            error_message=result.get("error", None)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.get("/agents")
async def get_available_agents():
    """Get information about available agents"""
    return {
        "agents": [
            {
                "name": "Math Agent",
                "description": "Handles basic arithmetic operations (+, -, *, /)",
                "examples": [
                    "What is 5 + 3?",
                    "Calculate 10 * 7",
                    "What's 15 - 8?",
                    "Divide 20 by 4"
                ]
            },
            {
                "name": "Blog Agent",
                "description": "Generates simple blog posts on given topics",
                "examples": [
                    "Write a blog about artificial intelligence",
                    "Create a blog post on climate change",
                    "Generate a blog about renewable energy"
                ]
            }
        ]
    }

if __name__ == "__main__":
    # Check for Ollama configuration
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    print(f"🔍 Checking Ollama connection at {ollama_base_url}...")
    try:
        import requests
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ Ollama server is running")
            print(f"🎯 Using model: {ollama_model}")
        else:
            print(f"❌ Ollama server not responding properly")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print(f"💡 Please ensure Ollama is running at {ollama_base_url}")
        print(f"💡 Make sure the model '{ollama_model}' is available")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 