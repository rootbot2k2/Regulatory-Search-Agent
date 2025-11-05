"""
Enhanced autonomous Gradio interface with intelligent query processing.
"""
import gradio as gr
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.autonomous_orchestrator import AutonomousOrchestrator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize autonomous orchestrator
orchestrator = AutonomousOrchestrator()


def autonomous_chat(message: str, history: list, agencies: list, model: str) -> tuple:
    """
    Process a chat message autonomously.
    
    The system will:
    1. Analyze the query
    2. Extract drug names
    3. Retrieve documents if needed
    4. Generate comprehensive answer
    
    Args:
        message: User's message
        history: Chat history
        agencies: Selected agencies
        model: Selected model
        
    Returns:
        Tuple of (empty string, updated history)
    """
    try:
        if not message or not message.strip():
            return "", history
        
        logger.info(f"Processing autonomous query: {message[:100]}...")
        
        # Process query autonomously
        result = orchestrator.process_query(
            query=message.strip(),
            session_id="default",
            selected_agencies=agencies if agencies else None,
            model=model
        )
        
        # Handle clarification needed
        if result.get('status') == 'clarification_needed':
            answer = f"🤔 **Clarification Needed**\n\n{result['question']}"
            history.append((message, answer))
            return "", history
        
        # Handle errors
        if result.get('status') == 'error':
            answer = f"❌ **Error**\n\n{result.get('answer', result.get('error', 'Unknown error'))}"
            history.append((message, answer))
            return "", history
        
        # Format successful answer
        answer = result.get('answer', 'No answer generated')
        
        # Add metadata
        answer_type = result.get('type', 'standard')
        
        if answer_type == 'comparative':
            answer = f"📊 **Comparative Analysis**\n\n{answer}"
            agencies_compared = result.get('agencies_compared', [])
            answer += f"\n\n*Agencies compared: {', '.join(agencies_compared)}*"
        
        # Add context summary
        context = result.get('context_summary', {})
        if context.get('current_drug'):
            answer += f"\n\n*Current drug: {context['current_drug']} | Documents indexed: {context.get('documents_indexed', 0)}*"
        
        # Add model info
        answer += f"\n\n*Model: {result.get('model_used', model)}*"
        
        # Update history
        history.append((message, answer))
        
        return "", history
        
    except Exception as e:
        logger.error(f"Error in autonomous_chat: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"❌ **Error**: {str(e)}"
        history.append((message, error_msg))
        return "", history


def reset_conversation():
    """Reset the conversation context."""
    try:
        orchestrator.reset_context("default")
        return None, "✅ Conversation reset. You can start a new query."
    except Exception as e:
        return None, f"❌ Error resetting conversation: {str(e)}"


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

**Features:**
- ✅ Autonomous Query Processing
- ✅ Comparative Analysis
- ✅ Context Tracking
- ✅ Intelligent Drug Name Extraction
"""
        return message
        
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"


# Build Gradio interface
with gr.Blocks(
    title="Regulatory Search Agent - Autonomous",
    theme=gr.themes.Soft()
) as demo:
    
    gr.Markdown("""
    # 🔬 Regulatory Search Agent (Autonomous)
    
    **Ask any question about drug regulatory reviews - the system will automatically:**
    - Extract drug names from your query
    - Search and download relevant documents from regulatory agencies
    - Generate comprehensive answers with comparative analysis
    - Track conversation context across multiple queries
    
    **Example queries:**
    - *"What were the differences in safety issues between FDA and EMA reviews for Tezspire?"*
    - *"Tell me about the efficacy data for Keytruda"*
    - *"Compare the dosage recommendations across agencies for Humira"*
    """)
    
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
                    placeholder="Ask anything about drug regulatory reviews...",
                    lines=2,
                    scale=4
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("Clear Chat")
                reset_btn = gr.Button("Reset Context", variant="secondary")
        
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            
            agencies_checkbox = gr.CheckboxGroup(
                choices=["FDA", "EMA"],
                value=["FDA", "EMA"],
                label="Agencies",
                info="Select agencies to search (default: all)"
            )
            
            model_dropdown = gr.Dropdown(
                choices=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                value="gpt-4",
                label="Model",
                info="Select the OpenAI model"
            )
            
            gr.Markdown("### 💡 How It Works")
            gr.Markdown("""
            1. **Ask your question** - Just type naturally
            2. **System analyzes** - Extracts drug names and intent
            3. **Auto-retrieves** - Downloads documents if needed
            4. **Generates answer** - Comprehensive response with sources
            5. **Comparative analysis** - When multiple agencies selected
            
            The system remembers context, so follow-up questions work seamlessly!
            """)
    
    with gr.Accordion("📊 System Status", open=False):
        status_output = gr.Markdown(value="*Loading status...*")
        refresh_btn = gr.Button("🔄 Refresh Status")
    
    with gr.Accordion("📖 Example Queries", open=False):
        gr.Markdown("""
        **Specific Comparative Queries:**
        - "What were the differences in safety issues and drug dosage between the FDA and EMA reviews for Tezspire?"
        - "Compare the efficacy endpoints used by FDA and EMA for Keytruda approval"
        - "How did the adverse event profiles differ between FDA and EMA reviews for Humira?"
        
        **General Queries:**
        - "What is Keytruda indicated for?"
        - "Tell me about the safety profile of Opdivo"
        - "What were the clinical trial results for Tezspire?"
        
        **Follow-up Queries (after initial query):**
        - "What about the dosing regimen?"
        - "Were there any black box warnings?"
        - "How does this compare to similar drugs?"
        """)
    
    # Event handlers
    submit_btn.click(
        autonomous_chat,
        inputs=[msg, chatbot, agencies_checkbox, model_dropdown],
        outputs=[msg, chatbot]
    )
    
    msg.submit(
        autonomous_chat,
        inputs=[msg, chatbot, agencies_checkbox, model_dropdown],
        outputs=[msg, chatbot]
    )
    
    clear_btn.click(
        lambda: None,
        None,
        chatbot,
        queue=False
    )
    
    reset_btn.click(
        reset_conversation,
        outputs=[chatbot, msg]
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
    logger.info("Starting Autonomous Gradio interface...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
