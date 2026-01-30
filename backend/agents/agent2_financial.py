"""
Agent 2: Financial Analyzer
Evaluates affordability of candidate products using RAG-enhanced financial rules
"""
from typing import Dict, Any, List, Union
import logging

# Optional imports for type hints (fallback to Any if not available)
try:
    from models.state import AgentState
    from models.schemas import UserProfile, Product, AffordabilityAnalysis, FinancingPath
except ImportError:
    AgentState = Dict[str, Any]
    UserProfile = Any
    Product = Any
    AffordabilityAnalysis = Any
    FinancingPath = Any

from utils.financial import FinancialCalculator



















































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































try:
    from core.qdrant_client import qdrant_manager
    from core.embeddings import MultimodalEmbedder
    QDRANT_AVAILABLE = True
except ImportError:
    qdrant_manager = None
    MultimodalEmbedder = None
    QDRANT_AVAILABLE = False

from core.config import settings

logger = logging.getLogger(__name__)


class FinancialAnalyzerAgent:
    """
    Agent 2: Analyzes financial viability of products

    Responsibilities:
    1. Retrieve relevant financial rules via RAG
    2. Assess affordability (cash + financing)
    3. Calculate financial metrics (DTI, PTI, emergency fund)
    4. Generate financing paths (savings, installments)
    5. Filter to only affordable products
    6. Flag if all products are unaffordable (triggers Agent 2.5)
    """

    def __init__(self):
        if QDRANT_AVAILABLE:
            self.embedder = MultimodalEmbedder()
        else:
            self.embedder = None
        self.calculator = FinancialCalculator()
        logger.info("Financial Analyzer Agent initialized")

    @staticmethod
    def _get_attr(obj: Any, attr: str, default: Any = None):
        """Helper to get attribute from dict or object"""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def execute(self, state: Union[Dict[str, Any], AgentState]) -> Union[Dict[str, Any], AgentState]:
        """
        Execute financial analysis on candidate products

        Args:
            state: Current agent state with candidate_products from Agent 1

        Returns:
            Updated state with affordable_products and financial_analysis
        """
        start_time = self._get_timestamp()
        logger.info(f"Agent 2 starting analysis of {len(state.get('candidate_products', []))} products")

        try:
            # Step 1: Retrieve financial knowledge base context
            financial_context = self._retrieve_financial_rules(state['query'])
            logger.info(f"Retrieved {len(financial_context)} financial rule chunks")

            # Step 2: Analyze each candidate product
            analyzed_products = []
            user_profile = state['user_profile']

            for product in state.get('candidate_products', []):
                analysis = self._analyze_product_affordability(
                    product=product,
                    profile=user_profile,
                    financial_rules=financial_context
                )

                if analysis:
                    analyzed_products.append({
                        'product': product,
                        'affordability': analysis,
                        'financial_score': self._calculate_financial_score(analysis)
                    })

            # Step 3: Filter to affordable products only
            affordable_products = [
                item for item in analyzed_products
                if item['affordability']['can_afford_cash'] or
                   item['affordability']['can_afford_financing']
            ]

            # Step 4: Check if all products are unaffordable
            all_unaffordable = len(affordable_products) == 0 and len(analyzed_products) > 0

            # Step 5: Sort by financial score (best to worst)
            affordable_products.sort(key=lambda x: x['financial_score'], reverse=True)

            # Step 6: Update state
            state['affordable_products'] = affordable_products
            state['all_unaffordable'] = all_unaffordable
            state['financial_context'] = financial_context
            state['agent2_execution_time'] = int(self._get_timestamp() - start_time)
            state['financial_analysis_time_ms'] = state['agent2_execution_time']

            logger.info(
                f"Agent 2 complete: {len(affordable_products)}/{len(analyzed_products)} affordable "
                f"(all_unaffordable={all_unaffordable})"
            )

            return state

        except Exception as e:
            logger.error(f"Agent 2 error: {e}", exc_info=True)
            state['errors'] = state.get('errors', []) + [f"Financial analysis failed: {str(e)}"]
            state['affordable_products'] = []
            state['all_unaffordable'] = False  # Set to False on error to prevent pathfinder activation
            return state

    def _retrieve_financial_rules(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant financial rules using RAG

        Args:
            query: User search query
            top_k: Number of rule chunks to retrieve

        Returns:
            List of financial rule chunks with text and metadata
        """
        try:
            if not QDRANT_AVAILABLE or self.embedder is None:
                logger.warning("Qdrant not available - using empty financial rules")
                return []

            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)

            # Search financial_kb collection
            results = qdrant_manager.retrieve_financial_rules(
                query_vector=query_embedding.tolist(),
                top_k=top_k
            )

            # Extract payloads
            context = []
            for result in results:
                context.append({
                    'text': result.payload['text'],
                    'category': result.payload.get('category', 'general'),
                    'source': result.payload.get('source', 'system'),
                    'relevance_score': result.score
                })

            return context

        except Exception as e:
            logger.warning(f"Failed to retrieve financial rules: {e}")
            return []

    def _analyze_product_affordability(
        self,
        product: Any,  # Can be dict or Product object
        profile: UserProfile,
        financial_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive affordability analysis for a single product

        Args:
            product: Product to analyze (dict or Product object)
            profile: User financial profile
            financial_rules: Retrieved financial knowledge

        Returns:
            Affordability analysis with all metrics and paths
        """
        try:
            # Handle both dict and Pydantic Product objects
            if hasattr(product, 'price'):
                # Pydantic Product object
                price = product.price
                product_name = product.name
                financing_available = getattr(product, 'financing_available', False)
                financing_terms = getattr(product, 'financing_terms', {})
            else:
                # Dictionary
                price = product['price']
                product_name = product.get('name', 'unknown')
                financing_available = product.get('financing_available', False)
                financing_terms = product.get('financing_terms', {})

            # 1. Check cash affordability
            can_afford_cash, cash_metrics = self.calculator.check_cash_affordability(
                profile=profile,
                price=price
            )

            # 2. Check financing affordability (if available)
            can_afford_financing = False
            financing_metrics = {}
            financing_paths = []

            if financing_available:
                if isinstance(financing_terms, dict):
                    months = financing_terms.get('months', 12)
                    apr = financing_terms.get('apr', 0.0)
                else:
                    # Default financing terms
                    months = 12
                    apr = 0.0

                can_afford_financing, financing_metrics = self.calculator.check_financing_affordability(
                    profile=profile,
                    price=price,
                    months=months,
                    apr=apr
                )

                # Generate financing path
                if can_afford_financing:
                    financing_path = self.calculator.generate_financing_path(
                        profile=profile,
                        price=price,
                        months=months,
                        apr=apr
                    )
                    financing_paths.append(financing_path)

            # 3. Generate savings path (if cash not affordable)
            savings_path = None
            if not can_afford_cash:
                savings_path = self.calculator.generate_savings_path(
                    profile=profile,
                    price=price
                )

            # 4. Assess risk level
            risk_level, risk_factors = self.calculator.assess_risk_level(
                cash_affordable=can_afford_cash,
                financing_affordable=can_afford_financing,
                cash_metrics=cash_metrics,
                financing_metrics=financing_metrics
            )

            # 5. Calculate composite metrics
            monthly_income = self._get_attr(profile, 'monthly_income', 0)
            monthly_expenses = self._get_attr(profile, 'monthly_expenses', 0)
            disposable_income = monthly_income - monthly_expenses

            # Build comprehensive analysis
            analysis = {
                'can_afford_cash': can_afford_cash,
                'can_afford_financing': can_afford_financing,
                'cash_metrics': cash_metrics,
                'financing_metrics': financing_metrics,
                'financing_paths': financing_paths,
                'savings_path': savings_path,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'disposable_income': disposable_income,
                'financial_rules_applied': len(financial_rules),
                'recommendation': self._generate_recommendation(
                    can_afford_cash,
                    can_afford_financing,
                    str(risk_level)
                )
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing product {product_name if 'product_name' in locals() else 'unknown'}: {e}")
            return None

    def _calculate_financial_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate a financial viability score (0.0-1.0)

        🔒 CONTRACT REQUIREMENT: MUST return 0.0-1.0 (NOT 0-100)

        Higher score = better financial fit

        Factors:
        - Cash affordability: +0.4 points
        - Financing affordability: +0.3 points
        - Risk level: SAFE=+0.3, CAUTION=+0.15, RISKY=+0.0
        - Emergency fund adequacy: +bonus

        Args:
            analysis: Affordability analysis

        Returns:
            Score 0.0-1.0 (normalized)
        """
        score = 0.0

        # Cash affordability (0.4 points)
        if analysis['can_afford_cash']:
            score += 0.4

            # Bonus for comfortable margin
            cash_metrics = analysis['cash_metrics']
            if 'emergency_fund_months' in cash_metrics:
                if cash_metrics['emergency_fund_months'] >= 6:
                    score += 0.1  # Excellent emergency fund
                elif cash_metrics['emergency_fund_months'] >= 3:
                    score += 0.05   # Good emergency fund

        # Financing affordability (0.3 points)
        if analysis['can_afford_financing']:
            score += 0.3

            # Bonus for low PTI ratio
            financing_metrics = analysis.get('financing_metrics', {})
            if 'pti_ratio' in financing_metrics:
                pti = financing_metrics['pti_ratio']
                if pti < 0.10:  # Less than 10% of income
                    score += 0.1
                elif pti < 0.15:
                    score += 0.05

        # Risk level (0.3 points max)
        risk_level = str(analysis['risk_level'])
        if 'SAFE' in risk_level:
            score += 0.3
        elif 'CAUTION' in risk_level:
            score += 0.15
        # RISKY = 0 points

        return min(score, 1.0)

    def _generate_recommendation(
        self,
        can_afford_cash: bool,
        can_afford_financing: bool,
        risk_level: str
    ) -> str:
        """
        Generate a brief recommendation text

        Args:
            can_afford_cash: Whether affordable with cash
            can_afford_financing: Whether affordable with financing
            risk_level: SAFE, CAUTION, or RISKY

        Returns:
            Recommendation string
        """
        if can_afford_cash and risk_level == 'SAFE':
            return "Excellent fit - comfortable cash purchase with healthy emergency fund"

        elif can_afford_cash and risk_level == 'CAUTION':
            return "Affordable with cash, but would reduce emergency fund - consider carefully"

        elif can_afford_financing and risk_level == 'SAFE':
            return "Good financing option with manageable monthly payments"

        elif can_afford_financing and risk_level == 'CAUTION':
            return "Financing available but will strain budget - ensure stable income"

        elif can_afford_cash or can_afford_financing:
            return "Technically affordable but HIGH RISK - strongly consider alternatives"

        else:
            return "Currently unaffordable - consider savings plan or lower-priced alternatives"

    def _get_timestamp(self) -> float:
        """Get current timestamp in milliseconds"""
        import time
        return time.time() * 1000


# Global agent instance
financial_analyzer_agent = FinancialAnalyzerAgent()
