import re
from typing import Dict, Any
from langchain_ollama import OllamaLLM
import os

class BlogAgent:
    """Agent for generating simple blog posts on given topics"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7
        )
        
        self.system_prompt = """You are a blog writing agent that creates engaging, informative blog posts.
        
        When given a topic:
        1. Create a compelling title
        2. Write 3-4 paragraphs (approximately 300-500 words)
        3. Make the content engaging and informative
        4. Use a conversational tone
        5. Include relevant examples or insights
        
        Structure your blog post as follows:
        - Title: [Engaging title]
        - Introduction: Hook the reader and introduce the topic
        - Body: 2-3 paragraphs with main content
        - Conclusion: Summarize key points and provide a closing thought
        
        Make the content accessible to a general audience while being informative."""
    
    def can_handle(self, query: str) -> bool:
        """Check if this agent can handle the given query"""
        # Look for blog-related keywords
        blog_patterns = [
            r'write\s+a\s+blog',           # "Write a blog"
            r'create\s+a\s+blog',          # "Create a blog"
            r'blog\s+about',               # "Blog about"
            r'blog\s+post',                # "Blog post"
            r'article\s+about',            # "Article about"
            r'write\s+about',              # "Write about"
            r'create\s+content\s+about',   # "Create content about"
            r'generate\s+a\s+blog',        # "Generate a blog"
            r'compose\s+a\s+blog',         # "Compose a blog"
            r'draft\s+a\s+blog'            # "Draft a blog"
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in blog_patterns)
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process the blog generation query and return result"""
        try:
            # Extract the topic from the query
            topic = self._extract_topic(query)
            
            # For Ollama, we'll use a simpler approach with direct text generation
            full_prompt = f"{self.system_prompt}\n\nUser: Write a blog post about: {topic}\nAssistant:"
            
            response = self.llm.invoke(full_prompt)
            result = response.strip()
            
            return {
                "success": True,
                "result": result,
                "agent": "Blog Agent",
                "operation": "blog_generation",
                "topic": topic
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": f"Error generating blog: {str(e)}",
                "agent": "Blog Agent",
                "operation": "blog_generation"
            }
    
    def _extract_topic(self, query: str) -> str:
        """Extract the topic from the blog request query"""
        # Remove common blog request phrases
        topic = query.lower()
        
        # Remove blog request patterns
        patterns_to_remove = [
            r'write\s+a\s+blog\s+(?:about|on)\s*',
            r'create\s+a\s+blog\s+(?:about|on)\s*',
            r'blog\s+about\s*',
            r'write\s+a\s+blog\s+post\s+(?:about|on)\s*',
            r'create\s+a\s+blog\s+post\s+(?:about|on)\s*',
            r'generate\s+a\s+blog\s+(?:about|on)\s*',
            r'compose\s+a\s+blog\s+(?:about|on)\s*',
            r'draft\s+a\s+blog\s+(?:about|on)\s*',
            r'write\s+about\s*',
            r'create\s+content\s+about\s*'
        ]
        
        for pattern in patterns_to_remove:
            topic = re.sub(pattern, '', topic)
        
        # Clean up and capitalize
        topic = topic.strip()
        if topic:
            return topic.capitalize()
        else:
            return "general topic" 