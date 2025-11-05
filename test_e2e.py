#!/usr/bin/env python3
"""
End-to-end test script for the Regulatory Search Agent.
Tests the complete workflow from document retrieval to question answering.
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.orchestrator import AgenticOrchestrator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_system():
    """Run end-to-end system test."""
    
    print("\n" + "="*70)
    print("REGULATORY SEARCH AGENT - END-TO-END TEST")
    print("="*70 + "\n")
    
    try:
        # Initialize orchestrator
        print("1️⃣  Initializing orchestrator...")
        orchestrator = AgenticOrchestrator()
        print("✅ Orchestrator initialized\n")
        
        # Check system status
        print("2️⃣  Checking system status...")
        status = orchestrator.get_system_status()
        print(f"✅ System status: {status['status']}")
        print(f"   Available agencies: {status['available_agencies']}")
        print(f"   Current vectors in index: {status['vector_store']['total_vectors']}\n")
        
        # Test document retrieval
        print("3️⃣  Testing document retrieval...")
        print("   Drug: Keytruda")
        print("   Agencies: FDA")
        print("   Max docs: 2")
        print("   (This may take 2-3 minutes...)\n")
        
        result = orchestrator.retrieve_and_index(
            drug_name="Keytruda",
            agencies=["FDA"],
            max_docs_per_agency=2
        )
        
        if result['status'] == 'success':
            print(f"✅ Document retrieval successful!")
            print(f"   Agencies searched: {', '.join(result['agencies_searched'])}")
            print(f"   Documents downloaded: {len(result['documents_downloaded'])}")
            print(f"   Documents indexed: {result['documents_indexed']}")
            print(f"   Total vectors: {result['total_vectors_in_index']}")
            
            if result['errors']:
                print(f"   ⚠️  Warnings: {len(result['errors'])}")
                for error in result['errors'][:3]:
                    print(f"      - {error}")
        else:
            print(f"❌ Document retrieval failed: {result.get('error', 'Unknown error')}")
            return False
        
        print()
        
        # Test query if documents were indexed
        if result['documents_indexed'] > 0:
            print("4️⃣  Testing question answering...")
            
            test_questions = [
                "What is Keytruda used for?",
                "What are the main safety considerations for Keytruda?",
            ]
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n   Question {i}: {question}")
                
                answer_result = orchestrator.query(
                    question=question,
                    k=3
                )
                
                if answer_result['status'] == 'success':
                    print(f"   ✅ Answer generated ({len(answer_result['answer'])} characters)")
                    print(f"   Sources: {answer_result['num_chunks_retrieved']} chunks")
                    print(f"   Model: {answer_result['model_used']}")
                    print(f"\n   Answer preview:")
                    print(f"   {answer_result['answer'][:200]}...")
                else:
                    print(f"   ❌ Query failed: {answer_result.get('error', 'Unknown error')}")
        else:
            print("4️⃣  Skipping question answering (no documents indexed)")
        
        print("\n" + "="*70)
        print("✅ END-TO-END TEST COMPLETE")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
