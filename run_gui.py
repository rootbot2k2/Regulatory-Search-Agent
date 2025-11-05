#!/usr/bin/env python3
"""
Simple launcher for the Regulatory Search Agent GUI.
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.gui.gradio_interface import demo

if __name__ == "__main__":
    print("🚀 Starting Regulatory Search Agent...")
    print("📍 Access the interface at: http://localhost:7860")
    print("⏹️  Press Ctrl+C to stop\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
