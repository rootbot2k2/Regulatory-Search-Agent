"""
Gradio chat interface for the Regulatory Search Agent.
"""
import gradio as gr
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.orchestrator import AgenticOrchestrator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize orchestrator
orchestrator = AgenticOrchestrator()


def retrieve_documents(drug_name: str, agencies: list, max_docs: int) -> str:
    """
    Retrieve and index documents from regulatory agencies.
    
    Args:
        drug_name: Name of the drug to search for
        agencies: List of selected agencies
        max_docs: Maximum documents per agency
        
    Returns:
        Status message
    """
    try:
        if not drug_name or not drug_name.strip():
            return "❌ Please enter a drug name"
        
        if not agencies:
            return "❌ Please select at least one agency"
        
        logger.info(f"Retrieving documents for: {drug_name}")
        
        result = orchestrator.retrieve_and_index(
            drug_name=drug_name.strip(),
            agencies=agencies,
            max_docs_per_agency=max_docs
        )
        
        if result['status'] == 'error':
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        # Format success message
        message = f"""✅ **Document Retrieval Complete!**

**Drug:** {result['drug_name']}
**Agencies Searched:** {', '.join(result['agencies_searched'])}
**Documents Downloaded:** {len(result['documents_downloaded'])}
**Documents Indexed:** {result['documents_indexed']}
**Total Vectors in Index:** {result['total_vectors_in_index']}
**Unique Documents:** {result['unique_documents_in_index']}
"""
        
        if result['errors']:
            message += f"\n**Warnings/Errors:**\n"
            for error in result['errors'][:5]:  # Show first 5 errors
                message += f"- {error}\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Error in retrieve_documents: {str(e)}")
        return f"❌ Error: {str(e)}"


def chat_with_agent(message: str, history: list, model: str, k: int) -> tuple:
    """
    Process a chat message and return response.
    
    Args:
        message: User's message
        history: Chat history
        model: Selected model
        k: Number of context chunks
        
    Returns:
        Tuple of (empty string, updated history)
    """
    try:
        if not message or not message.strip():
            return "", history
        
        logger.info(f"Processing query: {message[:100]}...")
        
        # Query the orchestrator
        result = orchestrator.query(
            question=message.strip(),
            model=model,
            k=k
        )
        
        # Format response
        answer = result.get('answer', 'No answer generated')
        
        # Add source information
        sources = result.get('sources', [])
        if sources:
            answer += "\n\n**Sources:**\n"
            for i, source in enumerate(sources[:5], 1):  # Show top 5 sources
                answer += f"{i}. {source.get('document', 'Unknown')} (chunk {source.get('chunk_index', 0)})\n"
        
        # Add metadata
        answer += f"\n*Model: {result.get('model_used', 'unknown')} | Chunks: {result.get('num_chunks_retrieved', 0)}*"
        
        # Update history
        history.append((message, answer))
        
        return "", history
        
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        error_msg = f"❌ Error: {str(e)}"
        history.append((message, error_msg))
        return "", history


def get_system_status() -> str:
    """Get current system status."""
    try:
        status = orchestrator.get_system_status()
        
        message = f"""**System Status: {status['status'].upper()}**

**Vector Store:**
- Total Vectors: {status['vector_store']['total_vectors']}
- Unique Documents: {status['vector_store']['unique_documents']}
- Dimension: {status['vector_store']['dimension']}

**Available Agencies:** {', '.join(status['available_agencies'])}

**Models:**
- Embedding: {status['models']['embedding']}
- Chat: {status['models']['chat']}
"""
        return message
        
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"


# Build Gradio interface
with gr.Blocks(
    title="Regulatory Search Agent",
    theme=gr.themes.Soft()
) as demo:
    
    gr.Markdown("""
    # 🔬 Regulatory Search Agent
    
    An intelligent AI system for automated retrieval and analysis of drug regulatory documents from FDA and EMA.
    """)
    
    with gr.Tabs():
        
        # Tab 1: Chat Interface
        with gr.Tab("💬 Chat"):
            gr.Markdown("Ask questions about indexed regulatory documents.")
            
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=500,
                        show_label=True
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a question about regulatory documents...",
                            lines=2,
                            scale=4
                        )
                        submit_btn = gr.Button("Submit", variant="primary", scale=1)
                    
                    clear_btn = gr.Button("Clear Chat")
                
                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ Settings")
                    
                    model_dropdown = gr.Dropdown(
                        choices=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                        value="gpt-4",
                        label="Model",
                        info="Select the OpenAI model to use"
                    )
                    
                    k_slider = gr.Slider(
                        minimum=3,
                        maximum=10,
                        value=5,
                        step=1,
                        label="Context Chunks",
                        info="Number of document chunks to retrieve"
                    )
                    
                    gr.Markdown("### 💡 Tips")
                    gr.Markdown("""
                    - Be specific in your questions
                    - Mention drug names when relevant
                    - Ask about safety, efficacy, or approval processes
                    """)
        
        # Tab 2: Document Retrieval
        with gr.Tab("📥 Retrieve Documents"):
            gr.Markdown("Search and index regulatory documents from FDA and EMA.")
            
            with gr.Row():
                with gr.Column():
                    drug_name_input = gr.Textbox(
                        label="Drug Name",
                        placeholder="e.g., Keytruda, Humira, Opdivo",
                        info="Enter the brand or generic name of the drug"
                    )
                    
                    agencies_checkbox = gr.CheckboxGroup(
                        choices=["FDA", "EMA"],
                        value=["FDA", "EMA"],
                        label="Select Agencies",
                        info="Choose which regulatory agencies to search"
                    )
                    
                    max_docs_slider = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        label="Max Documents per Agency",
                        info="Limit the number of documents to download"
                    )
                    
                    retrieve_btn = gr.Button("🔍 Retrieve & Index Documents", variant="primary", size="lg")
                
                with gr.Column():
                    retrieve_output = gr.Markdown(
                        label="Status",
                        value="*Ready to retrieve documents*"
                    )
            
            gr.Markdown("""
            ### 📝 Instructions
            1. Enter the drug name you want to search for
            2. Select the regulatory agencies (FDA and/or EMA)
            3. Choose how many documents to download per agency
            4. Click "Retrieve & Index Documents"
            5. Wait for the process to complete (this may take a few minutes)
            6. Once complete, go to the Chat tab to ask questions
            
            **Note:** The first retrieval may take longer as the system initializes web drivers.
            """)
        
        # Tab 3: System Status
        with gr.Tab("📊 System Status"):
            gr.Markdown("View the current status of the Regulatory Search Agent.")
            
            status_output = gr.Markdown(value="*Loading status...*")
            refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
            
            gr.Markdown("""
            ### 📈 About the System
            
            The Regulatory Search Agent uses:
            - **FAISS** for local vector storage
            - **OpenAI** for embeddings and chat completion
            - **Selenium** for web automation
            - **PyMuPDF** for PDF processing
            
            All data is stored locally for privacy and control.
            """)
    
    # Event handlers
    submit_btn.click(
        chat_with_agent,
        inputs=[msg, chatbot, model_dropdown, k_slider],
        outputs=[msg, chatbot]
    )
    
    msg.submit(
        chat_with_agent,
        inputs=[msg, chatbot, model_dropdown, k_slider],
        outputs=[msg, chatbot]
    )
    
    clear_btn.click(
        lambda: None,
        None,
        chatbot,
        queue=False
    )
    
    retrieve_btn.click(
        retrieve_documents,
        inputs=[drug_name_input, agencies_checkbox, max_docs_slider],
        outputs=retrieve_output
    )
    
    refresh_btn.click(
        get_system_status,
        outputs=status_output
    )
    
    # Load status on startup
    demo.load(
        get_system_status,
        outputs=status_output
    )


if __name__ == "__main__":
    logger.info("Starting Gradio interface...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
