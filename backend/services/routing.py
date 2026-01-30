"""
Complexity Router
Determines which workflow path to take based on query complexity
"""
import logging
from enum import Enum
from typing import Optional

from models.state import AgentState
from models.schemas import UserProfile
from core.config import settings

logger = logging.getLogger(__name__)


class PathType(str, Enum):
    """Workflow path types"""
    FAST = "FAST"    # Cache only (~50ms)
    SMART = "SMART"  # Agent 1 + 3 + 4 (~500ms)
    DEEP = "DEEP"    # All 5 agents (~2000ms)


class ComplexityRouter:
    """
    Routes queries to appropriate workflow path based on complexity
    
    Complexity factors:
    - Query length and content
    - Financial keywords present
    - User profile completeness
    - Image included
    - Cache availability
    """
    
    def __init__(self):
        self.fast_threshold = settings.complexity_threshold_fast  # 0.3
        self.smart_threshold = settings.complexity_threshold_smart  # 0.7
        
        self.financial_keywords = [
            'afford', 'financing', 'budget', 'credit', 'payment',
            'loan', 'monthly', 'installment', 'debt', 'income',
            'savings', 'price range', 'cheap', 'expensive', 'cost'
        ]
    
    def estimate_complexity(self, state: AgentState) -> float:
        """
        Calculate complexity score (0.0 - 1.0)
        
        Args:
            state: Current agent state
            
        Returns:
            Complexity score between 0.0 and 1.0
        """
        score = 0.0
        query = state.get('query', '').lower()
        user_profile = state.get('user_profile')
        
        # Factor 1: Query length (0-0.1)
        word_count = len(query.split())
        if word_count > 10:
            score += 0.1
        elif word_count > 5:
            score += 0.05
        
        # Factor 2: Financial keywords (0-0.3)
        financial_keyword_count = sum(
            1 for keyword in self.financial_keywords 
            if keyword in query
        )
        if financial_keyword_count > 0:
            score += min(0.3, financial_keyword_count * 0.1)
        
        # Factor 3: User profile completeness (0-0.3)
        if user_profile and self._has_complete_profile(user_profile):
            score += 0.3
        elif user_profile and self._has_partial_profile(user_profile):
            score += 0.15
        
        # Factor 4: Image included (0-0.2)
        if state.get('image_embedding') is not None:
            score += 0.2
        
        # Factor 5: Specific product requirements (0-0.1)
        specific_terms = ['professional', 'gaming', 'student', 'business', 'premium']
        if any(term in query for term in specific_terms):
            score += 0.1
        
        # Ensure score is in valid range
        final_score = min(1.0, max(0.0, score))
        
        logger.info(f"Complexity score: {final_score:.2f} (query: '{query[:50]}...')")
        
        return final_score
    
    def _has_complete_profile(self, profile: UserProfile) -> bool:
        """Check if user profile is complete"""
        return (
            profile.monthly_income > 0 and
            profile.monthly_expenses > 0 and
            profile.savings >= 0 and
            profile.credit_score > 0
        )
    
    def _has_partial_profile(self, profile: UserProfile) -> bool:
        """Check if user profile has some information"""
        return (
            profile.monthly_income > 0 or
            profile.credit_score > 0
        )
    
    def determine_path(
        self, 
        state: AgentState,
        force_path: Optional[str] = None,
        cache_available: bool = False
    ) -> PathType:
        """
        Determine which workflow path to use
        
        Args:
            state: Current agent state
            force_path: Override automatic routing (for testing)
            cache_available: Whether cache hit is available
            
        Returns:
            PathType enum (FAST, SMART, or DEEP)
        """
        # Override if requested
        if force_path:
            logger.info(f"Path forced to: {force_path}")
            return PathType(force_path)
        
        # FAST path: Cache hit + low complexity
        if cache_available:
            complexity = self.estimate_complexity(state)
            if complexity < self.fast_threshold:
                logger.info("Selected FAST path (cache available, low complexity)")
                return PathType.FAST
        
        # Calculate complexity
        complexity = self.estimate_complexity(state)
        
        # Route based on complexity thresholds
        if complexity < self.fast_threshold:
            # Low complexity: No cache, but simple query
            # Still use SMART path for basic recommendations
            logger.info("Selected SMART path (low complexity, no financial analysis needed)")
            return PathType.SMART
        
        elif complexity < self.smart_threshold:
            # Medium complexity: Good recommendations without full financial analysis
            logger.info("Selected SMART path (medium complexity)")
            return PathType.SMART
        
        else:
            # High complexity: Full pipeline with financial analysis
            logger.info("Selected DEEP path (high complexity, full analysis)")
            return PathType.DEEP
    
    def get_path_description(self, path: PathType) -> str:
        """Get human-readable description of path"""
        descriptions = {
            PathType.FAST: "Quick recommendations from cache",
            PathType.SMART: "AI-powered product discovery and ranking",
            PathType.DEEP: "Comprehensive financial analysis with personalized recommendations"
        }
        return descriptions.get(path, "Unknown path")


# Global router instance
complexity_router = ComplexityRouter()
