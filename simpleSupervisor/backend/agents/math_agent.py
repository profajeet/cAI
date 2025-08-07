import re
from typing import Dict, Any
from langchain_ollama import OllamaLLM
import os

class MathAgent:
    """Agent for handling basic arithmetic operations"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0
        )
        
        self.system_prompt = """You are a math agent that performs basic arithmetic operations.
        You can handle addition (+), subtraction (-), multiplication (*), and division (/).
        
        When given a math problem:
        1. Extract the numbers and operation
        2. Perform the calculation
        3. Return the result in a clear format
        
        Examples:
        - "What is 5 + 3?" → "5 + 3 = 8"
        - "Calculate 10 * 7" → "10 * 7 = 70"
        - "What's 15 - 8?" → "15 - 8 = 7"
        - "Divide 20 by 4" → "20 ÷ 4 = 5"
        
        Always show your work and provide the final answer clearly."""
    
    def can_handle(self, query: str) -> bool:
        """Check if this agent can handle the given query"""
        # Look for mathematical operations
        math_patterns = [
            r'\d+\s*[\+\-\*\/]\s*\d+',  # Basic operations
            r'what\s+is\s+\d+',         # "What is X"
            r'calculate\s+\d+',         # "Calculate X"
            r'add\s+\d+',               # "Add X"
            r'subtract\s+\d+',          # "Subtract X"
            r'multiply\s+\d+',          # "Multiply X"
            r'divide\s+\d+',            # "Divide X"
            r'\d+\s+plus\s+\d+',        # "X plus Y"
            r'\d+\s+minus\s+\d+',       # "X minus Y"
            r'\d+\s+times\s+\d+',       # "X times Y"
            r'\d+\s+divided\s+by\s+\d+' # "X divided by Y"
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in math_patterns)
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process the math query and return result"""
        try:
            # For Ollama, we'll use a simpler approach with direct text generation
            full_prompt = f"{self.system_prompt}\n\nUser: {query}\nAssistant:"
            
            response = self.llm.invoke(full_prompt)
            result = response.strip()
            
            return {
                "success": True,
                "result": result,
                "agent": "Math Agent",
                "operation": "arithmetic_calculation"
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": f"Error processing math query: {str(e)}",
                "agent": "Math Agent",
                "operation": "arithmetic_calculation"
            } 