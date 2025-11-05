# GUI Implementation Guide

**Author:** Manus AI
**Date:** November 4, 2025

## 1. Overview

This guide provides instructions for building a simple, user-friendly chat interface for the Regulatory Search Agent using Streamlit. Streamlit is chosen for its simplicity and rapid development capabilities.

## 2. Installing Streamlit

Add Streamlit to your dependencies:

```bash
poetry add streamlit
# or
pip install streamlit
```

## 3. Basic Chat Interface

Create `app/gui/chat_interface.py`:

```python
import streamlit as st
import requests
from typing import List, Dict

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Regulatory Search Agent",
    page_icon="🔬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .source-title {
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

def query_agent(query: str, model: str, k: int) -> Dict:
    """Send query to the backend API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={
                "query": query,
                "model": model,
                "k": k
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def index_documents(drug_name: str, agencies: List[str]) -> Dict:
    """Trigger document retrieval and indexing."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/orchestrate",
            json={
                "drug_name": drug_name,
                "agencies": agencies
            },
            timeout=300
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Header
st.markdown('<div class="main-header">🔬 Regulatory Search Agent</div>', unsafe_allow_html=True)
st.markdown("Ask questions about drug regulatory documents from FDA, EMA, Health Canada, TGA, NHRA, and Swissmedic.")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model selection
    model_option = st.selectbox(
        "Select OpenAI Model",
        ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0
    )
    
    # Number of context chunks
    k_value = st.slider(
        "Number of context chunks",
        min_value=3,
        max_value=10,
        value=5,
        help="Number of document chunks to retrieve for context"
    )
    
    st.divider()
    
    # Document retrieval section
    st.header("📥 Retrieve Documents")
    
    drug_name_input = st.text_input(
        "Drug Name",
        placeholder="e.g., Keytruda, Humira"
    )
    
    agencies_selected = st.multiselect(
        "Select Agencies",
        ["FDA", "EMA", "Health Canada", "TGA", "Swissmedic", "NHRA"],
        default=["FDA", "EMA", "Health Canada"]
    )
    
    if st.button("🔍 Retrieve & Index Documents", use_container_width=True):
        if drug_name_input:
            with st.spinner(f"Retrieving documents for {drug_name_input}..."):
                result = index_documents(drug_name_input, agencies_selected)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"✅ Retrieved and indexed {result.get('documents_indexed', 0)} documents")
                    st.info(f"Searched: {', '.join(result.get('agencies_searched', []))}")
        else:
            st.warning("Please enter a drug name")
    
    st.divider()
    
    # System status
    st.header("📊 System Status")
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ Backend Online")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Offline")

# Main chat interface
st.header("💬 Chat Interface")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display sources if available
        if "sources" in message and message["sources"]:
            with st.expander("📚 View Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**Source {i}:** {source.get('document', 'Unknown')}")

# Chat input
if prompt := st.chat_input("Ask a question about regulatory documents..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = query_agent(prompt, model_option, k_value)
            
            if "error" in response:
                error_message = f"❌ Error: {response['error']}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })
            else:
                answer = response.get("answer", "No answer generated")
                sources = response.get("sources", [])
                
                # Display answer
                st.markdown(answer)
                
                # Display sources
                if sources:
                    with st.expander("📚 View Sources"):
                        for i, source in enumerate(sources, 1):
                            st.markdown(f"**Source {i}:** {source.get('document', 'Unknown')}")
                
                # Display metadata
                st.caption(f"Model: {response.get('model_used', 'unknown')} | "
                          f"Chunks retrieved: {response.get('num_chunks_retrieved', 0)}")
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

# Clear chat button
if st.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()
```

## 4. Adding Orchestrator Endpoint

Update `main.py` to add the orchestration endpoint:

```python
from app.core.orchestrator import AgenticOrchestrator

# Initialize orchestrator
orchestrator = AgenticOrchestrator()

class OrchestrationRequest(BaseModel):
    drug_name: str
    agencies: Optional[List[str]] = None

@app.post("/api/orchestrate")
async def orchestrate(request: OrchestrationRequest):
    """
    Orchestrate document retrieval and indexing.
    """
    try:
        result = orchestrator.process_query(
            drug_name=request.drug_name,
            agencies=request.agencies
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 5. Running the GUI

To run the Streamlit interface:

```bash
streamlit run app/gui/chat_interface.py
```

The interface will be available at `http://localhost:8501`.

## 6. Alternative: Gradio Implementation

If you prefer Gradio, here's an alternative implementation. Create `app/gui/gradio_interface.py`:

```python
import gradio as gr
import requests
from typing import List, Tuple

API_BASE_URL = "http://localhost:8000"

def query_agent(message: str, history: List, model: str, k: int) -> Tuple[str, List]:
    """Query the agent and return response."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={
                "query": message,
                "model": model,
                "k": k
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        answer = result.get("answer", "No answer generated")
        sources = result.get("sources", [])
        
        # Format sources
        if sources:
            sources_text = "\n\n**Sources:**\n"
            for i, source in enumerate(sources, 1):
                sources_text += f"{i}. {source.get('document', 'Unknown')}\n"
            answer += sources_text
        
        history.append((message, answer))
        return "", history
    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append((message, error_msg))
        return "", history

def retrieve_documents(drug_name: str, agencies: List[str]) -> str:
    """Retrieve and index documents."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/orchestrate",
            json={
                "drug_name": drug_name,
                "agencies": agencies
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        
        return (f"✅ Success!\n"
                f"- Searched: {', '.join(result.get('agencies_searched', []))}\n"
                f"- Downloaded: {len(result.get('documents_downloaded', []))} documents\n"
                f"- Indexed: {result.get('documents_indexed', 0)} documents")
    
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Build Gradio interface
with gr.Blocks(title="Regulatory Search Agent") as demo:
    gr.Markdown("# 🔬 Regulatory Search Agent")
    gr.Markdown("Ask questions about drug regulatory documents from major health agencies.")
    
    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Conversation", height=500)
                msg = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask a question about regulatory documents...",
                    lines=2
                )
                with gr.Row():
                    submit = gr.Button("Submit", variant="primary")
                    clear = gr.Button("Clear")
            
            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    value="gpt-4",
                    label="Model"
                )
                k_slider = gr.Slider(
                    minimum=3,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Context Chunks"
                )
    
    with gr.Tab("Retrieve Documents"):
        gr.Markdown("### Retrieve and index regulatory documents")
        
        drug_name = gr.Textbox(
            label="Drug Name",
            placeholder="e.g., Keytruda, Humira"
        )
        
        agencies = gr.CheckboxGroup(
            choices=["FDA", "EMA", "Health Canada", "TGA", "Swissmedic", "NHRA"],
            value=["FDA", "EMA", "Health Canada"],
            label="Select Agencies"
        )
        
        retrieve_btn = gr.Button("Retrieve & Index", variant="primary")
        retrieve_output = gr.Textbox(label="Status", lines=5)
        
        retrieve_btn.click(
            retrieve_documents,
            inputs=[drug_name, agencies],
            outputs=retrieve_output
        )
    
    # Event handlers
    submit.click(
        query_agent,
        inputs=[msg, chatbot, model_dropdown, k_slider],
        outputs=[msg, chatbot]
    )
    
    msg.submit(
        query_agent,
        inputs=[msg, chatbot, model_dropdown, k_slider],
        outputs=[msg, chatbot]
    )
    
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

Run with:

```bash
python app/gui/gradio_interface.py
```

## 7. Deployment Considerations

For production deployment:

1. **Environment Variables**: Ensure all sensitive configuration is in environment variables
2. **Authentication**: Add user authentication if needed
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Logging**: Add comprehensive logging for monitoring
5. **Error Handling**: Improve error messages for better user experience
6. **Caching**: Cache responses to reduce API costs
7. **Monitoring**: Add health checks and monitoring dashboards
