"""
Intelligent query analyzer for extracting drug names and intent from user queries.
"""
from typing import Dict, List, Optional
from openai import OpenAI
import logging
import json

from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes user queries to extract drug names, agencies, and intent."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url='https://api.openai.com/v1'
        )
    
    def analyze_query(self, query: str, conversation_context: Optional[Dict] = None) -> Dict:
        """
        Analyze a user query to extract key information.
        
        Args:
            query: User's query
            conversation_context: Previous conversation context
            
        Returns:
            Dictionary with extracted information:
            {
                'drug_names': List[str],
                'agencies': List[str],
                'needs_documents': bool,
                'query_type': str,  # 'specific', 'vague', 'follow_up'
                'clarification_needed': bool,
                'clarification_question': str,
                'topics': List[str]  # safety, efficacy, dosage, etc.
            }
        """
        try:
            logger.info(f"Analyzing query: {query[:100]}...")
            
            # Build context for GPT
            context_info = ""
            if conversation_context and conversation_context.get('current_drug'):
                context_info = f"\n\nCurrent conversation context:\n- Drug being discussed: {conversation_context['current_drug']}\n- Topics covered: {', '.join(conversation_context.get('topics', []))}"
            
            # Create analysis prompt
            prompt = f"""You are an expert regulatory affairs analyst. Analyze the following user query and extract key information.

User Query: "{query}"{context_info}

Extract and return the following information in JSON format:
{{
    "drug_names": ["list of drug names mentioned (brand or generic)"],
    "agencies": ["list of regulatory agencies mentioned (FDA, EMA, Health Canada, TGA, Swissmedic, NHRA)"],
    "needs_documents": true/false (whether new documents need to be retrieved),
    "query_type": "specific/vague/follow_up",
    "clarification_needed": true/false,
    "clarification_question": "question to ask user if clarification needed",
    "topics": ["list of topics: safety, efficacy, dosage, approval, mechanism, indications, adverse_events, clinical_trials, comparative"]
}}

Rules:
1. If no drug name is mentioned and no context exists, set query_type to "vague" and clarification_needed to true
2. If drug name is in context but not in query, use context drug and set query_type to "follow_up"
3. If query asks for comparison between agencies, include those agencies in the list
4. needs_documents is true only if:
   - A new drug is mentioned (not in context)
   - User explicitly asks for "deep research" or "additional documents"
   - Query type is "specific" with a new drug
5. If agencies are not mentioned, return empty list (system will use defaults)
6. Extract all relevant topics from the query

Return ONLY valid JSON, no additional text."""

            # Call GPT-4 for analysis
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a precise JSON extraction system. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if analysis_text.startswith("```"):
                analysis_text = analysis_text.split("```")[1]
                if analysis_text.startswith("json"):
                    analysis_text = analysis_text[4:]
                analysis_text = analysis_text.strip()
            
            analysis = json.loads(analysis_text)
            
            logger.info(f"✓ Query analysis complete: {analysis}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from GPT response: {str(e)}")
            logger.error(f"Response text: {analysis_text}")
            # Return safe default
            return {
                'drug_names': [],
                'agencies': [],
                'needs_documents': False,
                'query_type': 'vague',
                'clarification_needed': True,
                'clarification_question': "I couldn't understand your query. Could you please specify which drug you'd like to know about?",
                'topics': []
            }
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                'drug_names': [],
                'agencies': [],
                'needs_documents': False,
                'query_type': 'vague',
                'clarification_needed': True,
                'clarification_question': "I encountered an error. Could you please rephrase your question?",
                'topics': []
            }
    
    def extract_drug_name_simple(self, query: str) -> Optional[str]:
        """
        Simple fallback method to extract drug name from query.
        
        Args:
            query: User's query
            
        Returns:
            Extracted drug name or None
        """
        # Common patterns
        patterns = [
            "about ",
            "for ",
            "regarding ",
            "concerning ",
        ]
        
        query_lower = query.lower()
        
        for pattern in patterns:
            if pattern in query_lower:
                # Extract text after pattern
                parts = query_lower.split(pattern)
                if len(parts) > 1:
                    # Get first word after pattern
                    words = parts[1].split()
                    if words:
                        return words[0].strip('.,?!').title()
        
        return None
