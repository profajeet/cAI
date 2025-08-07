import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Simple Supervisor - AI Agent Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    
    .reasoning-step {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    .agent-badge {
        display: inline-block;
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .step-badge {
        display: inline-block;
        background-color: #ff9800;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .timestamp {
        color: #666;
        font-size: 0.8rem;
        font-style: italic;
    }
    
    .error-message {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 0.5rem;
        padding: 1rem;
        color: #c62828;
    }
    
    .success-message {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 0.5rem;
        padding: 1rem;
        color: #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

if "example_text" not in st.session_state:
    st.session_state.example_text = ""

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # API URL configuration
    api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        help="URL of the FastAPI backend server"
    )
    st.session_state.api_url = api_url
    
    # Test connection
    if st.button("Test Connection"):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connected to API")
            else:
                st.error("❌ API connection failed")
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")
    
    st.divider()
    
    # Available agents info
    st.subheader("🤖 Available Agents")
    try:
        response = requests.get(f"{api_url}/agents", timeout=5)
        if response.status_code == 200:
            agents = response.json()["agents"]
            for agent in agents:
                with st.expander(f"{agent['name']}"):
                    st.write(agent['description'])
                    st.write("**Examples:**")
                    for example in agent['examples']:
                        st.write(f"• {example}")
        else:
            st.error("Failed to load agents info")
    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.markdown('<h1 class="main-header">🤖 Simple Supervisor AI Agent</h1>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.container():
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    else:
        with st.container():
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            # Display reasoning steps if available
            if "reasoning_steps" in message:
                with st.expander("🔍 View Reasoning Steps", expanded=False):
                    for i, step in enumerate(message["reasoning_steps"], 1):
                        st.markdown(f"""
                        <div class="reasoning-step">
                            <span class="step-badge">Step {i}</span>
                            <span class="agent-badge">{step['agent']}</span><br><br>
                            <strong>Step:</strong> {step['step']}<br>
                            <strong>Input:</strong> {step['input']}<br>
                            <strong>Output:</strong> {step['output']}<br>
                            <span class="timestamp">{step['timestamp']}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Display selected agent
            if "selected_agent" in message and message["selected_agent"]:
                agent_name = "Math Agent" if message["selected_agent"] == "math" else "Blog Agent"
                st.info(f"🎯 Selected Agent: {agent_name}")

# Chat input
with st.container():
    st.markdown("---")
    
    # Example buttons outside the form
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        math_example = st.button("📝 Example: Math", use_container_width=True)
    
    with col2:
        blog_example = st.button("📝 Example: Blog", use_container_width=True)
    
    with col3:
        pass  # Empty column for spacing
    
    # Handle example buttons
    if math_example:
        st.session_state.example_text = "What is 25 * 8?"
        st.rerun()
    
    if blog_example:
        st.session_state.example_text = "Write a blog about renewable energy"
        st.rerun()
    
    # Use a form for better state management
    with st.form(key="query_form", clear_on_submit=True):
        # Query input with example text
        initial_text = st.session_state.example_text
        query = st.text_area(
            "💬 Ask me anything!",
            value=initial_text,
            placeholder="Try: 'What is 15 + 23?' or 'Write a blog about artificial intelligence'",
            height=100,
            key="query_input"
        )
        
        send_button = st.form_submit_button("🚀 Send", type="primary", use_container_width=True)

# Process query when send button is clicked
if send_button and query.strip():
    # Clear example text after submission
    st.session_state.example_text = ""
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Show processing message
    with st.spinner("🤔 Processing your request..."):
        try:
            # Send request to API
            response = requests.post(
                f"{st.session_state.api_url}/query",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add assistant message to chat
                assistant_message = {
                    "role": "assistant",
                    "content": result.get("final_result", "No result received"),
                    "reasoning_steps": result.get("reasoning_steps", []),
                    "selected_agent": result.get("selected_agent", "")
                }
                
                st.session_state.messages.append(assistant_message)
                
                # Show success message
                st.success("✅ Response received successfully!")
                
            else:
                error_msg = f"❌ API Error: {response.status_code} - {response.text}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                st.error(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "❌ Request timed out. Please try again."
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            st.error(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = "❌ Connection error. Please check if the API server is running."
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            st.error(error_msg)
            
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            st.error(error_msg)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Built with ❤️ using LangGraph, FastAPI, and Streamlit<br>
        Simple Supervisor AI Agent System
    </div>
    """,
    unsafe_allow_html=True
) 