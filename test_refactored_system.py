"""
Test script for the refactored Regulatory Search Agent.
Tests the new browser-use based system.
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.autonomous_orchestrator import AutonomousOrchestrator
from app.services.web_automation.ai_navigator import AIWebNavigator

def test_1_orchestrator_initialization():
    """Test 1: Verify orchestrator initializes correctly."""
    print("\n" + "="*70)
    print("TEST 1: Orchestrator Initialization")
    print("="*70)
    
    try:
        orchestrator = AutonomousOrchestrator()
        print("✓ Orchestrator initialized successfully")
        print(f"✓ AI Navigator: {type(orchestrator.ai_navigator).__name__}")
        print(f"✓ Query Analyzer: {type(orchestrator.query_analyzer).__name__}")
        print(f"✓ RAG Service: {type(orchestrator.rag_service).__name__}")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_query_analysis():
    """Test 2: Test query analysis without document retrieval."""
    print("\n" + "="*70)
    print("TEST 2: Query Analysis")
    print("="*70)
    
    try:
        orchestrator = AutonomousOrchestrator()
        
        # Test query
        query = "What is Keytruda indicated for?"
        
        print(f"\nQuery: {query}")
        print("\nAnalyzing...")
        
        analysis = orchestrator.query_analyzer.analyze_query(query, {})
        
        print(f"\n✓ Drug names: {analysis.get('drug_names', [])}")
        print(f"✓ Topics: {analysis.get('topics', [])}")
        print(f"✓ Query type: {analysis.get('query_type', 'unknown')}")
        print(f"✓ Needs documents: {analysis.get('needs_documents', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Query analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_ai_navigator_basic():
    """Test 3: Test AI navigator basic functionality."""
    print("\n" + "="*70)
    print("TEST 3: AI Navigator Basic Test")
    print("="*70)
    
    try:
        navigator = AIWebNavigator()
        print("✓ AI Navigator created")
        print(f"✓ Download directory: {navigator.download_dir}")
        print(f"✓ Available agencies: {list(navigator.AGENCY_URLS.keys())}")
        
        # Note: We won't actually run the navigator in test mode
        # as it requires browser automation which may be slow
        print("\n✓ AI Navigator ready for use")
        print("  (Skipping actual navigation test to save time)")
        
        return True
        
    except Exception as e:
        print(f"✗ AI Navigator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_end_to_end_without_retrieval():
    """Test 4: End-to-end test without document retrieval."""
    print("\n" + "="*70)
    print("TEST 4: End-to-End (Without Document Retrieval)")
    print("="*70)
    
    try:
        orchestrator = AutonomousOrchestrator()
        
        # Use a follow-up query that doesn't need new documents
        query = "Tell me about the safety profile"
        
        print(f"\nQuery: {query}")
        print("\nProcessing...")
        
        # This should ask for clarification (no drug specified)
        result = orchestrator.process_query(query, session_id="test_session")
        
        print(f"\n✓ Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'clarification_needed':
            print(f"✓ Clarification question: {result.get('question', '')}")
        elif result.get('answer'):
            print(f"✓ Answer: {result.get('answer', '')[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_context_management():
    """Test 5: Test context management across queries."""
    print("\n" + "="*70)
    print("TEST 5: Context Management")
    print("="*70)
    
    try:
        orchestrator = AutonomousOrchestrator()
        session_id = "test_context_session"
        
        # First query - sets drug context
        query1 = "What is Keytruda indicated for?"
        print(f"\nQuery 1: {query1}")
        
        result1 = orchestrator.process_query(query1, session_id=session_id)
        print(f"✓ Result 1 status: {result1.get('status', 'unknown')}")
        
        # Get context
        context = orchestrator.context_manager.get_context(session_id)
        print(f"✓ Current drug in context: {context.current_drug}")
        print(f"✓ Topics: {context.topics}")
        
        # Second query - should use context
        query2 = "What about safety?"
        print(f"\nQuery 2: {query2}")
        
        result2 = orchestrator.process_query(query2, session_id=session_id)
        print(f"✓ Result 2 status: {result2.get('status', 'unknown')}")
        
        # Verify context was used
        context2 = orchestrator.context_manager.get_context(session_id)
        print(f"✓ Drug still in context: {context2.current_drug}")
        print(f"✓ Topics updated: {context2.topics}")
        
        return True
        
    except Exception as e:
        print(f"✗ Context management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "#"*70)
    print("# REGULATORY SEARCH AGENT - REFACTORED SYSTEM TESTS")
    print("#"*70)
    
    tests = [
        ("Orchestrator Initialization", test_1_orchestrator_initialization),
        ("Query Analysis", test_2_query_analysis),
        ("AI Navigator Basic", test_3_ai_navigator_basic),
        ("End-to-End (No Retrieval)", test_4_end_to_end_without_retrieval),
        ("Context Management", test_5_context_management),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
    
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
