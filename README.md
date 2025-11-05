# 🔬 Regulatory Search Agent (Autonomous)

An intelligent AI system for automated retrieval and analysis of drug regulatory documents from FDA, EMA, and other international regulatory agencies.

## ✨ Key Features

### 🤖 Fully Autonomous Operation
- **Automatic Drug Name Extraction**: Just ask naturally - the system extracts drug names from your queries
- **Intelligent Document Retrieval**: Automatically searches and downloads relevant regulatory documents
- **Smart Caching**: Avoids re-downloading documents for follow-up questions
- **Clarification Requests**: Asks for more information when queries are vague

### 📊 Comparative Analysis
- **Multi-Agency Synthesis**: Compare findings across FDA, EMA, and other agencies
- **Side-by-Side Analysis**: Identify similarities and differences in regulatory reviews
- **Integrated Synthesis**: Get comprehensive answers based on totality of evidence

### 💬 Conversational Intelligence
- **Context Tracking**: Remembers the current drug and topics across multiple queries
- **Follow-up Questions**: Ask related questions without repeating drug names
- **Topic Detection**: Automatically identifies safety, efficacy, dosage, and other topics

### 🎯 RAG-Powered Q&A
- **GPT-4 Integration**: Generates expert-level answers grounded in regulatory documents
- **Source Citations**: All answers include references to specific documents
- **FAISS Vector Store**: Fast, local similarity search with no external dependencies

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/rootbot2k2/Regulatory-Search-Agent.git
cd Regulatory-Search-Agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
nano .env  # Add your OpenAI API key
```

### Run the Application

**Autonomous Interface (Recommended)**
```bash
python3 run_autonomous.py
```

Then open **http://localhost:7860** in your browser.

**Original Manual Interface**
```bash
python3 run_gui.py
```

**API Server**
```bash
python3 main.py
```

## 💡 Usage Examples

### Example 1: Comparative Query
```
You: "What were the differences in safety issues and drug dosage between 
      the FDA and EMA reviews for Tezspire?"

System:
1. Extracts drug name: "Tezspire"
2. Identifies agencies: FDA, EMA
3. Searches and downloads regulatory documents
4. Generates comprehensive comparative analysis
```

### Example 2: Simple Query
```
You: "What is Keytruda indicated for?"

System:
1. Extracts drug name: "Keytruda"
2. Downloads FDA and EMA approval documents
3. Generates answer with specific indications
```

### Example 3: Follow-up Question
```
You: "What about the safety profile?"

System:
1. Uses context (still discussing Keytruda)
2. Retrieves relevant sections from already-indexed documents
3. Generates answer without re-downloading
```

### Example 4: Vague Query
```
You: "Tell me about safety issues"

System: "Which drug would you like me to analyze? I can search FDA, 
         EMA, and other regulatory agencies."
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Autonomous Gradio GUI                      │
│  • Natural language queries                             │
│  • Agency selection (FDA, EMA, etc.)                    │
│  • Model selection (GPT-4, GPT-3.5-turbo)              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Autonomous Orchestrator                        │
│  • Query analysis & drug name extraction                │
│  • Context management                                   │
│  • Workflow automation                                  │
└─────┬──────────┬──────────┬──────────┬─────────────────┘
      │          │          │          │
┌─────▼────┐ ┌──▼────┐ ┌───▼────┐ ┌───▼──────────┐
│  Query   │ │Context│ │  Web   │ │ Comparative  │
│ Analyzer │ │Manager│ │Scraping│ │  Analysis    │
└──────────┘ └───────┘ └────────┘ └──────────────┘
      │          │          │          │
      └──────────┴──────────┴──────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              RAG & Vector Store                         │
│  • FAISS similarity search                              │
│  • OpenAI embeddings                                    │
│  • GPT-4 answer generation                              │
└─────────────────────────────────────────────────────────┘
```

## 📋 Supported Agencies

- ✅ **FDA** (Food and Drug Administration - USA)
- ✅ **EMA** (European Medicines Agency - EU)
- 🔄 **Health Canada** (ready for implementation)
- 🔄 **TGA** (Australia - ready for implementation)
- 🔄 **Swissmedic** (Switzerland - ready for implementation)
- 🔄 **NHRA** (Bahrain - ready for implementation)

## 🧪 Testing

### Run Autonomous System Test
```bash
python3 test_autonomous.py
```

This tests:
- Query analysis and drug name extraction
- Context tracking across queries
- Clarification detection
- Autonomous document retrieval
- Answer generation

### Run Simple Pipeline Test
```bash
python3 test_simple.py
```

This tests the core RAG pipeline with a sample document.

## 📊 Test Results

```
✅ Query Analysis: Correctly extracted "Tezspire" from complex query
✅ Agency Detection: Identified FDA and EMA from query
✅ Topic Extraction: Detected safety, comparative analysis
✅ Context Tracking: Remembered drug across multiple queries
✅ Clarification: Asked for drug name when query was vague
✅ Answer Generation: Generated comprehensive responses with GPT-4
```

## ⚙️ Configuration

### Environment Variables (.env)

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

### Model Options

- **gpt-4**: Best quality, most accurate (recommended)
- **gpt-4-turbo**: Faster, cost-effective
- **gpt-3.5-turbo**: Most economical

## 🔧 Advanced Features

### Query Analyzer
Powered by GPT-4 to extract:
- Drug names (brand and generic)
- Regulatory agencies mentioned
- Topics (safety, efficacy, dosage, etc.)
- Query intent and type
- Need for clarification

### Context Manager
Tracks across conversation:
- Current drug being discussed
- Selected agencies
- Topics covered
- Documents indexed
- Query history

### Comparative Analysis Service
Generates structured comparisons:
1. Individual agency summaries
2. Similarities across agencies
3. Differences and discrepancies
4. Integrated synthesis
5. Key takeaways

## 📈 Performance

- **Query Analysis**: ~2-3 seconds
- **Document Download**: 30-60 seconds per document
- **Embedding Generation**: 0.5-1 second per chunk
- **Answer Generation**: 3-7 seconds
- **Comparative Analysis**: 5-10 seconds

## 💰 Cost Estimates (OpenAI API)

- **Query Analysis**: ~$0.01 per query
- **Embeddings**: ~$0.0001 per 1,000 tokens
- **GPT-4 Answer**: ~$0.03-0.06 per query
- **Typical Session**: $1-3 for 10-20 queries with document retrieval

## 🔒 Security

- ✅ API keys stored in .env (not committed to git)
- ✅ All data stored locally
- ✅ No external data transmission except to OpenAI
- ✅ Input validation on all user inputs
- ✅ Secure document handling

## 🐛 Troubleshooting

### ChromeDriver Issues
```bash
# Clear webdriver cache
rm -rf ~/.wdm/
```

### API Key Errors
1. Verify key in `.env` file
2. Check OpenAI account has credits
3. Ensure `load_dotenv(override=True)` in config.py

### No Documents Found
1. Check drug name spelling
2. Try alternative names (brand vs generic)
3. Verify agency website is accessible
4. Check logs for specific errors

## 📚 Documentation

- **README_IMPLEMENTATION.md**: Detailed implementation guide
- **REGULATORY_SEARCH_AGENT_ARCHITECTURE.md**: System architecture
- **IMPLEMENTATION_GUIDE.md**: Step-by-step development guide
- **WEB_AUTOMATION_GUIDE.md**: Web scraping documentation
- **GUI_IMPLEMENTATION.md**: GUI development guide

## 🚧 Known Limitations

1. **Web Scraping**: Regulatory websites may change structure
2. **PDF Parsing**: Some complex PDFs may not parse correctly
3. **Rate Limiting**: Respect agency website rate limits
4. **API Costs**: OpenAI usage incurs costs

## 🔮 Future Enhancements

- [ ] Add remaining agency scrapers
- [ ] Implement document update monitoring
- [ ] Add user authentication
- [ ] Create analytics dashboard
- [ ] Migrate to scalable vector database
- [ ] Add multi-language support
- [ ] Implement advanced entity extraction

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **OpenAI GPT-4** for intelligent analysis and generation
- **FAISS** by Facebook Research for vector similarity search
- **Selenium** for web automation
- **Gradio** for rapid GUI development
- **FastAPI** for high-performance API backend

## 📞 Support

- **GitHub**: https://github.com/rootbot2k2/Regulatory-Search-Agent
- **Issues**: https://github.com/rootbot2k2/Regulatory-Search-Agent/issues

---

**Built with ❤️ for the regulatory affairs community**

*Autonomous, intelligent, and ready to help you navigate the complex world of drug regulation.*
