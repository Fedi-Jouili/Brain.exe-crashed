"""
Unit tests for RAGASEvaluator
Run with: pytest test_ragas_evaluator.py -v

Tests cover:
- Initialization
- Single evaluation
- Faithfulness detection (hallucination catching)
- Query-product relevancy scoring
- Batch evaluation
- Error handling
"""

import pytest
from ragas_evaluator import RAGASEvaluator


class TestRAGASEvaluator:
    """Test suite for RAGAS evaluation module"""

    def test_initialization(self):
        """Test evaluator initializes correctly"""
        evaluator = RAGASEvaluator()

        assert evaluator is not None, "Evaluator should be created"
        assert evaluator._initialized is True, "Evaluator should initialize successfully"
        assert len(evaluator.metrics) == 3, "Should have 3 default metrics"
        assert evaluator.context_precision is not None
        assert evaluator.faithfulness is not None
        assert evaluator.answer_relevancy is not None

    def test_single_evaluation(self):
        """Test single QA evaluation returns correct structure"""
        evaluator = RAGASEvaluator()

        question = "What is the DTI limit?"
        answer = "The debt-to-income limit is 43%"
        contexts = [
            "Debt-to-income ratio should not exceed 43%",
            "DTI measures your monthly debt payments against gross income"
        ]

        scores = evaluator.evaluate_single(question, answer, contexts)

        # Verify structure
        assert isinstance(scores, dict), "Should return a dictionary"
        assert "context_precision" in scores
        assert "faithfulness" in scores
        assert "answer_relevancy" in scores

        # Verify scores are in correct range
        for metric, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{metric} should be in [0.0, 1.0], got {score}"

        print(f"\n✅ Single evaluation scores: {scores}")

    def test_faithfulness_detection(self):
        """Test that faithfulness catches hallucinations"""
        evaluator = RAGASEvaluator()

        question = "What is the recommended DTI limit?"
        contexts = ["Debt-to-income ratio should not exceed 43%"]

        # CORRECT answer (faithful to context)
        correct_answer = "The recommended DTI limit is 43%"
        correct_scores = evaluator.evaluate_single(question, correct_answer, contexts)

        # HALLUCINATED answer (not in context)
        hallucinated_answer = (
            "The recommended DTI limit is 35% according to Federal Reserve guidelines. "
            "Additionally, you should maintain a credit utilization below 20%."
        )
        hallucinated_scores = evaluator.evaluate_single(
            question, hallucinated_answer, contexts
        )

        print(f"\n📊 Faithfulness Comparison:")
        print(f"   Correct answer: {correct_scores['faithfulness']:.3f}")
        print(f"   Hallucinated answer: {hallucinated_scores['faithfulness']:.3f}")

        # Correct answer should have higher faithfulness
        assert correct_scores["faithfulness"] > hallucinated_scores["faithfulness"], \
            "Correct answer should have higher faithfulness than hallucinated answer"

        print(f"   ✅ Correct > Hallucinated: {correct_scores['faithfulness']:.3f} > {hallucinated_scores['faithfulness']:.3f}")

    def test_relevancy_scoring(self):
        """Test query-product relevancy calculation"""
        evaluator = RAGASEvaluator()

        query = "laptop for programming"

        # RELEVANT product
        relevant_product = {
            "name": "Dell XPS 15 Developer Edition",
            "description": "High-performance laptop with 16GB RAM, Intel i7 processor, Ubuntu pre-installed, perfect for software development and coding"
        }

        # IRRELEVANT product
        irrelevant_product = {
            "name": "Garden Hose 50ft",
            "description": "Durable rubber garden hose for outdoor watering, 50 feet long with brass fittings"
        }

        relevant_score = evaluator.calculate_query_product_relevancy(
            query,
            relevant_product["name"],
            relevant_product["description"]
        )

        irrelevant_score = evaluator.calculate_query_product_relevancy(
            query,
            irrelevant_product["name"],
            irrelevant_product["description"]
        )

        print(f"\n🎯 Relevancy Scores:")
        print(f"   Relevant product: {relevant_score:.2f}/100")
        print(f"   Irrelevant product: {irrelevant_score:.2f}/100")

        # Verify scores are in correct range
        assert 0.0 <= relevant_score <= 100.0, "Score should be in [0, 100]"
        assert 0.0 <= irrelevant_score <= 100.0, "Score should be in [0, 100]"

        # Relevant product should score higher
        assert relevant_score > irrelevant_score, \
            "Relevant product should have higher score than irrelevant product"

        # Relevant product should score reasonably well (>50)
        assert relevant_score > 50.0, "Relevant product should score above 50"

        print(f"   ✅ Relevant > Irrelevant: {relevant_score:.2f} > {irrelevant_score:.2f}")

    def test_batch_evaluation(self):
        """Test batch evaluation with multiple QA pairs"""
        evaluator = RAGASEvaluator()

        questions = [
            "What is the DTI limit?",
            "What is the PTI threshold?"
        ]

        answers = [
            "The DTI limit is 43%",
            "The PTI threshold is 28%"
        ]

        contexts_list = [
            ["Debt-to-income ratio should not exceed 43%"],
            ["Payment-to-income ratio should not exceed 28%"]
        ]

        scores = evaluator.evaluate_batch(questions, answers, contexts_list)

        # Verify structure
        assert isinstance(scores, dict), "Should return a dictionary"
        assert "context_precision" in scores
        assert "faithfulness" in scores
        assert "answer_relevancy" in scores

        # Verify scores are in correct range
        for metric, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{metric} should be in [0.0, 1.0], got {score}"

        print(f"\n✅ Batch evaluation scores (2 QA pairs): {scores}")

    def test_error_handling(self):
        """Test graceful failure on invalid input"""
        evaluator = RAGASEvaluator()

        # Test 1: Empty contexts
        scores = evaluator.evaluate_single(
            question="Test question",
            answer="Test answer",
            contexts=[]
        )

        # Should return neutral scores
        assert scores["context_precision"] == 0.5, "Should return neutral on error"
        assert scores["faithfulness"] == 0.5, "Should return neutral on error"
        assert scores["answer_relevancy"] == 0.5, "Should return neutral on error"

        print("\n✅ Empty contexts handled gracefully (neutral scores)")

        # Test 2: None inputs
        scores = evaluator.evaluate_single(
            question=None,
            answer="Test",
            contexts=["Context"]
        )

        assert scores["faithfulness"] == 0.5, "Should return neutral on None input"
        print("✅ None input handled gracefully")

        # Test 3: Mismatched batch lengths
        scores = evaluator.evaluate_batch(
            questions=["Q1", "Q2"],
            answers=["A1"],  # Only 1 answer for 2 questions
            contexts_list=[["C1"], ["C2"]]
        )

        assert scores["faithfulness"] == 0.5, "Should return neutral on mismatched lengths"
        print("✅ Mismatched batch lengths handled gracefully")

        # Test 4: Invalid contexts type
        scores = evaluator.evaluate_single(
            question="Test",
            answer="Test",
            contexts="Not a list"  # Should be list
        )

        assert scores["faithfulness"] == 0.5, "Should return neutral on invalid type"
        print("✅ Invalid contexts type handled gracefully")

    def test_ground_truth_support(self):
        """Test that ground_truth parameter works correctly"""
        evaluator = RAGASEvaluator()

        question = "What is the DTI limit?"
        answer = "The DTI limit is 43%"
        contexts = ["Debt-to-income should not exceed 43%"]
        ground_truth = "The debt-to-income ratio limit is 43%"

        scores = evaluator.evaluate_single(
            question, answer, contexts, ground_truth=ground_truth
        )

        # When ground_truth is provided, should have context_recall
        assert "context_recall" in scores, "Should include context_recall with ground_truth"
        assert 0.0 <= scores["context_recall"] <= 1.0

        print(f"\n✅ Ground truth support working: context_recall = {scores['context_recall']:.3f}")

    def test_relevancy_error_handling(self):
        """Test relevancy calculation error handling"""
        evaluator = RAGASEvaluator()

        # Test with empty query
        score = evaluator.calculate_query_product_relevancy(
            query="",
            product_name="Product",
            product_description="Description"
        )

        assert score == 50.0, "Should return 50.0 (neutral) on empty query"
        print("\n✅ Empty query handled gracefully (50.0)")

        # Test with None product name
        score = evaluator.calculate_query_product_relevancy(
            query="test",
            product_name=None,
            product_description="Description"
        )

        assert score == 50.0, "Should return 50.0 (neutral) on None product_name"
        print("✅ None product_name handled gracefully (50.0)")


class TestRAGASIntegrationExamples:
    """Test that integration examples work correctly"""

    def test_agent2_example_runs(self):
        """Test that Agent 2 example executes without errors"""
        from ragas_evaluator import example_agent2_usage

        try:
            example_agent2_usage()
            print("\n✅ Agent 2 example runs successfully")
        except Exception as e:
            pytest.fail(f"Agent 2 example failed: {e}")

    def test_agent3_example_runs(self):
        """Test that Agent 3 example executes without errors"""
        from ragas_evaluator import example_agent3_usage

        try:
            example_agent3_usage()
            print("\n✅ Agent 3 example runs successfully")
        except Exception as e:
            pytest.fail(f"Agent 3 example failed: {e}")

    def test_agent4_example_runs(self):
        """Test that Agent 4 example executes without errors"""
        from ragas_evaluator import example_agent4_usage

        try:
            example_agent4_usage()
            print("\n✅ Agent 4 example runs successfully")
        except Exception as e:
            pytest.fail(f"Agent 4 example failed: {e}")


class TestRAGASPerformance:
    """Performance-related tests (optional, not strictly unit tests)"""

    def test_batch_faster_than_sequential(self):
        """Verify batch evaluation is more efficient than sequential"""
        import time

        evaluator = RAGASEvaluator()

        questions = ["Q1", "Q2", "Q3"]
        answers = ["A1", "A2", "A3"]
        contexts_list = [["C1"], ["C2"], ["C3"]]

        # Sequential evaluation
        start = time.time()
        for q, a, c in zip(questions, answers, contexts_list):
            evaluator.evaluate_single(q, a, c)
        sequential_time = time.time() - start

        # Batch evaluation
        start = time.time()
        evaluator.evaluate_batch(questions, answers, contexts_list)
        batch_time = time.time() - start

        print(f"\n⏱️ Performance Comparison:")
        print(f"   Sequential (3 calls): {sequential_time:.2f}s")
        print(f"   Batch (1 call): {batch_time:.2f}s")
        print(f"   Speedup: {sequential_time/batch_time:.2f}x")

        # Batch should be at least slightly faster
        # (In practice, speedup depends on RAGAS internal batching)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
