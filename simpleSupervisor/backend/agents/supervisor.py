from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
import os
from datetime import datetime
from .math_agent import MathAgent
from .blog_agent import BlogAgent

# Define the state structure
class AgentState(TypedDict):
    query: str
    selected_agent: str
    agent_result: Dict[str, Any]
    reasoning_steps: List[Dict[str, str]]
    final_result: str
    error: str

class SupervisorAgent:
    """LangGraph-based supervisor agent that orchestrates child agents"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0
        )
        
        self.math_agent = MathAgent()
        self.blog_agent = BlogAgent()
        
        # Create the LangGraph workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("process_with_math", self._process_with_math)
        workflow.add_node("process_with_blog", self._process_with_blog)
        workflow.add_node("finalize_response", self._finalize_response)
        
        # Add edges
        workflow.add_edge("analyze_query", "route_to_agent")
        workflow.add_conditional_edges(
            "route_to_agent",
            self._should_route_to_math,
            {
                "math": "process_with_math",
                "blog": "process_with_blog",
                "unknown": "finalize_response"
            }
        )
        workflow.add_edge("process_with_math", "finalize_response")
        workflow.add_edge("process_with_blog", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_query")
        
        return workflow.compile()
    
    def _analyze_query(self, state: AgentState) -> AgentState:
        """Analyze the user query to understand the intent"""
        query = state["query"]
        
        reasoning_step = {
            "step": "Query Analysis",
            "agent": "Supervisor",
            "input": query,
            "output": f"Analyzing query: '{query}' to determine appropriate agent",
            "timestamp": datetime.now().isoformat()
        }
        
        state["reasoning_steps"] = [reasoning_step]
        return state
    
    def _route_to_agent(self, state: AgentState) -> AgentState:
        """Route the query to the appropriate agent"""
        query = state["query"]
        
        # Check which agent can handle the query
        if self.math_agent.can_handle(query):
            selected_agent = "math"
            agent_name = "Math Agent"
        elif self.blog_agent.can_handle(query):
            selected_agent = "blog"
            agent_name = "Blog Agent"
        else:
            selected_agent = "unknown"
            agent_name = "No suitable agent found"
        
        reasoning_step = {
            "step": "Agent Selection",
            "agent": "Supervisor",
            "input": query,
            "output": f"Selected {agent_name} for query processing",
            "timestamp": datetime.now().isoformat()
        }
        
        state["selected_agent"] = selected_agent
        state["reasoning_steps"].append(reasoning_step)
        
        return state
    
    def _should_route_to_math(self, state: AgentState) -> str:
        """Determine which agent to route to"""
        return state["selected_agent"]
    
    def _process_with_math(self, state: AgentState) -> AgentState:
        """Process the query with the math agent"""
        query = state["query"]
        
        # Process with math agent
        result = self.math_agent.process(query)
        
        reasoning_step = {
            "step": "Math Processing",
            "agent": "Math Agent",
            "input": query,
            "output": result["result"],
            "timestamp": datetime.now().isoformat()
        }
        
        state["agent_result"] = result
        state["reasoning_steps"].append(reasoning_step)
        
        return state
    
    def _process_with_blog(self, state: AgentState) -> AgentState:
        """Process the query with the blog agent"""
        query = state["query"]
        
        # Process with blog agent
        result = self.blog_agent.process(query)
        
        reasoning_step = {
            "step": "Blog Generation",
            "agent": "Blog Agent",
            "input": query,
            "output": f"Generated blog post about: {result.get('topic', 'topic')}",
            "timestamp": datetime.now().isoformat()
        }
        
        state["agent_result"] = result
        state["reasoning_steps"].append(reasoning_step)
        
        return state
    
    def _finalize_response(self, state: AgentState) -> AgentState:
        """Finalize the response and prepare the result"""
        if state["selected_agent"] == "unknown":
            # No suitable agent found
            final_result = "I'm sorry, I couldn't determine how to handle your request. Please try asking for a math calculation (e.g., 'What is 5 + 3?') or a blog post (e.g., 'Write a blog about AI')."
            state["error"] = "No suitable agent found"
        else:
            # Get result from the selected agent
            agent_result = state["agent_result"]
            if agent_result["success"]:
                final_result = agent_result["result"]
            else:
                final_result = f"Error: {agent_result['result']}"
                state["error"] = agent_result["result"]
        
        reasoning_step = {
            "step": "Response Finalization",
            "agent": "Supervisor",
            "input": f"Agent result: {state.get('agent_result', {})}",
            "output": "Preparing final response for user",
            "timestamp": datetime.now().isoformat()
        }
        
        state["final_result"] = final_result
        state["reasoning_steps"].append(reasoning_step)
        
        return state
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the workflow"""
        try:
            # Initialize state
            initial_state = AgentState(
                query=query,
                selected_agent="",
                agent_result={},
                reasoning_steps=[],
                final_result="",
                error=""
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "success": True,
                "final_result": final_state["final_result"],
                "reasoning_steps": final_state["reasoning_steps"],
                "selected_agent": final_state["selected_agent"],
                "error": final_state.get("error", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "final_result": f"Error processing query: {str(e)}",
                "reasoning_steps": [],
                "selected_agent": "",
                "error": str(e)
            } 