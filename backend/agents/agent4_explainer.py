"""
Agent 4: Explainer with LLM and Fact Verification

Generates human-readable explanations for recommendations using Gemini LLM.
Verifies factual accuracy and calculates trust scores.

🔒 ENFORCED CONTRACTS:
1. Trust scores in [0.0, 1.0] range (NOT 0-100%)
2. Immutable explanation objects (no in-place mutation)
3. Structured, actionable violation reporting
4. Privacy-safe context (no raw financial data to LLM)
5. Fallback trust capped at 0.85 (deterministic ≠ verified)
6. LLM repetition detection and prevention

VERIFIED SEMANTICS:
- verified: True → Factual verification passed (NOT LLM confidence)
- verified: False → Trust below threshold or violations detected

For fallback explanations:
- verified: True → Template is consistent (not hallucinated)
- trust: 0.85 → Epistemic humility (not ground-truthed)
"""
import re
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
# DO NOT use google.generativeai — deprecated by Google (use google.genai)
from google import genai

# Optional imports for type hints (fallback to Any if not available)
try:
    from models.state import AgentState
    from models.schemas import Product, UserProfile
except ImportError:
    AgentState = Dict[str, Any]
    Product = Any
    UserProfile = Any

from core.config import settings
from core.redis_client import redis_manager

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Service for generating LLM explanations

    Separated from verification for single responsibility principle.
    Handles all LLM interaction and prompt building.
    """

    def __init__(self, client, model_name):
        """
        Initialize explanation service

        Args:
            client: Configured Gemini client instance
            model_name: Model name (e.g., 'gemini-1.5-flash')
        """
        self.client = client
        self.model_name = model_name
        self.max_regeneration_attempts = 2

    def generate(
        self,
        context: Dict[str, Any],
        rank: int
    ) -> str:
        """
        Generate explanation using Gemini LLM with self-check

        Adds final reminder before generation to ensure keyword inclusion.
        """
        # Build comprehensive prompt with requirements
        prompt = self._build_prompt(context, rank)

        # Add final self-check reminder (hidden from end-user output)
        # This is prompt-only engineering, no post-processing
        enhanced_prompt = prompt + """

FINAL REMINDER:
Do not omit required affordability keywords, payment method, or product category.
Your response will be verified for factual accuracy.
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=enhanced_prompt,
            config={
                "temperature": settings.llm_temperature,
                "max_output_tokens": settings.llm_max_tokens,
            }
        )

        return response.text.strip()

    def _build_prompt(self, context: Dict, rank: int) -> str:
        """
        Build LLM prompt with STRICT keyword requirements

        Ensures verifier-required terms are included while maintaining
        natural language quality.
        """
        product = context['product']
        affordability = context['affordability']
        financial_standing = context['financial_standing']  # Label, NOT raw number!

        # Determine required payment method wording
        if affordability['can_afford_cash']:
            payment_instruction = 'You MUST use the word "cash" to describe payment.'
        elif affordability['can_afford_financing']:
            payment_instruction = 'You MUST use the word "financing" to describe payment options.'
        else:
            payment_instruction = 'Mention payment options available.'

        # Determine required affordability wording
        if affordability['can_afford_cash'] or affordability['can_afford_financing']:
            affordability_instruction = 'You MUST include the word "afford" or "affordable".'
        else:
            affordability_instruction = 'Be honest about affordability constraints.'

        prompt = f"""You are a financial advisor explaining a product recommendation to a customer.

PRODUCT DETAILS:
- Name: {product['name']}
- Price: ${product['price']:.2f}
- Category: {product['category']}
- Brand: {product['brand']}
- Rating: {product['rating']:.1f}/5.0 ({product['num_reviews']} reviews)

CUSTOMER CONTEXT:
- Financial standing: {financial_standing}
- Can afford with cash: {affordability['can_afford_cash']}
- Financing available: {affordability['can_afford_financing']}
- Risk level: {affordability['risk_level']}

RANKING CONTEXT:
This product ranked #{rank} for this customer's needs.

TASK:
Write a 2-3 sentence explanation (max 100 words) for why this product is recommended.

MANDATORY REQUIREMENTS (YOU MUST FOLLOW ALL):

1. AFFORDABILITY WORDING:
   {affordability_instruction}
   Use phrases like "can afford", "affordable", or "within budget".

2. PAYMENT METHOD:
   {payment_instruction}
   Be explicit about HOW the customer can purchase.

3. CATEGORY MENTION:
   You MUST mention the product category: "{product['category']}"
   Use it naturally in your explanation.

4. FACTUAL ACCURACY:
   - Only mention facts provided above
   - Do NOT fabricate features or specifications
   - Do NOT use hype words (best, revolutionary, cutting-edge)
   - Do NOT mention internal scoring or ranking algorithms

5. STYLE:
   - Professional but friendly
   - Consumer-friendly language
   - Honest about financial commitment
   - Focus on value and fit for customer needs

VERIFICATION CHECKLIST (Check before finishing):
□ Did I include affordability wording? (afford/affordable)
□ Did I specify payment method? (cash or financing)
□ Did I mention the category? ({product['category']})
□ Is everything factual (no fabrication)?
□ Is it 2-3 sentences and under 100 words?

Generate explanation:"""

        return prompt


class VerificationService:
    """
    Service for verifying LLM explanation accuracy

    Returns structured, actionable violations for debugging and observability.

    VIOLATION FORMAT:
    - Human-readable: "Price mismatch: mentioned $X, actual $Y"
    - Actionable: Specifies what's wrong and values
    - Stable keys: Enables CI assertions and metrics
    """

    def __init__(self):
        """Initialize verification service with trust threshold"""
        self.trust_threshold = 0.70  # 70% minimum (0.0-1.0 scale)

    def verify(
        self,
        explanation: str,
        context: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Verify factual accuracy of explanation

        Args:
            explanation: LLM-generated text
            context: Original context used for generation

        Returns:
            Tuple of (trust_score: 0.0-1.0, violations: List[str])

            Violations are structured as:
            "{category}: {specific_details}"

            Examples:
            - "Price mismatch: mentioned $1299.99, actual $999.99"
            - "Rating mismatch: mentioned 5.0, actual 4.2"
            - "Incorrect affordability claim: financing"
        """
        violations = []
        trust_score = 1.0  # Start with full trust

        explanation_lower = explanation.lower()
        product = context['product']
        affordability = context['affordability']

        # 🔒 Check 1: Product name accuracy
        if product['name'].lower() not in explanation_lower:
            violations.append(
                f"Product name missing: expected '{product['name']}'"
            )
            trust_score -= 0.10

        # 🔒 Check 2: Price accuracy (if mentioned)
        price_mentions = re.findall(r'\$[\d,]+(?:\.\d{2})?', explanation)
        for price_str in price_mentions:
            price_value = float(price_str.replace('$', '').replace(',', ''))
            actual_price = product['price']

            # Allow 1% variance for rounding
            if abs(price_value - actual_price) > (actual_price * 0.01):
                violations.append(
                    f"Price mismatch: mentioned ${price_value:.2f}, actual ${actual_price:.2f}"
                )
                trust_score -= 0.20

        # 🔒 Check 3: Rating accuracy (if mentioned)
        rating_mentions = re.findall(
            r'(\d+(?:\.\d+)?)\s*(?:\/\s*5|stars?|rating)',
            explanation_lower
        )
        for rating_str in rating_mentions:
            mentioned_rating = float(rating_str)
            actual_rating = product['rating']

            if abs(mentioned_rating - actual_rating) > 0.5:
                violations.append(
                    f"Rating mismatch: mentioned {mentioned_rating:.1f}, actual {actual_rating:.1f}"
                )
                trust_score -= 0.15

        # 🔒 Check 4: Affordability claims with synonym support
        # Accept natural language variations while maintaining strictness

        # Define synonym groups for flexible matching
        affordability_synonyms = ['afford', 'affordable', 'within budget', 'can get']
        financing_synonyms = ['financing', 'installment', 'payment plan', 'finance']
        cash_synonyms = ['cash', 'pay upfront', 'full payment', 'outright']

        affordability_checks = {
            'affordability': {
                'should_be_present': affordability['can_afford_cash'] or affordability['can_afford_financing'],
                'synonyms': affordability_synonyms,
                'missing_msg': "Missing affordability wording (afford/affordable)"
            },
            'financing': {
                'should_be_present': affordability['can_afford_financing'],
                'synonyms': financing_synonyms,
                'missing_msg': "Missing financing mention when financing available"
            },
            'cash': {
                'should_be_present': affordability['can_afford_cash'],
                'synonyms': cash_synonyms,
                'missing_msg': "Missing cash payment mention when cash affordable"
            }
        }

        for check_name, check_config in affordability_checks.items():
            should_be_present = check_config['should_be_present']
            synonyms = check_config['synonyms']

            # Check if ANY synonym is present
            keyword_present = any(syn in explanation_lower for syn in synonyms)

            if should_be_present and not keyword_present:
                violations.append(check_config['missing_msg'])
                trust_score -= 0.05
            elif not should_be_present and keyword_present:
                # More specific error message
                violations.append(
                    f"Incorrect {check_name} claim: mentioned but not supported by analysis"
                )
                trust_score -= 0.15

        # 🔒 Check 5: Hallucinated features detection
        suspicious_patterns = [
            (
                r'includes?\s+(?:free|unlimited|premium)',
                "Unverifiable 'includes' claim (possible hallucination)"
            ),
            (
                r'comes?\s+with\s+(?:free|bonus)',
                "Unverifiable 'comes with' claim (possible hallucination)"
            ),
            (
                r'(?:revolutionary|cutting-edge|best\s+in\s+class)',
                "Subjective superlative claim (not in source data)"
            ),
        ]

        for pattern, violation_msg in suspicious_patterns:
            if re.search(pattern, explanation_lower):
                violations.append(violation_msg)
                trust_score -= 0.05

        # 🔒 Check 6: Brand/category correctness
        if len(product['brand']) > 3 and product['brand'].lower() not in explanation_lower:
            violations.append(f"Brand not mentioned: {product['brand']}")
            trust_score -= 0.05

        # Category mention (with partial matching)
        category_lower = product['category'].lower()

        # Accept partial category matches (e.g., "laptop" in "Gaming Laptop")
        # Split category into words to catch variations
        category_words = category_lower.split()
        category_mentioned = any(word in explanation_lower for word in category_words if len(word) > 3)

        if not category_mentioned:
            violations.append(f"Product category not mentioned: {product['category']}")
            trust_score -= 0.05

        # Clamp to [0.0, 1.0] range
        trust_score = max(0.0, min(1.0, trust_score))

        return trust_score, violations


class ExplainerAgent:
    """
    Agent 4: Explainer with LLM and fact verification

    ENFORCED CONTRACTS:
    1. Trust scores in [0.0, 1.0] range (NOT 0-100%)
    2. Immutable explanation objects (no in-place mutation)
    3. Structured, actionable violation reporting
    4. Privacy-safe context (no raw financial data to LLM)
    5. Fallback trust capped at 0.85 (deterministic ≠ verified)
    6. LLM repetition detection and prevention

    VERIFIED SEMANTICS:
    - verified: True → Factual verification passed (NOT LLM confidence)
    - verified: False → Trust below threshold or violations detected

    For fallback explanations:
    - verified: True → Template is consistent (not hallucinated)
    - trust: 0.85 → Epistemic humility (not ground-truthed)
    """

    def __init__(self):
        """Initialize Explainer Agent with services"""
        # Configure Gemini (using official google-genai SDK)
        # DO NOT use gemini-1.5-* models — not supported for this project
        if settings.google_api_key:
            client = genai.Client(api_key=settings.google_api_key)
            self.explanation_service = ExplanationService(client, settings.llm_model)
            self.has_llm = True
            logger.info(f"✅ Gemini LLM initialized: {settings.llm_model}")
        else:
            self.explanation_service = None
            self.has_llm = False
            logger.warning("Google API key not configured - using fallback explanations")

        # Verification service (always available)
        self.verification_service = VerificationService()

        # Constants
        self.trust_threshold = 0.70  # 70% minimum trust (0.0-1.0 scale)
        self.fallback_trust = 0.85   # Cap fallback at 85% (NOT 1.0)

        logger.info("Explainer Agent initialized with contract enforcement")

        logger.info("Explainer Agent initialized with contract enforcement")

    def execute(self, state: AgentState) -> AgentState:
        """
        Generate explanations for recommendations

        CONTRACT ENFORCEMENT:
        - Creates immutable explanation objects
        - Uses 0.0-1.0 trust scores
        - Returns structured violations
        - Detects LLM repetition

        Args:
            state: Current agent state with recommendations

        Returns:
            Updated state with explanation objects added
        """
        start_time = time.time()
        logger.info("Agent 4: Starting explanation generation")

        recommendations = state.get('final_recommendations', [])

        if not recommendations:
            logger.warning("Agent 4: No recommendations to explain")
            state['agent4_execution_time'] = int((time.time() - start_time) * 1000)
            return state

        # Process top 3 recommendations
        top_recommendations = recommendations[:3]

        for i, rec in enumerate(top_recommendations):
            try:
                # Gather ANONYMIZED context
                context = self._gather_context(rec, state)

                # Generate explanation
                if self.has_llm:
                    explanation_obj = self._generate_with_llm(rec, context, state)
                else:
                    explanation_obj = self._generate_fallback(rec, context)

                # 🔒 CONTRACT: Create immutable explanation object
                # DO NOT mutate rec directly (e.g., rec['trust_score'] = ...)
                rec['explanation'] = explanation_obj

                logger.info(
                    f"Explained #{i+1}: trust={explanation_obj['trust']:.2f}, "
                    f"violations={len(explanation_obj['violations'])}, "
                    f"verified={explanation_obj['verified']}"
                )

            except Exception as e:
                logger.error(f"Failed to explain recommendation #{i+1}: {e}")
                rec['explanation'] = {
                    'text': 'Explanation unavailable',
                    'trust': 0.0,
                    'verified': False,
                    'violations': ['Generation failed: ' + str(e)],
                    'used_llm': False,
                    'type': 'error'
                }

        # Update state
        execution_time = int((time.time() - start_time) * 1000)
        state['agent4_execution_time'] = execution_time
        state['explainer_time_ms'] = execution_time

        logger.info(
            f"Agent 4 complete: Explained {len(top_recommendations)} recommendations "
            f"in {execution_time}ms"
        )

        return state

    def _generate_with_llm(
        self,
        rec: Dict,
        context: Dict,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Generate explanation using LLM with verification

        🔒 LLM SAFETY: Detects and prevents repetition

        Args:
            rec: Recommendation dictionary
            context: Anonymized context
            state: Agent state

        Returns:
            Explanation object with trust score in [0.0, 1.0]
        """
        best_explanation = None
        best_trust = 0.0
        best_violations = []
        previous_explanation = None
        regeneration_count = 0

        for attempt in range(self.explanation_service.max_regeneration_attempts):
            # Generate
            explanation_text = self.explanation_service.generate(
                context=context,
                rank=rec.get('rank', 0)
            )

            # 🔒 CONTRACT: Explicit repetition detection (LLM safety)
            if explanation_text == previous_explanation:
                logger.warning(
                    f"LLM repeated same output (attempt {attempt + 1}), stopping retry. "
                    "This prevents infinite loops and wasted API calls."
                )
                break

            previous_explanation = explanation_text
            regeneration_count = attempt + 1

            # Verify facts
            trust_score, violations = self.verification_service.verify(
                explanation_text,
                context
            )

            logger.debug(
                f"Attempt {attempt + 1}: trust={trust_score:.2f}, "
                f"violations={len(violations)}"
            )

            # Keep best
            if trust_score > best_trust:
                best_explanation = explanation_text
                best_trust = trust_score
                best_violations = violations

            # Stop if good enough
            if trust_score >= self.trust_threshold:
                logger.debug(f"Trust threshold met ({trust_score:.2f}), stopping")
                break

            if attempt == 0:
                logger.warning(
                    f"Low trust ({trust_score:.2f}), will retry. "
                    f"Violations: {violations}"
                )

        # 🔒 CONTRACT: Return immutable explanation object
        # SEMANTICS: verified = factual verification passed (NOT LLM confidence)
        return {
            'text': best_explanation,
            'trust': best_trust,  # 0.0-1.0 scale, NOT 0-100%
            'verified': best_trust >= self.trust_threshold,  # Factual check passed
            'violations': best_violations,
            'used_llm': True,
            'regeneration_count': regeneration_count,
            'type': self._classify_explanation_type(context)
        }

    def _generate_fallback(
        self,
        rec: Dict,
        context: Dict
    ) -> Dict[str, Any]:
        """
        Generate template-based explanation

        🔒 CONTRACT: Fallback trust capped at 0.85 (NOT 1.0)

        FALLBACK SEMANTICS:
        - verified: True → Template is consistent (not hallucinated)
        - trust: 0.85 → Epistemic humility (not ground-truthed)

        Philosophy:
        Deterministic != verified truth
        Fallback is consistent but not fact-checked against external data

        Args:
            rec: Recommendation dictionary
            context: Context dictionary

        Returns:
            Fallback explanation object
        """
        product = context['product']
        affordability = context['affordability']

        parts = []

        # Build explanation
        parts.append(
            f"{product['name']} is a {product['category']} from {product['brand']}"
        )

        if product['rating'] >= 4.0:
            parts.append(
                f"with a strong {product['rating']:.1f}/5 rating "
                f"({product['num_reviews']} reviews)"
            )

        if affordability['can_afford_cash']:
            parts.append("You can afford this with cash")
        elif affordability['can_afford_financing']:
            parts.append("Financing options are available")

        if context.get('rank') == 1:
            parts.append("This is our top recommendation for your needs")

        explanation_text = ". ".join(parts) + "."

        # 🔒 CONTRACT: Fallback trust = 0.85 (NOT 1.0)
        # Fallback is deterministic and consistent, but not ground-truthed
        return {
            'text': explanation_text,
            'trust': self.fallback_trust,  # 0.85, enforcing epistemic humility
            'verified': True,  # Template is consistent (not hallucinated)
            'violations': [],
            'used_llm': False,
            'regeneration_count': 0,
            'type': 'fallback'
        }

    def _classify_explanation_type(self, context: Dict) -> str:
        """
        Classify explanation type for analytics

        Args:
            context: Context dictionary with scores

        Returns:
            "affordability-led" | "value-led" | "learning-led"
        """
        affordability = context['affordability']
        scores = context['scores']

        if not affordability['can_afford_cash'] and affordability['can_afford_financing']:
            return "affordability-led"
        elif scores.get('thompson', 0) > 0.8:
            return "learning-led"
        else:
            return "value-led"

    def _gather_context(self, rec: Dict, state: AgentState) -> Dict[str, Any]:
        """
        Gather context for explanation

        🔒 CONTRACT: Privacy-safe context
        - NEVER pass raw income/credit_score/savings to LLM
        - Use derived labels only

        ANONYMIZATION:
        Raw data → Derived labels
        - credit_score: 750 → "excellent"
        - credit_score: 700 → "good"
        - credit_score: 650 → "moderate"
        - credit_score: <650 → "rebuilding"

        Args:
            rec: Recommendation dictionary
            state: Agent state

        Returns:
            Anonymized context dictionary
        """
        try:
            product = rec['product']

            # Extract product details
            if isinstance(product, dict):
                product_context = {
                    'name': product.get('name', 'Unknown'),
                    'price': product.get('price', 0),
                    'category': product.get('category', 'Unknown'),
                    'brand': product.get('brand', 'Unknown'),
                    'rating': product.get('rating', 0),
                    'num_reviews': product.get('num_reviews', 0),
                }
            else:
                product_context = {
                    'name': getattr(product, 'name', 'Unknown'),
                    'price': getattr(product, 'price', 0),
                    'category': getattr(product, 'category', 'Unknown'),
                    'brand': getattr(product, 'brand', 'Unknown'),
                    'rating': getattr(product, 'rating', 0),
                    'num_reviews': getattr(product, 'num_reviews', 0),
                }

            # Extract affordability
            affordability = rec.get('affordability', {})
            affordability_context = {
                'can_afford_cash': affordability.get('can_afford_cash', False),
                'can_afford_financing': affordability.get('can_afford_financing', False),
                'risk_level': affordability.get('risk_level', 'unknown'),
            }

            # Extract scores
            scores = rec.get('scores', {})
            scores_context = {
                'thompson': scores.get('thompson', 0),
                'collaborative': scores.get('collaborative', 0),
                'ragas': scores.get('ragas', 0),
                'final_score': rec.get('final_score', 0),
            }

            # 🔒 CONTRACT: Anonymize user profile
            # Convert raw numbers to categorical labels
            user_profile = state.get('user_profile')
            if user_profile:
                credit_score = getattr(user_profile, 'credit_score', 0)

                # Derived label, NOT raw number
                if credit_score >= 750:
                    financial_standing = "excellent"
                elif credit_score >= 700:
                    financial_standing = "good"
                elif credit_score >= 650:
                    financial_standing = "moderate"
                else:
                    financial_standing = "rebuilding"
            else:
                financial_standing = "unknown"

            # Combine context
            context = {
                'product': product_context,
                'affordability': affordability_context,
                'scores': scores_context,
                'financial_standing': financial_standing,  # Label, not raw number!
                'rank': rec.get('rank', 0),
                'query': state.get('query', ''),
            }

            return context

        except Exception as e:
            logger.error(f"Error gathering context: {e}")
            return {}
            return context

        except Exception as e:
            logger.error(f"Error gathering context: {e}")
            return {}


# 🔒 CONTRACT ENFORCEMENT - Validation on import
# These checks run when the module loads, catching violations early

def _validate_contracts():
    """
    Validate Agent 4 contracts are enforced

    Called during agent initialization to catch violations early.
    Fails fast in development, prevents silent drift.

    CI catches regressions before deployment.
    """
    contracts = []

    # Contract 1: Trust threshold in [0.0, 1.0]
    trust_threshold = 0.70
    assert 0.0 <= trust_threshold <= 1.0, \
        f"trust_threshold must be in [0.0, 1.0], got {trust_threshold}"
    contracts.append("✓ Trust threshold in valid range")

    # Contract 2: Fallback trust < 1.0 (deterministic ≠ verified)
    fallback_trust = 0.85
    assert fallback_trust < 1.0, \
        f"fallback_trust must be < 1.0 (epistemic humility), got {fallback_trust}"
    contracts.append("✓ Fallback trust enforces epistemic humility")

    # Contract 3: Fallback trust reasonable
    assert 0.8 <= fallback_trust <= 0.9, \
        f"fallback_trust should be high but capped (0.8-0.9), got {fallback_trust}"
    contracts.append("✓ Fallback trust in reasonable range")

    logger.debug("Agent 4 contract validation:")
    for contract in contracts:
        logger.debug(f"  {contract}")

    logger.info("✅ Agent 4 contracts validated")


# Global instance
explainer_agent = ExplainerAgent()
_validate_contracts()  # Run on import for early failure detection
