"""
Conversational context manager for tracking drug, topics, and conversation state.
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationContext:
    """Manages conversation context across multiple queries."""
    
    def __init__(self):
        self.current_drug: Optional[str] = None
        self.agencies: List[str] = ['FDA', 'EMA']  # Default agencies
        self.topics: List[str] = []
        self.documents_indexed: List[str] = []
        self.query_history: List[Dict] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def update_drug(self, drug_name: str):
        """
        Update the current drug being discussed.
        
        Args:
            drug_name: Name of the drug
        """
        if self.current_drug != drug_name:
            logger.info(f"Switching drug context from '{self.current_drug}' to '{drug_name}'")
            self.current_drug = drug_name
            self.topics = []  # Reset topics for new drug
            self.last_updated = datetime.now()
    
    def add_topics(self, topics: List[str]):
        """
        Add topics to the conversation context.
        
        Args:
            topics: List of topics discussed
        """
        for topic in topics:
            if topic not in self.topics:
                self.topics.append(topic)
                logger.info(f"Added topic: {topic}")
        self.last_updated = datetime.now()
    
    def set_agencies(self, agencies: List[str]):
        """
        Set the agencies to search.
        
        Args:
            agencies: List of agency names
        """
        self.agencies = agencies
        logger.info(f"Updated agencies: {', '.join(agencies)}")
        self.last_updated = datetime.now()
    
    def add_document(self, document_path: str):
        """
        Record that a document has been indexed.
        
        Args:
            document_path: Path to the indexed document
        """
        if document_path not in self.documents_indexed:
            self.documents_indexed.append(document_path)
            logger.info(f"Recorded indexed document: {document_path}")
        self.last_updated = datetime.now()
    
    def add_query(self, query: str, response: str, analysis: Dict):
        """
        Add a query to the history.
        
        Args:
            query: User's query
            response: System's response
            analysis: Query analysis results
        """
        self.query_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'analysis': analysis
        })
        self.last_updated = datetime.now()
    
    def has_documents_for_drug(self, drug_name: str) -> bool:
        """
        Check if documents are already indexed for a drug.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            True if documents exist, False otherwise
        """
        if not self.current_drug:
            return False
        
        # Check if current drug matches and documents exist
        return (
            self.current_drug.lower() == drug_name.lower() and 
            len(self.documents_indexed) > 0
        )
    
    def needs_new_documents(self, drug_name: str) -> bool:
        """
        Determine if new documents need to be retrieved.
        
        Args:
            drug_name: Name of the drug in the query
            
        Returns:
            True if new documents needed, False otherwise
        """
        # New documents needed if:
        # 1. No current drug set
        # 2. Different drug mentioned
        # 3. Current drug but no documents indexed
        
        if not self.current_drug:
            return True
        
        if self.current_drug.lower() != drug_name.lower():
            return True
        
        if len(self.documents_indexed) == 0:
            return True
        
        return False
    
    def get_context_summary(self) -> Dict:
        """
        Get a summary of the current context.
        
        Returns:
            Dictionary with context information
        """
        return {
            'current_drug': self.current_drug,
            'agencies': self.agencies,
            'topics': self.topics,
            'documents_indexed': len(self.documents_indexed),
            'queries_asked': len(self.query_history),
            'session_duration': (datetime.now() - self.created_at).total_seconds()
        }
    
    def reset(self):
        """Reset the conversation context."""
        logger.info("Resetting conversation context")
        self.current_drug = None
        self.topics = []
        self.documents_indexed = []
        self.query_history = []
        self.agencies = ['FDA', 'EMA']  # Reset to defaults
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict:
        """
        Convert context to dictionary for passing to query analyzer.
        
        Returns:
            Dictionary representation of context
        """
        return {
            'current_drug': self.current_drug,
            'agencies': self.agencies,
            'topics': self.topics,
            'has_documents': len(self.documents_indexed) > 0
        }


class ContextManager:
    """Manager for conversation contexts (supports multiple sessions)."""
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        self.default_session = "default"
    
    def get_context(self, session_id: str = None) -> ConversationContext:
        """
        Get or create a conversation context for a session.
        
        Args:
            session_id: Session identifier (defaults to "default")
            
        Returns:
            ConversationContext for the session
        """
        if session_id is None:
            session_id = self.default_session
        
        if session_id not in self.contexts:
            logger.info(f"Creating new context for session: {session_id}")
            self.contexts[session_id] = ConversationContext()
        
        return self.contexts[session_id]
    
    def reset_context(self, session_id: str = None):
        """
        Reset a conversation context.
        
        Args:
            session_id: Session identifier (defaults to "default")
        """
        if session_id is None:
            session_id = self.default_session
        
        if session_id in self.contexts:
            self.contexts[session_id].reset()
    
    def delete_context(self, session_id: str):
        """
        Delete a conversation context.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.contexts:
            logger.info(f"Deleting context for session: {session_id}")
            del self.contexts[session_id]
