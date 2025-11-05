# Regulatory Search Agent

An intelligent AI agent for automated retrieval, indexing, and analysis of drug regulatory documents from major international health agencies.

## 🎯 Overview

The Regulatory Search Agent is a sophisticated system that combines web automation, natural language processing, and retrieval-augmented generation (RAG) to provide researchers and regulatory professionals with instant access to regulatory information. The system autonomously navigates regulatory agency websites, downloads relevant documents, and enables natural language queries through a chat interface.

## 🌐 Supported Agencies

- **FDA** (Food and Drug Administration - USA)
- **EMA** (European Medicines Agency - EU)
- **Health Canada** (Canada)
- **TGA** (Therapeutic Goods Administration - Australia)
- **Swissmedic** (Swiss Agency for Therapeutic Products - Switzerland)
- **NHRA** (National Health Regulatory Authority - Bahrain)

## ✨ Key Features

- **Autonomous Web Browsing**: Automatically navigates complex regulatory websites and retrieves documents
- **On-Demand Retrieval**: Fetches documents based on specific drug names or topics
- **Local Vector Indexing**: Uses FAISS for efficient similarity search without external dependencies
- **RAG-Powered Q&A**: Leverages GPT-4 to answer questions grounded in retrieved documents
- **Multi-Model Support**: Choose between GPT-4, GPT-4-turbo, or GPT-3.5-turbo
- **User-Friendly Interface**: Simple chat interface built with Streamlit or Gradio
- **Source Citations**: All answers include references to source documents

## 🏗️ Architecture

The system is built with a modular, service-oriented architecture:

```
┌─────────────────────┐
│   User Interface    │
│   (Streamlit/Gradio)│
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Agentic Core /     │
│    Orchestrator     │
└─────┬───────┬───────┘
      │       │
      │       └──────────────┐
      │                      │
┌─────▼──────────┐   ┌──────▼────────┐
│ Web Automation │   │  RAG & Q&A    │
│     Module     │   │    Module     │
└─────┬──────────┘   └──────┬────────┘
      │                     │
┌─────▼──────────┐   ┌──────▼────────┐
│   Document     │   │  FAISS Vector │
│   Processing   │───▶│     Store     │
└────────────────┘   └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Google Chrome and ChromeDriver
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Regulatory-Search-Agent.git
cd Regulatory-Search-Agent
```

2. Install dependencies:
```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.template .env
# Edit .env and add your OPENAI_API_KEY
```

4. Start the backend:
```bash
python main.py
```

5. Start the GUI (in a new terminal):
```bash
streamlit run app/gui/chat_interface.py
```

## 📖 Usage

### Retrieving Documents

1. Open the GUI at `http://localhost:8501`
2. In the sidebar, enter a drug name (e.g., "Keytruda")
3. Select the agencies to search
4. Click "Retrieve & Index Documents"
5. Wait for the system to download and index the documents

### Asking Questions

1. Type your question in the chat input
2. The system will:
   - Search the vector store for relevant context
   - Generate an answer using GPT-4
   - Provide source citations
3. View sources by expanding the "View Sources" section

### Example Questions

- "What are the safety considerations for Keytruda?"
- "Compare the FDA and EMA approval processes for this drug"
- "What adverse events were reported during clinical trials?"
- "What is the recommended dosage according to regulatory documents?"

## 🛠️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
EMBEDDING_MODEL=text-embedding-ada-002
CHAT_MODEL=gpt-4

# FAISS Configuration
FAISS_INDEX_PATH=./data/faiss_index/regulatory_docs.index
FAISS_METADATA_PATH=./data/faiss_index/metadata.json

# Document Storage
DOWNLOAD_DIR=./data/downloaded_docs/

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Model Selection

The system supports multiple OpenAI models:

- **gpt-4**: Best quality, higher cost (recommended for production)
- **gpt-4-turbo**: Faster, cost-effective alternative
- **gpt-3.5-turbo**: Fastest, most economical option

## 📁 Project Structure

```
Regulatory-Search-Agent/
├── app/
│   ├── api/
│   │   └── endpoints.py
│   ├── core/
│   │   ├── config.py
│   │   └── orchestrator.py
│   ├── services/
│   │   ├── document_processing.py
│   │   ├── rag_service.py
│   │   ├── vector_store.py
│   │   └── web_automation/
│   │       ├── base_scraper.py
│   │       ├── fda_scraper.py
│   │       ├── ema_scraper.py
│   │       └── health_canada_scraper.py
│   └── gui/
│       └── chat_interface.py
├── data/
│   ├── downloaded_docs/
│   └── faiss_index/
├── .env
├── .env.template
├── main.py
└── README.md
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Test individual components:

```bash
# Test document processing
python tests/test_document_processing.py

# Test vector store
python tests/test_vector_store.py

# Test scrapers
python tests/test_scrapers.py
```

## 📊 Performance Considerations

### FAISS Index Management

- **Index Type**: Uses `IndexFlatL2` for accuracy; consider `IndexIVFFlat` for larger datasets
- **Persistence**: Index is saved to disk after each update
- **Incremental Indexing**: New documents are added without rebuilding the entire index

### Cost Management

- **Embedding Caching**: Embeddings are cached to avoid regeneration
- **Model Selection**: Use `gpt-3.5-turbo` for cost-effective queries
- **Chunk Optimization**: Configurable chunk size to balance context and cost

## 🔒 Security

- API keys are stored in environment variables
- `.env` file is excluded from version control
- Input validation prevents injection attacks
- HTTPS recommended for production deployments

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t regulatory-search-agent .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  regulatory-search-agent
```

### Cloud Deployment

The application can be deployed to:
- AWS (EC2, ECS, or Lambda)
- Google Cloud Platform (Cloud Run, Compute Engine)
- Azure (App Service, Container Instances)

## 🔮 Future Enhancements

- [ ] Advanced query understanding with entity extraction
- [ ] Multi-document synthesis and comparative analysis
- [ ] Automatic document update monitoring
- [ ] User authentication and personalization
- [ ] Support for additional regulatory agencies
- [ ] Migration to scalable vector database (Pinecone, Weaviate)
- [ ] Real-time document processing pipeline
- [ ] Advanced analytics and reporting dashboard

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Support

For questions, issues, or feature requests, please open an issue on GitHub.

## 🙏 Acknowledgments

- Inspired by the AgentForge project
- Built with OpenAI's GPT-4 and embedding models
- Uses FAISS for efficient vector search
- Web automation powered by Selenium

---

**Built with ❤️ by the Regulatory AI Team**
