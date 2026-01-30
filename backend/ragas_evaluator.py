"""
RAGAS Evaluation Module - Standalone Implementation
Can be integrated into any RAG system

Author: GitHub Copilot
Created: January 30, 2026
Requirements: pip install ragas datasets

This module provides RAG quality evaluation using RAGAS metrics for:
- Agent 2: Financial rule retrieval validation
- Agent 3: Query-product relevancy scoring
- Agent 4: Explanation faithfulness verification
"""

from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGASEvaluator:
    """
    Standalone RAGAS evaluator for RAG quality assessment.

    This class provides methods to evaluate retrieval quality, answer faithfulness,
    and query-document relevancy using RAGAS metrics. All methods handle errors
    gracefully and never crash.

    Usage:
        evaluator = RAGASEvaluator()
        scores = evaluator.evaluate_single(
            question="Why is this laptop affordable?",
            answer="The laptop is affordable because...",
            contexts=["Rule 1: DTI < 43%", "Rule 2: Payment < 15%"],
            ground_truth="Affordable due to financing (optional)"
        )

        print(scores)
        # {
        #     "context_precision": 0.95,
        #     "faithfulness": 0.92,
        #     "answer_relevancy": 0.88,
        #     "context_recall": 0.85  # if ground_truth provided
        # }

    Attributes:
        metrics (list): List of RAGAS metrics used for evaluation
        _initialized (bool): Flag indicating successful initialization
    """

    def __init__(self):
        """
        Initialize RAGAS evaluator with default metrics.

        Loads the following metrics:
        - context_precision: Are retrieved documents relevant?
        - faithfulness: Does answer stick to context (no hallucinations)?
        - answer_relevancy: Is answer relevant to the question?

        Raises:
            No exceptions - logs warnings if initialization fails
        """
        self.metrics = []
        self._initialized = False

        try:
            from ragas.metrics import (
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy
            )

            # Default metrics for all evaluations
            self.context_precision = context_precision
            self.context_recall = context_recall
            self.faithfulness = faithfulness
            self.answer_relevancy = answer_relevancy

            self.metrics = [
                self.context_precision,
                self.faithfulness,
                self.answer_relevancy
            ]

            self._initialized = True
            logger.info("✅ RAGAS evaluator initialized successfully with 3 default metrics")

        except ImportError as e:
            logger.error(f"❌ Failed to import RAGAS metrics: {e}")
            logger.error("Install with: pip install ragas datasets")
        except Exception as e:
            logger.error(f"❌ Unexpected error during RAGAS initialization: {e}")

    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evaluate a single question-answer pair using RAGAS metrics.

        This method evaluates:
        1. Context precision: Are the retrieved contexts relevant?
        2. Faithfulness: Does the answer stick to the provided contexts?
        3. Answer relevancy: Is the answer relevant to the question?
        4. Context recall (optional): Did we retrieve all necessary information?

        Args:
            question (str): The question asked by the user
            answer (str): The generated answer to evaluate
            contexts (List[str]): List of retrieved context strings
            ground_truth (Optional[str]): Optional reference answer for context_recall

        Returns:
            Dict[str, float]: Dictionary with metric scores (all in 0.0-1.0 range)
                - context_precision: 0.0-1.0
                - faithfulness: 0.0-1.0
                - answer_relevancy: 0.0-1.0
                - context_recall: 0.0-1.0 (only if ground_truth provided)

        Examples:
            >>> evaluator = RAGASEvaluator()
            >>> scores = evaluator.evaluate_single(
            ...     question="What is the DTI limit?",
            ...     answer="The DTI limit is 43%",
            ...     contexts=["Debt-to-income should not exceed 43%"]
            ... )
            >>> print(scores["faithfulness"])
            0.95

        Notes:
            - Returns neutral scores (0.5) on any error
            - Logs all evaluation results
            - Takes ~500-1000ms due to internal LLM calls
        """
        if not self._initialized:
            logger.error("❌ RAGAS evaluator not initialized properly")
            return self._neutral_scores()

        # Validate inputs
        if not question or not answer or not contexts:
            logger.error("❌ Invalid input: question, answer, and contexts are required")
            return self._neutral_scores()

        if not isinstance(contexts, list):
            logger.error(f"❌ contexts must be a list, got {type(contexts)}")
            return self._neutral_scores()

        try:
            from ragas import evaluate
            from datasets import Dataset

            # CRITICAL: RAGAS requires this exact structure
            dataset_dict = {
                "question": [question],           # List of strings
                "answer": [answer],               # List of strings
                "contexts": [contexts]            # List of LIST of strings (nested!)
            }

            # Determine which metrics to use
            metrics_to_use = [
                self.context_precision,
                self.faithfulness,
                self.answer_relevancy
            ]

            # Add ground_truth and context_recall ONLY if provided
            if ground_truth:
                dataset_dict["ground_truth"] = [ground_truth]
                metrics_to_use.append(self.context_recall)

            # Create dataset
            dataset = Dataset.from_dict(dataset_dict)

            # Run RAGAS evaluation
            logger.info(f"🔍 Evaluating: Q='{question[:50]}...' | A='{answer[:50]}...'")
            result = evaluate(dataset, metrics=metrics_to_use)

            # Extract scores
            scores = {
                "context_precision": float(result["context_precision"]),
                "faithfulness": float(result["faithfulness"]),
                "answer_relevancy": float(result["answer_relevancy"])
            }

            if ground_truth:
                scores["context_recall"] = float(result["context_recall"])

            # Log results
            logger.info(f"✅ Evaluation complete: {scores}")

            # Validate scores are in correct range
            for metric, score in scores.items():
                if not (0.0 <= score <= 1.0):
                    logger.warning(f"⚠️ {metric} score {score} outside [0.0, 1.0] range")

            return scores

        except ImportError as e:
            logger.error(f"❌ Missing dependencies: {e}")
            logger.error("Install with: pip install ragas datasets")
            return self._neutral_scores()
        except Exception as e:
            logger.error(f"❌ RAGAS evaluation failed: {e}")
            return self._neutral_scores()

    def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluate multiple question-answer pairs and return average scores.

        This is more efficient than calling evaluate_single() repeatedly because
        RAGAS can batch LLM calls internally.

        Args:
            questions (List[str]): List of questions
            answers (List[str]): List of corresponding answers
            contexts_list (List[List[str]]): List of context lists (nested!)
            ground_truths (Optional[List[str]]): Optional list of reference answers

        Returns:
            Dict[str, float]: Dictionary with average metric scores

        Examples:
            >>> evaluator = RAGASEvaluator()
            >>> scores = evaluator.evaluate_batch(
            ...     questions=["Q1", "Q2"],
            ...     answers=["A1", "A2"],
            ...     contexts_list=[["C1"], ["C2"]]
            ... )
            >>> print(scores["faithfulness"])
            0.87

        Notes:
            - All input lists must have the same length
            - Returns neutral scores (0.5) on error
            - More efficient than multiple evaluate_single() calls
        """
        if not self._initialized:
            logger.error("❌ RAGAS evaluator not initialized properly")
            return self._neutral_scores()

        # Validate input lengths
        if len(questions) != len(answers) or len(questions) != len(contexts_list):
            logger.error("❌ Mismatched lengths: questions, answers, and contexts_list must be same length")
            return self._neutral_scores()

        if ground_truths and len(ground_truths) != len(questions):
            logger.error("❌ ground_truths length must match questions length")
            return self._neutral_scores()

        try:
            from ragas import evaluate
            from datasets import Dataset

            # Build dataset dict
            dataset_dict = {
                "question": questions,
                "answer": answers,
                "contexts": contexts_list
            }

            # Determine metrics
            metrics_to_use = [
                self.context_precision,
                self.faithfulness,
                self.answer_relevancy
            ]

            if ground_truths:
                dataset_dict["ground_truth"] = ground_truths
                metrics_to_use.append(self.context_recall)

            # Create dataset
            dataset = Dataset.from_dict(dataset_dict)

            # Run batch evaluation
            logger.info(f"🔍 Batch evaluation: {len(questions)} QA pairs")
            result = evaluate(dataset, metrics=metrics_to_use)

            # Extract average scores
            scores = {
                "context_precision": float(result["context_precision"]),
                "faithfulness": float(result["faithfulness"]),
                "answer_relevancy": float(result["answer_relevancy"])
            }

            if ground_truths:
                scores["context_recall"] = float(result["context_recall"])

            logger.info(f"✅ Batch evaluation complete: {scores}")
            return scores

        except Exception as e:
            logger.error(f"❌ Batch evaluation failed: {e}")
            return self._neutral_scores()

    def calculate_query_product_relevancy(
        self,
        query: str,
        product_name: str,
        product_description: str
    ) -> float:
        """
        Calculate relevancy score between query and product (0-100 scale).

        This method is CRITICAL for Agent 3 integration. It uses RAGAS's
        answer_relevancy metric internally to judge how well a product matches
        a search query. The score is scaled to 0-100 for easier interpretation.

        Args:
            query (str): User's search query (e.g., "laptop for programming")
            product_name (str): Product name (e.g., "Dell XPS 15")
            product_description (str): Product description

        Returns:
            float: Relevancy score in 0.0-100.0 range
                - 0-30: Poor match
                - 30-60: Moderate match
                - 60-80: Good match
                - 80-100: Excellent match
                - 50.0: Neutral (returned on error)

        Examples:
            >>> evaluator = RAGASEvaluator()
            >>> score = evaluator.calculate_query_product_relevancy(
            ...     query="laptop for programming",
            ...     product_name="Dell XPS 15",
            ...     product_description="High-performance laptop with 16GB RAM"
            ... )
            >>> print(score)
            87.5

        Notes:
            - This is used by Agent 3 for RAGAS re-ranking (20% weight)
            - Returns 50.0 (neutral) on any error
            - Takes ~500-1000ms due to internal LLM calls
        """
        if not self._initialized:
            logger.error("❌ RAGAS evaluator not initialized properly")
            return 50.0  # Neutral score

        if not query or not product_name:
            logger.error("❌ query and product_name are required")
            return 50.0

        try:
            from ragas import evaluate
            from datasets import Dataset

            # Construct question and answer for relevancy evaluation
            question = query
            answer = f"{product_name}: {product_description}"

            # Use answer_relevancy metric to judge query-product match
            dataset_dict = {
                "question": [question],
                "answer": [answer],
                "contexts": [[answer]]  # Use product info as context
            }

            dataset = Dataset.from_dict(dataset_dict)

            # Evaluate using answer_relevancy only
            result = evaluate(dataset, metrics=[self.answer_relevancy])

            # Extract score and scale to 0-100
            ragas_score = float(result["answer_relevancy"])  # 0.0-1.0
            scaled_score = ragas_score * 100.0  # 0.0-100.0

            logger.info(
                f"🎯 Relevancy: '{query}' → '{product_name}' = {scaled_score:.2f}/100"
            )

            return scaled_score

        except Exception as e:
            logger.error(f"❌ Relevancy calculation failed: {e}")
            return 50.0  # Neutral score on error

    def _neutral_scores(self) -> Dict[str, float]:
        """
        Return neutral scores (0.5) for all metrics.

        This is used as a fallback when evaluation fails. 0.5 represents
        "uncertain" - neither good nor bad.

        Returns:
            Dict[str, float]: All scores set to 0.5
        """
        return {
            "context_precision": 0.5,
            "faithfulness": 0.5,
            "answer_relevancy": 0.5
        }


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

def example_agent2_usage():
    """
    Example: How Agent 2 (Financial Analyzer) uses RAGAS

    Agent 2 uses RAGAS to validate that retrieved financial rules
    are relevant to the affordability question and that the generated
    answer is faithful to those rules (no hallucinations).
    """
    print("=" * 60)
    print("EXAMPLE 1: Agent 2 (Financial Analyzer)")
    print("=" * 60)

    evaluator = RAGASEvaluator()

    # Simulate Agent 2's RAG process
    question = "Is this $899 laptop affordable for $5000 monthly income?"

    retrieved_contexts = [
        "Debt-to-income ratio should not exceed 43%",
        "Monthly payment should not exceed 15% of income",
        "Emergency fund should cover 3-6 months expenses"
    ]

    answer = "Yes, affordable. DTI is 38%, monthly payment is $75 (1.5% of income)."

    # Evaluate RAG quality
    scores = evaluator.evaluate_single(question, answer, retrieved_contexts)

    print(f"\n📊 Evaluation Results:")
    print(f"   Context Precision: {scores['context_precision']:.2f}")
    print(f"   Faithfulness: {scores['faithfulness']:.2f}")
    print(f"   Answer Relevancy: {scores['answer_relevancy']:.2f}")

    # Agent 2 validation logic
    print(f"\n🔍 Agent 2 Validation:")

    if scores["faithfulness"] < 0.9:
        print("   ⚠️ Warning: Answer may contain hallucinations")
    else:
        print("   ✅ Answer is faithful to retrieved context")

    if scores["context_precision"] < 0.85:
        print("   ⚠️ Warning: Retrieved contexts may not be relevant")
    else:
        print("   ✅ Retrieved contexts are relevant")

    print()


def example_agent3_usage():
    """
    Example: How Agent 3 (Recommender) uses RAGAS

    Agent 3 uses RAGAS to calculate how relevant each product is
    to the user's search query. This score contributes 20% to the
    final composite ranking score.

    Final Score = 0.4*Thompson + 0.2*Financial + 0.2*RAGAS + 0.2*Vector
    """
    print("=" * 60)
    print("EXAMPLE 2: Agent 3 (Product Recommender)")
    print("=" * 60)

    evaluator = RAGASEvaluator()

    # Simulate Agent 3's re-ranking process
    query = "laptop for programming"

    products = [
        {
            "name": "Dell XPS 15",
            "description": "High-performance laptop with 16GB RAM, Intel i7, ideal for development"
        },
        {
            "name": "Gaming Mouse",
            "description": "RGB gaming mouse with 16000 DPI sensor"
        }
    ]

    print(f"\n🔍 Query: '{query}'\n")

    for product in products:
        relevancy_score = evaluator.calculate_query_product_relevancy(
            query,
            product["name"],
            product["description"]
        )

        # Agent 3 normalizes to 0.0-1.0 and applies 0.2 weight
        normalized_score = relevancy_score / 100.0
        weighted_score = normalized_score * 0.2

        print(f"📦 {product['name']}")
        print(f"   RAGAS Relevancy: {relevancy_score:.2f}/100")
        print(f"   Weighted (20%): {weighted_score:.4f}")
        print()


def example_agent4_usage():
    """
    Example: How Agent 4 (Explainer) uses RAGAS

    Agent 4 uses RAGAS to verify that Gemini-generated explanations
    are faithful to the retrieved context. If faithfulness is too low,
    Agent 4 regenerates the explanation (max 2 retries).
    """
    print("=" * 60)
    print("EXAMPLE 3: Agent 4 (LLM Explainer)")
    print("=" * 60)

    evaluator = RAGASEvaluator()

    # Simulate Agent 4's explanation verification
    question = "Why is this laptop recommended?"

    # Gemini-generated explanation
    explanation = (
        "This laptop is recommended because your debt-to-income ratio is 38%, "
        "which is comfortably below the 43% threshold. Your monthly payment of "
        "$75 represents only 1.5% of your income, well within safe limits."
    )

    # Retrieved context from Agent 2
    contexts = [
        "Debt-to-income ratio should not exceed 43%",
        "Your current DTI: 38%",
        "Monthly payment should not exceed 15% of income",
        "Your payment-to-income ratio: 1.5%"
    ]

    # Evaluate explanation faithfulness
    scores = evaluator.evaluate_single(question, explanation, contexts)

    print(f"\n📊 Explanation Evaluation:")
    print(f"   Faithfulness: {scores['faithfulness']:.2f}")
    print(f"   Answer Relevancy: {scores['answer_relevancy']:.2f}")

    print(f"\n🔍 Agent 4 Decision:")

    if scores["faithfulness"] >= 0.9:
        print("   ✅ Explanation is faithful to context - APPROVED")
    else:
        print("   ❌ Explanation may contain inaccuracies - REGENERATE")
        print("   (Agent 4 will retry up to 2 times)")

    print()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("=" * 60)
    print("RAGAS Evaluator - Standalone Module Tests")
    print("=" * 60)
    print()

    # Run all integration examples
    example_agent2_usage()
    example_agent3_usage()
    example_agent4_usage()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print()
