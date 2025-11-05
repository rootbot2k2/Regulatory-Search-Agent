"""
Comparative analysis service for synthesizing findings across multiple agencies.
"""
from typing import Dict, List
from openai import OpenAI
import logging

from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComparativeAnalysisService:
    """Service for generating comparative analyses across regulatory agencies."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url='https://api.openai.com/v1'
        )
    
    def generate_comparative_analysis(
        self,
        query: str,
        contexts: List[Dict],
        agencies: List[str],
        model: str = None
    ) -> Dict:
        """
        Generate a comparative analysis across multiple agencies.
        
        Args:
            query: User's query
            contexts: List of context chunks from different agencies
            agencies: List of agencies being compared
            model: OpenAI model to use
            
        Returns:
            Dictionary with comparative analysis
        """
        try:
            if model is None:
                model = self.settings.chat_model
            
            logger.info(f"Generating comparative analysis across {len(agencies)} agencies")
            
            # Organize contexts by agency
            agency_contexts = self._organize_by_agency(contexts)
            
            # Build comparative prompt
            prompt = self._build_comparative_prompt(query, agency_contexts, agencies)
            
            # Generate analysis
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert regulatory affairs analyst specializing in comparative analysis across international regulatory agencies (FDA, EMA, Health Canada, TGA, etc.).

Your task is to:
1. Summarize findings from each agency separately
2. Identify key similarities across agencies
3. Highlight important differences or discrepancies
4. Provide an integrated synthesis
5. Note any gaps or areas where agencies diverge

Be precise, cite specific documents, and maintain scientific rigor."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            
            logger.info(f"✓ Generated comparative analysis ({len(analysis)} characters)")
            
            return {
                'status': 'success',
                'analysis': analysis,
                'agencies_compared': agencies,
                'num_contexts': len(contexts),
                'model_used': model
            }
            
        except Exception as e:
            logger.error(f"Error generating comparative analysis: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'analysis': f"Error generating comparative analysis: {str(e)}"
            }
    
    def _organize_by_agency(self, contexts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Organize context chunks by agency.
        
        Args:
            contexts: List of context chunks
            
        Returns:
            Dictionary mapping agency names to their contexts
        """
        agency_contexts = {}
        
        for context in contexts:
            # Extract agency from document name or metadata
            agency = self._extract_agency(context)
            
            if agency not in agency_contexts:
                agency_contexts[agency] = []
            
            agency_contexts[agency].append(context)
        
        return agency_contexts
    
    def _extract_agency(self, context: Dict) -> str:
        """
        Extract agency name from context metadata.
        
        Args:
            context: Context chunk with metadata
            
        Returns:
            Agency name
        """
        # Check metadata for agency
        if 'agency' in context:
            return context['agency']
        
        # Try to extract from document name
        doc_name = context.get('document', '').upper()
        
        if 'FDA' in doc_name:
            return 'FDA'
        elif 'EMA' in doc_name or 'EPAR' in doc_name or 'CHMP' in doc_name:
            return 'EMA'
        elif 'HEALTH CANADA' in doc_name or 'HPFB' in doc_name:
            return 'Health Canada'
        elif 'TGA' in doc_name:
            return 'TGA'
        elif 'SWISSMEDIC' in doc_name:
            return 'Swissmedic'
        elif 'NHRA' in doc_name:
            return 'NHRA'
        
        return 'Unknown'
    
    def _build_comparative_prompt(
        self,
        query: str,
        agency_contexts: Dict[str, List[Dict]],
        agencies: List[str]
    ) -> str:
        """
        Build the prompt for comparative analysis.
        
        Args:
            query: User's query
            agency_contexts: Contexts organized by agency
            agencies: List of agencies
            
        Returns:
            Formatted prompt
        """
        prompt = f"**User Question:** {query}\n\n"
        prompt += "**Regulatory Documents by Agency:**\n\n"
        
        for agency in agencies:
            if agency in agency_contexts:
                prompt += f"### {agency} Documents:\n\n"
                
                for i, context in enumerate(agency_contexts[agency][:5], 1):  # Limit to 5 per agency
                    doc_name = context.get('document', 'Unknown')
                    text = context.get('text', '')
                    
                    prompt += f"**{agency} Document {i}:** {doc_name}\n"
                    prompt += f"```\n{text[:1000]}...\n```\n\n"
            else:
                prompt += f"### {agency} Documents:\n\n"
                prompt += "*No documents available from this agency.*\n\n"
        
        prompt += """
**Instructions:**

Please provide a comprehensive comparative analysis with the following structure:

1. **Individual Agency Summaries:**
   - Summarize key findings from each agency separately
   - Include specific data points, conclusions, and recommendations

2. **Similarities Across Agencies:**
   - Identify areas of consensus
   - Note common findings or conclusions

3. **Differences and Discrepancies:**
   - Highlight where agencies diverge
   - Explain potential reasons for differences
   - Note any conflicting data or conclusions

4. **Integrated Synthesis:**
   - Provide an overall assessment based on the totality of evidence
   - Reconcile differences where possible
   - Identify the most reliable or comprehensive findings

5. **Key Takeaways:**
   - Summarize the most important points
   - Note any gaps in the available information

Use specific citations from the documents provided.
"""
        
        return prompt
