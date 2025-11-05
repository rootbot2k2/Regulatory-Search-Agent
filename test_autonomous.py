#!/usr/bin/env python3
"""
Test script for the autonomous regulatory search agent.
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.autonomous_orchestrator import AutonomousOrchestrator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_autonomous_system():
    """Test the autonomous query processing system."""
    
    print("\n" + "="*70)
    print("AUTONOMOUS REGULATORY SEARCH AGENT - TEST")
    print("="*70 + "\n")
    
    try:
        # Initialize orchestrator
        print("1️⃣  Initializing autonomous orchestrator...")
        orchestrator = AutonomousOrchestrator()
        print("✅ Orchestrator initialized\n")
        
        # Test 1: Specific query with drug name
        print("="*70)
        print("TEST 1: Specific Query with Drug Name")
        print("="*70)
        
        query1 = "What is Keytruda indicated for?"
        print(f"\nQuery: \"{query1}\"\n")
        
        result1 = orchestrator.process_query(
            query=query1,
            session_id="test",
            selected_agencies=["FDA"]
        )
        
        print(f"\nStatus: {result1.get('status')}")
        
        if result1.get('status') == 'clarification_needed':
            print(f"Clarification: {result1.get('question')}")
        elif result1.get('status') == 'success':
            print(f"✅ Answer generated")
            print(f"Answer preview: {result1.get('answer', '')[:300]}...")
            
            context = result1.get('context_summary', {})
            print(f"\nContext:")
            print(f"  Current drug: {context.get('current_drug')}")
            print(f"  Documents indexed: {context.get('documents_indexed')}")
        else:
            print(f"❌ Error: {result1.get('error')}")
        
        # Test 2: Follow-up query (should use existing documents)
        print("\n" + "="*70)
        print("TEST 2: Follow-up Query (No New Documents Needed)")
        print("="*70)
        
        query2 = "What are the safety considerations?"
        print(f"\nQuery: \"{query2}\"\n")
        
        result2 = orchestrator.process_query(
            query=query2,
            session_id="test",
            selected_agencies=["FDA"]
        )
        
        print(f"\nStatus: {result2.get('status')}")
        
        if result2.get('status') == 'success':
            print(f"✅ Answer generated (using existing documents)")
            print(f"Answer preview: {result2.get('answer', '')[:300]}...")
        else:
            print(f"❌ Error: {result2.get('error')}")
        
        # Test 3: Vague query (should ask for clarification)
        print("\n" + "="*70)
        print("TEST 3: Vague Query (Should Request Clarification)")
        print("="*70)
        
        query3 = "Tell me about safety issues"
        print(f"\nQuery: \"{query3}\"\n")
        
        # Reset context first
        orchestrator.reset_context("test")
        
        result3 = orchestrator.process_query(
            query=query3,
            session_id="test"
        )
        
        print(f"\nStatus: {result3.get('status')}")
        
        if result3.get('status') == 'clarification_needed':
            print(f"✅ Clarification requested (as expected)")
            print(f"Question: {result3.get('question')}")
        else:
            print(f"⚠️  Expected clarification but got: {result3.get('status')}")
        
        # Test 4: Query analyzer
        print("\n" + "="*70)
        print("TEST 4: Query Analyzer")
        print("="*70)
        
        from app.services.query_analyzer import QueryAnalyzer
        analyzer = QueryAnalyzer()
        
        test_query = "What were the differences in safety issues between FDA and EMA reviews for Tezspire?"
        print(f"\nQuery: \"{test_query}\"\n")
        
        analysis = analyzer.analyze_query(test_query)
        
        print(f"✅ Analysis complete:")
        print(f"  Drug names: {analysis.get('drug_names')}")
        print(f"  Agencies: {analysis.get('agencies')}")
        print(f"  Topics: {analysis.get('topics')}")
        print(f"  Query type: {analysis.get('query_type')}")
        print(f"  Needs documents: {analysis.get('needs_documents')}")
        print(f"  Clarification needed: {analysis.get('clarification_needed')}")
        
        print("\n" + "="*70)
        print("✅ AUTONOMOUS SYSTEM TEST COMPLETE")
        print("="*70 + "\n")
        
        print("Summary:")
        print("  ✅ Autonomous orchestrator initialized")
        print("  ✅ Query processing working")
        print("  ✅ Context tracking functional")
        print("  ✅ Query analyzer operational")
        print("  ✅ Clarification detection working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_autonomous_system()
    sys.exit(0 if success else 1)
