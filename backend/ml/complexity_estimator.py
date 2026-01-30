"""
Complexity Estimator for Query Routing
Determines whether a search query should use FAST/SMART/DEEP path

Routing Logic:
- FAST (score < 0.3): Cache hit, no computation needed
- SMART (0.3 ≤ score < 0.7): Agent 1 only, simple ranking
- DEEP (score ≥ 0.7): Full 5-agent pipeline with financial analysis
"""
import re
import logging
from typing import Optional, Dict, Any
from models.schemas import UserProfile

logger = logging.getLogger(__name__)


class ComplexityEstimator:
    """
    Estimates query complexity to determine optimal execution path

    Complexity Score Components:
    - Query length (0.1 - 0.3)
    - Financial keywords (0.0 - 0.9)
    - Price constraints (0.0 - 0.2)
    - User profile completeness (0.0 - 0.2)
    - Multimodal input (0.0 - 0.1)

    Examples:
        >>> estimator = ComplexityEstimator()
        >>> estimator.estimate("laptops", None, False)
        {'level': 'FAST', 'score': 0.1, 'reasoning': '...'}

        >>> estimator.estimate("laptop under $1000", None, False)
        {'level': 'SMART', 'score': 0.5, 'reasoning': '...'}

        >>> user = UserProfile(user_id="u1", monthly_income=5000, credit_score=720)
        >>> estimator.estimate("laptop with financing", user, False)
        {'level': 'DEEP', 'score': 0.8, 'reasoning': '...'}
    """

    # Financial analysis keywords
    FINANCIAL_KEYWORDS = [
        "afford", "affordable", "budget", "financing", "finance",
        "payment", "monthly", "credit", "debt", "income", "loan",
        "interest", "apr", "down payment", "installment", "pay over time"
    ]

    # Price constraint keywords
    PRICE_KEYWORDS = ["$", "under", "below", "less than", "max", "maximum", "up to"]

    def __init__(self):
        """Initialize complexity estimator"""
        self.financial_pattern = re.compile(
            r'\b(' + '|'.join(self.FINANCIAL_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self.price_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in self.PRICE_KEYWORDS if k != '$') + r')\b|\$',
            re.IGNORECASE
        )

    def estimate(
        self,
        query: str,
        user_profile: Optional[UserProfile] = None,
        has_image: bool = False
    ) -> Dict[str, Any]:
        """
        Estimate query complexity and determine routing path

        Args:
            query: Search query string
            user_profile: Optional user profile with financial data
            has_image: Whether query includes image upload

        Returns:
            Dict with:
                - level: "FAST" | "SMART" | "DEEP"
                - score: float (0.0 - 1.0+)
                - reasoning: str explaining the score
                - factors: dict of individual factor contributions
        """
        if not query or not query.strip():
            logger.warning("Empty query provided, defaulting to FAST path")
            return {
                'level': 'FAST',
                'score': 0.0,
                'reasoning': 'Empty query defaults to FAST path',
                'factors': {}
            }

        query = query.strip()
        complexity_score = 0.0
        factors = {}
        reasoning_parts = []

        # Factor 1: Query length analysis
        word_count = len(query.split())
        if word_count <= 2:
            length_score = 0.1
            reasoning_parts.append(f"Simple query ({word_count} words) +0.1")
        elif word_count > 10:
            length_score = 0.3
            reasoning_parts.append(f"Complex query ({word_count} words) +0.3")
        else:
            length_score = 0.15
            reasoning_parts.append(f"Medium query ({word_count} words) +0.15")

        complexity_score += length_score
        factors['query_length'] = length_score

        # Factor 2: Financial keywords detection
        financial_matches = self.financial_pattern.findall(query)
        financial_count = len(financial_matches)

        if financial_count > 0:
            # Cap at 0.9 (3 keywords = 0.9)
            financial_score = min(0.3 * financial_count, 0.9)
            complexity_score += financial_score
            factors['financial_keywords'] = financial_score
            reasoning_parts.append(
                f"Financial keywords detected ({financial_count}: {', '.join(financial_matches)}) +{financial_score:.1f}"
            )
        else:
            factors['financial_keywords'] = 0.0

        # Factor 3: Price constraint detection
        price_matches = self.price_pattern.findall(query)
        if price_matches:
            price_score = 0.2
            complexity_score += price_score
            factors['price_constraints'] = price_score
            reasoning_parts.append(f"Price constraints detected +0.2")
        else:
            factors['price_constraints'] = 0.0

        # Factor 4: User profile completeness
        profile_score = 0.0
        if user_profile:
            has_income = hasattr(user_profile, 'monthly_income') and user_profile.monthly_income is not None
            has_credit = hasattr(user_profile, 'credit_score') and user_profile.credit_score is not None

            if has_income and has_credit:
                profile_score = 0.2
                reasoning_parts.append(f"Complete financial profile (income + credit) +0.2")
            elif has_income or has_credit:
                profile_score = 0.1
                reasoning_parts.append(f"Partial financial profile +0.1")

        complexity_score += profile_score
        factors['user_profile'] = profile_score

        # Factor 5: Multimodal input
        if has_image:
            multimodal_score = 0.1
            complexity_score += multimodal_score
            factors['multimodal'] = multimodal_score
            reasoning_parts.append("Image upload detected +0.1")
        else:
            factors['multimodal'] = 0.0

        # Determine routing level based on score
        if complexity_score < 0.3:
            level = "FAST"
            path_reasoning = "Low complexity - FAST path (cache check only)"
        elif complexity_score < 0.7:
            level = "SMART"
            path_reasoning = "Medium complexity - SMART path (Agent 1 + simple ranking)"
        else:
            level = "DEEP"
            path_reasoning = "High complexity - DEEP path (full 5-agent pipeline)"

        reasoning = f"{path_reasoning}. " + "; ".join(reasoning_parts)

        result = {
            'level': level,
            'score': round(complexity_score, 3),
            'reasoning': reasoning,
            'factors': factors
        }

        logger.info(
            f"Complexity estimation: query='{query[:50]}...' → {level} "
            f"(score={complexity_score:.3f})"
        )

        return result

    def get_routing_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable routing summary

        Args:
            result: Output from estimate() method

        Returns:
            Formatted summary string
        """
        level = result['level']
        score = result['score']

        if level == 'FAST':
            return f"⚡ FAST PATH (score={score:.2f}): Cache check, <100ms target"
        elif level == 'SMART':
            return f"🎯 SMART PATH (score={score:.2f}): Agent 1 only, 300-800ms target"
        else:
            return f"🔬 DEEP PATH (score={score:.2f}): Full pipeline, 1500-3000ms target"


# Global instance for easy import
complexity_estimator = ComplexityEstimator()
