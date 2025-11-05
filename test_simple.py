#!/usr/bin/env python3
"""
Simple test with a sample PDF document.
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_processing import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_pdf():
    """Create a sample regulatory document PDF."""
    pdf_path = "./data/downloaded_docs/sample_keytruda_document.pdf"
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Add content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "KEYTRUDA (pembrolizumab)")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 140, "Regulatory Review Document")
    
    c.setFont("Helvetica", 11)
    y = height - 180
    
    content = [
        "INDICATION:",
        "KEYTRUDA is indicated for the treatment of patients with unresectable or metastatic",
        "melanoma and disease progression following ipilimumab and, if BRAF V600 mutation",
        "positive, a BRAF inhibitor.",
        "",
        "MECHANISM OF ACTION:",
        "Pembrolizumab is a humanized monoclonal antibody that blocks the interaction between",
        "PD-1 and its ligands, PD-L1 and PD-L2. This releases PD-1 pathway-mediated inhibition",
        "of the immune response, including the anti-tumor immune response.",
        "",
        "SAFETY CONSIDERATIONS:",
        "The most common adverse reactions (reported in ≥20% of patients) were fatigue,",
        "cough, nausea, pruritus, rash, decreased appetite, constipation, arthralgia, and diarrhea.",
        "",
        "Immune-mediated adverse reactions can occur, including pneumonitis, colitis, hepatitis,",
        "endocrinopathies, and nephritis. Monitor patients for signs and symptoms of immune-mediated",
        "adverse reactions.",
        "",
        "CLINICAL EFFICACY:",
        "In clinical trials, KEYTRUDA demonstrated significant improvement in overall survival",
        "and progression-free survival compared to chemotherapy in patients with advanced melanoma.",
        "The objective response rate was approximately 33% with a median duration of response",
        "not reached at the time of analysis.",
        "",
        "DOSAGE AND ADMINISTRATION:",
        "The recommended dose of KEYTRUDA is 200 mg administered as an intravenous infusion",
        "over 30 minutes every 3 weeks until disease progression or unacceptable toxicity.",
    ]
    
    for line in content:
        c.drawString(100, y, line)
        y -= 15
        if y < 100:  # New page if needed
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 100
    
    c.save()
    logger.info(f"✓ Created sample PDF: {pdf_path}")
    return pdf_path


def test_pipeline():
    """Test the complete pipeline with sample document."""
    
    print("\n" + "="*70)
    print("SIMPLE PIPELINE TEST")
    print("="*70 + "\n")
    
    try:
        # Create sample PDF
        print("1️⃣  Creating sample regulatory document...")
        pdf_path = create_sample_pdf()
        print(f"✅ Sample PDF created\n")
        
        # Test document processing
        print("2️⃣  Testing document processing...")
        processor = DocumentProcessor()
        chunks, metadata = processor.process_document(pdf_path, chunk_size=500, overlap=50)
        print(f"✅ Document processed: {len(chunks)} chunks created\n")
        
        # Test vector store
        print("3️⃣  Testing vector indexing...")
        vector_store = VectorStoreService()
        vector_store.add_documents(chunks, metadata)
        stats = vector_store.get_stats()
        print(f"✅ Document indexed: {stats['total_vectors']} vectors\n")
        
        # Test RAG
        print("4️⃣  Testing question answering...")
        rag_service = RAGService()
        
        test_questions = [
            "What is Keytruda indicated for?",
            "What are the safety considerations for Keytruda?",
            "What is the recommended dosage?",
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n   Question {i}: {question}")
            result = rag_service.generate_answer(question, k=3)
            
            if result['status'] == 'success':
                print(f"   ✅ Answer generated")
                print(f"   Model: {result['model_used']}")
                print(f"   Chunks: {result['num_chunks_retrieved']}")
                print(f"\n   Answer:")
                print(f"   {result['answer'][:300]}...")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*70)
        print("✅ SIMPLE PIPELINE TEST COMPLETE")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
