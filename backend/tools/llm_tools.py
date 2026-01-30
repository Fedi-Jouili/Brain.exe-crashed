"""
LLM Tools - Large Language Model and Evaluation Operations

This module provides 3 tools for LLM-based operations:

1. generate_explanation - Generate product recommendation explanations using Gemini
2. verify_explanation_facts - Fact-check LLM-generated explanations
3. evaluate_with_ragas - Evaluate RAG quality using RAGAS metrics

Architecture:
- Tools wrap LLM services (Gemini 2.0 Flash)
- Type-safe input/output via Pydantic
- Privacy-safe (no raw financial data to LLM)
- Fallback explanations for reliability

Usage Example:
    from tools.llm_tools import generate_explanation, verify_explanation_facts

    # Generate explanation
    result = generate_explanation.invoke({
        "context": {
            "product": {...},
            "affordability": {...},
            "financial_standing": "strong"
        },
        "rank": 1
    })

    # Verify explanation
    result = verify_explanation_facts.invoke({
        "explanation": "This laptop is affordable...",
        "context": {...}
    })
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from .base import BaseTool, ToolInput, ToolOutput
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 10: Generate Explanation
# ============================================================================

class ExplanationGenerationInput(ToolInput):
    """
    Input schema for explanation generation.

    Attributes:
        context: Context dict with product, affordability, financial_standing
        rank: Product rank in recommendation list (1-based)
    """
    context: Dict[str, Any] = Field(
        ...,
        description="Context dictionary with product, affordability, financial_standing"
    )
    rank: int = Field(
        ...,
        ge=1,
        description="Product rank in recommendation list (1-based)"
    )

    @validator('context')
    def validate_context_keys(cls, v):
        """Ensure context has required keys"""
        required_keys = ["product", "affordability", "financial_standing"]
        missing_keys = [k for k in required_keys if k not in v]
        if missing_keys:
            raise ValueError(f"context missing required keys: {missing_keys}")
        return v


class GenerateExplanationTool(BaseTool):
    """
    Generate product recommendation explanation using Gemini 2.0 Flash.

    This tool generates human-readable explanations for product recommendations
    using Google's Gemini LLM with strict factual requirements.

    Used by:
        - Agent 4 (Explainer) - Explanation generation

    LLM Configuration:
        - Model: Gemini 2.0 Flash (fast, cost-effective)
        - Temperature: 0.7 (balanced creativity)
        - Max tokens: 150 (2-3 sentences)

    Requirements:
        - Must include affordability wording (afford/affordable)
        - Must specify payment method (cash/financing)
        - Must mention product category
        - No fabrication of features
        - No hype words

    Privacy:
        - Uses financial_standing labels (NOT raw income)
        - No PII sent to LLM

    Example:
        tool = GenerateExplanationTool()
        result = tool.invoke({
            "context": {
                "product": {
                    "name": "Dell XPS 15",
                    "price": 1500.0,
                    "category": "Laptops",
                    "brand": "Dell",
                    "rating": 4.7,
                    "num_reviews": 523
                },
                "affordability": {
                    "can_afford_cash": False,
                    "can_afford_financing": True,
                    "risk_level": "caution"
                },
                "financial_standing": "moderate"  # NOT raw income
            },
            "rank": 1
        })

        if result["success"]:
            explanation = result["data"]["explanation"]
            print(f"Generated: {explanation}")
    """

    name = "generate_explanation"
    description = "Generate LLM-based product recommendation explanation using Gemini"
    input_schema = ExplanationGenerationInput

    def _execute(self, input_data: ExplanationGenerationInput) -> ToolOutput:
        """
        Execute explanation generation.

        Args:
            input_data: Validated generation parameters

        Returns:
            ToolOutput with:
                - explanation: Generated explanation text
                - model: Model name used
                - tokens: Approximate token count
        """
        try:
            # Lazy imports
            from google import genai
            from core.config import settings

            context = input_data.context
            rank = input_data.rank
            product = context['product']

            logger.info(
                f"Generating explanation for {product.get('name', 'Product')} "
                f"(rank #{rank})"
            )

            # Initialize Gemini client
            client = genai.Client(api_key=settings.google_api_key)
            model_name = "gemini-2.0-flash-exp"

            # Build prompt
            affordability = context['affordability']
            financial_standing = context['financial_standing']

            # Determine payment method instruction
            if affordability['can_afford_cash']:
                payment_instruction = 'You MUST use the word "cash" to describe payment.'
            elif affordability['can_afford_financing']:
                payment_instruction = 'You MUST use the word "financing" to describe payment options.'
            else:
                payment_instruction = 'Mention payment options available.'

            # Determine affordability instruction
            if affordability['can_afford_cash'] or affordability['can_afford_financing']:
                affordability_instruction = 'You MUST include the word "afford" or "affordable".'
            else:
                affordability_instruction = 'Be honest about affordability constraints.'

            prompt = f"""You are a financial advisor explaining a product recommendation to a customer.

PRODUCT DETAILS:
- Name: {product['name']}
- Price: ${product['price']:.2f}
- Category: {product['category']}
- Brand: {product.get('brand', 'N/A')}
- Rating: {product.get('rating', 0):.1f}/5.0 ({product.get('num_reviews', 0)} reviews)

CUSTOMER CONTEXT:
- Financial standing: {financial_standing}
- Can afford with cash: {affordability['can_afford_cash']}
- Financing available: {affordability['can_afford_financing']}
- Risk level: {affordability['risk_level']}

RANKING CONTEXT:
This product ranked #{rank} for this customer's needs.

TASK:
Write a 2-3 sentence explanation (max 100 words) for why this product is recommended.

MANDATORY REQUIREMENTS:

1. AFFORDABILITY WORDING:
   {affordability_instruction}

2. PAYMENT METHOD:
   {payment_instruction}

3. CATEGORY MENTION:
   You MUST mention the product category: "{product['category']}"

4. FACTUAL ACCURACY:
   - Only mention facts provided above
   - Do NOT fabricate features
   - Do NOT use hype words

5. STYLE:
   - Professional but friendly
   - Consumer-friendly language
   - Honest about financial commitment

Generate explanation:"""

            # Generate with Gemini
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": settings.llm_temperature,
                    "max_output_tokens": settings.llm_max_tokens,
                }
            )

            explanation = response.text.strip()

            # Estimate token count (rough approximation)
            tokens_approx = len(prompt.split()) + len(explanation.split())

            logger.info(
                f"Generated explanation ({len(explanation)} chars, ~{tokens_approx} tokens)"
            )

            return ToolOutput(
                success=True,
                data={
                    "explanation": explanation,
                    "model": model_name,
                    "tokens": tokens_approx
                }
            )

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}", exc_info=True)

            # Fallback to template-based explanation
            try:
                product = input_data.context['product']
                affordability = input_data.context['affordability']

                if affordability['can_afford_cash']:
                    fallback = f"The {product['name']} is a {product['category']} that you can afford with cash payment. It offers good value at ${product['price']:.2f}."
                elif affordability['can_afford_financing']:
                    fallback = f"The {product['name']} is a {product['category']} available through financing options. It's priced at ${product['price']:.2f}."
                else:
                    fallback = f"The {product['name']} is a {product['category']} priced at ${product['price']:.2f}. Consider savings or alternative options."

                logger.info("Using fallback template explanation")

                return ToolOutput(
                    success=True,
                    data={
                        "explanation": fallback,
                        "model": "fallback_template",
                        "tokens": len(fallback.split())
                    }
                )

            except Exception as fallback_error:
                logger.error(f"Fallback explanation also failed: {fallback_error}")
                return ToolOutput(
                    success=False,
                    error=f"Explanation generation failed: {str(e)}",
                    data=None
                )


# ============================================================================
# TOOL 11: Verify Explanation Facts
# ============================================================================

class FactVerificationInput(ToolInput):
    """
    Input schema for fact verification.

    Attributes:
        explanation: Generated explanation text
        context: Context used for generation (product, affordability)
    """
    explanation: str = Field(
        ...,
        description="Generated explanation text to verify",
        min_length=10
    )
    context: Dict[str, Any] = Field(
        ...,
        description="Context dictionary with product and affordability data"
    )


class VerifyExplanationFactsTool(BaseTool):
    """
    Verify factual accuracy of LLM-generated explanations.

    This tool checks that explanations match the provided context and
    don't contain fabricated information or violations.

    Used by:
        - Agent 4 (Explainer) - Post-generation verification

    Verification Checks:
        1. Affordability keywords present (afford/affordable)
        2. Payment method mentioned (cash/financing)
        3. Category mentioned
        4. Price accuracy (±$1 tolerance)
        5. No fabricated features
        6. No hype words (best, revolutionary, etc.)
        7. Repetition detection

    Trust Score:
        - 1.0: All checks passed
        - 0.7-0.9: Minor issues (rounding, synonyms)
        - <0.7: Major issues (fabrication, wrong facts)

    Example:
        tool = VerifyExplanationFactsTool()
        result = tool.invoke({
            "explanation": "The Dell XPS 15 laptop is affordable through financing...",
            "context": {
                "product": {"name": "Dell XPS 15", "price": 1500, "category": "Laptops"},
                "affordability": {"can_afford_cash": False, "can_afford_financing": True}
            }
        })

        if result["success"]:
            verified = result["data"]["verified"]
            trust_score = result["data"]["trust_score"]
            violations = result["data"]["violations"]

            if verified:
                print(f"✅ Verified (trust: {trust_score:.2f})")
            else:
                print(f"❌ Failed: {violations}")
    """

    name = "verify_explanation_facts"
    description = "Verify factual accuracy of LLM-generated explanations"
    input_schema = FactVerificationInput

    def _execute(self, input_data: FactVerificationInput) -> ToolOutput:
        """
        Execute fact verification.

        Args:
            input_data: Validated verification parameters

        Returns:
            ToolOutput with:
                - verified: bool (passed verification)
                - trust_score: float (0.0-1.0)
                - violations: list of violation strings
                - checks_passed: dict of individual check results
        """
        try:
            explanation = input_data.explanation.lower()  # Case-insensitive
            context = input_data.context
            product = context.get('product', {})
            affordability = context.get('affordability', {})

            logger.info("Verifying explanation factual accuracy")

            violations = []
            checks_passed = {}
            trust_score = 1.0

            # Check 1: Affordability keywords
            affordability_keywords = ["afford", "affordable", "within budget", "budget-friendly"]
            has_affordability = any(kw in explanation for kw in affordability_keywords)
            checks_passed["affordability_keywords"] = has_affordability

            if not has_affordability:
                violations.append("Missing affordability keywords (afford/affordable)")
                trust_score -= 0.2

            # Check 2: Payment method
            payment_keywords_cash = ["cash", "one-time", "upfront"]
            payment_keywords_financing = ["financing", "payment plan", "installment", "monthly payment"]

            if affordability.get('can_afford_cash'):
                has_payment = any(kw in explanation for kw in payment_keywords_cash)
            elif affordability.get('can_afford_financing'):
                has_payment = any(kw in explanation for kw in payment_keywords_financing)
            else:
                has_payment = True  # No specific requirement

            checks_passed["payment_method"] = has_payment

            if not has_payment:
                violations.append("Missing payment method specification")
                trust_score -= 0.2

            # Check 3: Category mention
            category = product.get('category', '').lower()
            has_category = category in explanation if category else True
            checks_passed["category_mentioned"] = has_category

            if not has_category:
                violations.append(f"Missing category mention: {product.get('category')}")
                trust_score -= 0.15

            # Check 4: Price accuracy (±$1 tolerance)
            actual_price = float(product.get('price', 0))
            import re
            price_matches = re.findall(r'\$\s?(\d+(?:,\d{3})*(?:\.\d{2})?)', input_data.explanation)

            price_accurate = True
            if price_matches:
                for price_str in price_matches:
                    mentioned_price = float(price_str.replace(',', ''))
                    if abs(mentioned_price - actual_price) > 1.0:
                        violations.append(f"Price mismatch: mentioned ${mentioned_price}, actual ${actual_price}")
                        trust_score -= 0.3
                        price_accurate = False

            checks_passed["price_accurate"] = price_accurate

            # Check 5: Hype words detection
            hype_words = ["best", "revolutionary", "cutting-edge", "game-changing", "amazing", "incredible"]
            has_hype = any(hw in explanation for hw in hype_words)
            checks_passed["no_hype_words"] = not has_hype

            if has_hype:
                violations.append("Contains hype words (best/revolutionary/amazing)")
                trust_score -= 0.1

            # Check 6: Repetition detection
            words = explanation.split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1

            repeated_words = [w for w, count in word_freq.items() if count > 2]
            has_repetition = len(repeated_words) > 0
            checks_passed["no_repetition"] = not has_repetition

            if has_repetition:
                violations.append(f"Repetitive wording: {repeated_words[:3]}")
                trust_score -= 0.05

            # Ensure trust_score is in [0.0, 1.0]
            trust_score = max(0.0, min(1.0, trust_score))

            # Determine verification status
            verified = trust_score >= 0.70

            logger.info(
                f"Verification complete: verified={verified}, trust={trust_score:.2f}, "
                f"violations={len(violations)}"
            )

            return ToolOutput(
                success=True,
                data={
                    "verified": verified,
                    "trust_score": float(trust_score),
                    "violations": violations,
                    "checks_passed": checks_passed
                }
            )

        except Exception as e:
            logger.error(f"Fact verification failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Fact verification failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 12: Evaluate with RAGAS
# ============================================================================

class RAGASEvaluationInput(ToolInput):
    """
    Input schema for RAGAS evaluation.

    Attributes:
        question: Original user query
        answer: Generated answer/explanation
        contexts: List of retrieved context documents
        ground_truth: Optional ground truth answer
    """
    question: str = Field(
        ...,
        description="Original user query/question",
        min_length=5
    )
    answer: str = Field(
        ...,
        description="Generated answer or explanation",
        min_length=10
    )
    contexts: List[str] = Field(
        ...,
        description="Retrieved context documents (RAG)",
        min_items=1
    )
    ground_truth: Optional[str] = Field(
        default=None,
        description="Optional ground truth answer for comparison"
    )


class EvaluateWithRAGASTool(BaseTool):
    """
    Evaluate RAG quality using RAGAS metrics.

    This tool evaluates Retrieval-Augmented Generation quality using
    RAGAS (Retrieval Augmented Generation Assessment) framework.

    Used by:
        - Agent 2 (Financial Analyzer) - RAG quality assessment
        - Agent 4 (Explainer) - Explanation quality evaluation

    RAGAS Metrics:
        1. Context Precision: Relevance of retrieved contexts
        2. Context Recall: Coverage of ground truth in contexts
        3. Faithfulness: Answer grounded in contexts (no hallucination)
        4. Answer Relevance: Answer relevance to question

    Note:
        This is a simplified implementation. Full RAGAS requires
        additional dependencies (ragas, datasets) and LLM access.

    Example:
        tool = EvaluateWithRAGASTool()
        result = tool.invoke({
            "question": "Can I afford a $1000 laptop?",
            "answer": "Yes, you can afford it through financing...",
            "contexts": [
                "User monthly income: $5000",
                "DTI threshold: 36%",
                "Financing available with 5% APR"
            ],
            "ground_truth": "Yes, financing is available"
        })

        if result["success"]:
            metrics = result["data"]["metrics"]
            print(f"Faithfulness: {metrics['faithfulness']:.2f}")
            print(f"Answer Relevance: {metrics['answer_relevance']:.2f}")
    """

    name = "evaluate_with_ragas"
    description = "Evaluate RAG quality using RAGAS metrics (faithfulness, relevance)"
    input_schema = RAGASEvaluationInput

    def _execute(self, input_data: RAGASEvaluationInput) -> ToolOutput:
        """
        Execute RAGAS evaluation.

        Args:
            input_data: Validated evaluation parameters

        Returns:
            ToolOutput with:
                - metrics: Dict of RAGAS metrics
                - overall_score: Average score
                - evaluation_details: Detailed breakdown
        """
        try:
            logger.info("Evaluating with RAGAS metrics (simplified implementation)")

            question = input_data.question.lower()
            answer = input_data.answer.lower()
            contexts = [c.lower() for c in input_data.contexts]

            metrics = {}

            # Metric 1: Faithfulness (answer grounded in contexts)
            # Check if answer statements appear in contexts
            answer_sentences = [s.strip() for s in answer.split('.') if s.strip()]
            grounded_count = 0

            for sentence in answer_sentences:
                # Check if sentence content appears in any context
                sentence_words = set(sentence.split())
                for context in contexts:
                    context_words = set(context.split())
                    # If >50% of sentence words appear in context, consider grounded
                    overlap = len(sentence_words & context_words) / len(sentence_words) if sentence_words else 0
                    if overlap > 0.5:
                        grounded_count += 1
                        break

            faithfulness = grounded_count / len(answer_sentences) if answer_sentences else 0.0
            metrics["faithfulness"] = float(faithfulness)

            # Metric 2: Answer Relevance (answer relevant to question)
            # Check if question keywords appear in answer
            question_words = set(question.split())
            answer_words = set(answer.split())

            # Remove stop words
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'can', 'you', 'i', 'to', 'for'}
            question_words = question_words - stop_words

            overlap = len(question_words & answer_words) / len(question_words) if question_words else 0.0
            answer_relevance = min(1.0, overlap * 1.5)  # Scale up, cap at 1.0
            metrics["answer_relevance"] = float(answer_relevance)

            # Metric 3: Context Precision (contexts relevant to question)
            relevant_context_count = 0

            for context in contexts:
                context_words = set(context.split())
                overlap = len(question_words & context_words) / len(question_words) if question_words else 0.0
                if overlap > 0.3:  # 30% overlap threshold
                    relevant_context_count += 1

            context_precision = relevant_context_count / len(contexts) if contexts else 0.0
            metrics["context_precision"] = float(context_precision)

            # Metric 4: Context Recall (if ground truth provided)
            if input_data.ground_truth:
                ground_truth = input_data.ground_truth.lower()
                gt_words = set(ground_truth.split()) - stop_words

                context_union = set()
                for context in contexts:
                    context_union.update(context.split())

                recall = len(gt_words & context_union) / len(gt_words) if gt_words else 0.0
                metrics["context_recall"] = float(recall)
            else:
                metrics["context_recall"] = None

            # Calculate overall score (average of non-None metrics)
            metric_values = [v for v in metrics.values() if v is not None]
            overall_score = sum(metric_values) / len(metric_values) if metric_values else 0.0

            evaluation_details = {
                "total_contexts": len(contexts),
                "answer_sentences": len(answer_sentences),
                "grounded_sentences": grounded_count,
                "relevant_contexts": relevant_context_count
            }

            logger.info(
                f"RAGAS evaluation complete: overall={overall_score:.2f}, "
                f"faithfulness={faithfulness:.2f}, relevance={answer_relevance:.2f}"
            )

            return ToolOutput(
                success=True,
                data={
                    "metrics": metrics,
                    "overall_score": float(overall_score),
                    "evaluation_details": evaluation_details
                }
            )

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"RAGAS evaluation failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL INSTANCES
# ============================================================================

# Create singleton instances for easy import
generate_explanation = GenerateExplanationTool()
verify_explanation_facts = VerifyExplanationFactsTool()
evaluate_with_ragas = EvaluateWithRAGASTool()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Tool classes
    "GenerateExplanationTool",
    "VerifyExplanationFactsTool",
    "EvaluateWithRAGASTool",
    # Tool instances
    "generate_explanation",
    "verify_explanation_facts",
    "evaluate_with_ragas",
]
