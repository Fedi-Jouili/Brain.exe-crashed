"""
Unit tests for Agent 4 (Explainer)

Run with: pytest backend/tests/test_agent4_explainer.py -v
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch


# Mock classes
class MockUserProfile:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id', 'TEST_USER')
        self.monthly_income = kwargs.get('monthly_income', 5000.0)
        self.credit_score = kwargs.get('credit_score', 720)
        self.monthly_expenses = kwargs.get('monthly_expenses', 3000.0)
        self.savings = kwargs.get('savings', 10000.0)


@pytest.fixture
def mock_user():
    """Mock user profile"""
    return MockUserProfile()


@pytest.fixture
def mock_recommendation():
    """Mock recommendation with product and affordability"""
    return {
        'rank': 1,
        'product': {
            'product_id': 'TEST001',
            'name': 'Test Laptop',
            'price': 899.99,
            'category': 'Electronics',
            'brand': 'TestBrand',
            'rating': 4.5,
            'num_reviews': 250
        },
        'affordability': {
            'can_afford_cash': True,
            'can_afford_financing': True,
            'risk_level': 'SAFE'
        },
        'scores': {
            'thompson': 0.85,
            'collaborative': 0.72,
            'final_score': 0.89
        }
    }


@pytest.fixture
def mock_state(mock_user, mock_recommendation):
    """Mock agent state"""
    return {
        'query': 'laptop for work',
        'user_profile': mock_user,
        'final_recommendations': [mock_recommendation],
        'errors': []
    }


class TestVerificationService:
    """Test fact verification layer"""

    def test_product_name_verification(self):
        """Test product name verification"""
        from agents.agent4_explainer import VerificationService

        verifier = VerificationService()

        context = {
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': False,
                'risk_level': 'SAFE'
            }
        }

        # Good explanation (mentions product name)
        good_explanation = "The Test Laptop is an affordable Electronics product from TestBrand."
        trust, violations = verifier.verify(good_explanation, context)

        assert trust > 0.80, f"Trust should be high for good explanation, got {trust:.2f}"
        assert len(violations) == 0 or all('Product name' not in v for v in violations), \
            f"Should not have product name violation, got {violations}"

    def test_price_accuracy_verification(self):
        """Test price accuracy verification"""
        from agents.agent4_explainer import VerificationService

        verifier = VerificationService()

        context = {
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': False,
                'risk_level': 'SAFE'
            }
        }

        # Incorrect price
        bad_explanation = "This Test Laptop costs $1299.99 and is from TestBrand Electronics."
        trust, violations = verifier.verify(bad_explanation, context)

        assert any('Price mismatch' in v for v in violations), \
            f"Should detect price mismatch, got violations: {violations}"
        assert trust < 0.95, f"Trust should be lower for price mismatch, got {trust:.2f}"

    def test_affordability_keyword_verification(self):
        """Test affordability keyword verification"""
        from agents.agent4_explainer import VerificationService

        verifier = VerificationService()

        context = {
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': True,
                'risk_level': 'SAFE'
            }
        }

        # Missing affordability keyword
        bad_explanation = "The Test Laptop from TestBrand is an Electronics product."
        trust, violations = verifier.verify(bad_explanation, context)

        # Should have violation for missing affordability wording
        assert any('affordability' in v.lower() or 'afford' in v.lower() for v in violations), \
            f"Should detect missing affordability wording, got: {violations}"

    def test_payment_method_verification(self):
        """Test payment method verification"""
        from agents.agent4_explainer import VerificationService

        verifier = VerificationService()

        # Cash affordable
        context_cash = {
            'product': {
                'name': 'Test Laptop',
                'price': 599.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': False,
                'risk_level': 'SAFE'
            }
        }

        # Missing "cash" keyword
        explanation_no_cash = "The Test Laptop is affordable for you in the Electronics category."
        trust, violations = verifier.verify(explanation_no_cash, context_cash)

        # Should detect missing cash mention
        assert any('cash' in v.lower() for v in violations), \
            f"Should detect missing cash mention, got: {violations}"

    def test_trust_score_bounded(self):
        """Test that trust score is bounded [0.0, 1.0]"""
        from agents.agent4_explainer import VerificationService

        verifier = VerificationService()

        context = {
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': True,
                'risk_level': 'SAFE'
            }
        }

        # Test with various explanations
        explanations = [
            "Perfect explanation with all keywords: affordable Test Laptop with cash payment in Electronics.",
            "Bad explanation with wrong price $9999.99 and missing category.",
            ""
        ]

        for explanation in explanations:
            trust, violations = verifier.verify(explanation, context)
            assert 0.0 <= trust <= 1.0, \
                f"Trust score must be [0.0, 1.0], got {trust}"

    def test_synonym_support(self):
        """Test that verification supports synonyms"""
        from agents.agent4_explainer import VerificationService

        verifier = VerificationService()

        context = {
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': False,
                'can_afford_financing': True,
                'risk_level': 'SAFE'
            }
        }

        # Use synonyms: "payment plan" instead of "financing"
        explanation = "The Test Laptop is within budget with a payment plan available in Electronics."
        trust, violations = verifier.verify(explanation, context)

        # Should accept "payment plan" as synonym for "financing"
        # and "within budget" as synonym for "affordable"
        financing_violation = any('financing' in v.lower() for v in violations)
        assert not financing_violation, \
            "Should accept 'payment plan' as synonym for 'financing'"


class TestFallbackExplanation:
    """Test fallback explanation generation"""

    def test_fallback_trust_score(self):
        """Test fallback trust score is 0.85 (not 1.0)"""
        from agents.agent4_explainer import ExplainerAgent

        agent = ExplainerAgent()

        rec = {
            'rank': 1,
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': False,
                'risk_level': 'SAFE'
            },
            'scores': {}
        }

        context = agent._gather_context(rec, {'user_profile': None, 'query': 'test'})
        fallback = agent._generate_fallback(rec, context)

        assert fallback['trust'] == 0.85, \
            f"Fallback trust should be 0.85 (epistemic humility), got {fallback['trust']}"
        assert fallback['verified'] == True, \
            "Fallback should be verified (template is consistent)"
        assert fallback['used_llm'] == False, \
            "Fallback should not claim to use LLM"
        assert fallback['type'] == 'fallback', \
            "Should be marked as fallback type"

    def test_fallback_includes_product_details(self):
        """Test fallback includes key product details"""
        from agents.agent4_explainer import ExplainerAgent

        agent = ExplainerAgent()

        rec = {
            'rank': 1,
            'product': {
                'name': 'Test Laptop',
                'price': 899.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 250
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': False,
                'risk_level': 'SAFE'
            },
            'scores': {}
        }

        context = agent._gather_context(rec, {'user_profile': None, 'query': 'test'})
        fallback = agent._generate_fallback(rec, context)

        text = fallback['text'].lower()
        assert 'test laptop' in text, "Should mention product name"
        assert 'electronics' in text, "Should mention category"
        assert 'testbrand' in text, "Should mention brand"
        assert 'cash' in text or 'afford' in text, "Should mention affordability"


class TestPrivacySafeContext:
    """Test privacy-safe context generation"""

    def test_no_raw_credit_score_in_context(self):
        """Test that raw credit score is not sent to LLM"""
        from agents.agent4_explainer import ExplainerAgent

        agent = ExplainerAgent()

        user = MockUserProfile(credit_score=750)

        rec = {
            'product': {
                'name': 'Test', 'price': 100, 'category': 'Test',
                'brand': 'Test', 'rating': 4.0, 'num_reviews': 10
            },
            'affordability': {'can_afford_cash': True, 'can_afford_financing': False, 'risk_level': 'SAFE'},
            'scores': {}
        }

        context = agent._gather_context(rec, {'user_profile': user, 'query': 'test'})

        # Should have financial_standing as label, not raw credit score
        assert 'financial_standing' in context, "Should have financial_standing"
        assert context['financial_standing'] == 'excellent', \
            f"Credit score 750 should map to 'excellent', got {context['financial_standing']}"

        # Should NOT have raw credit_score
        assert 'credit_score' not in str(context), \
            "Should not expose raw credit_score in context"

    def test_credit_score_anonymization(self):
        """Test credit score to label mapping"""
        from agents.agent4_explainer import ExplainerAgent

        agent = ExplainerAgent()

        test_cases = [
            (780, 'excellent'),   # ≥ 750
            (720, 'good'),        # 700-749
            (670, 'moderate'),    # 650-699
            (620, 'rebuilding')   # < 650
        ]

        for credit_score, expected_label in test_cases:
            user = MockUserProfile(credit_score=credit_score)
            rec = {
                'product': {
                    'name': 'Test', 'price': 100, 'category': 'Test',
                    'brand': 'Test', 'rating': 4.0, 'num_reviews': 10
                },
                'affordability': {'can_afford_cash': True, 'can_afford_financing': False, 'risk_level': 'SAFE'},
                'scores': {}
            }

            context = agent._gather_context(rec, {'user_profile': user, 'query': 'test'})

            assert context['financial_standing'] == expected_label, \
                f"Credit score {credit_score} should map to '{expected_label}', got '{context['financial_standing']}'"


class TestLLMRegeneration:
    """Test LLM regeneration and repetition detection"""

    @pytest.mark.skip(reason="Requires Gemini API key")
    def test_llm_regeneration_on_low_trust(self):
        """Test LLM regenerates on low trust score"""
        # Would require mocking Gemini API
        pass

    @pytest.mark.skip(reason="Requires Gemini API key")
    def test_repetition_detection(self):
        """Test that repetition detection prevents infinite loops"""
        # Would require mocking Gemini API to return same text twice
        pass

    @pytest.mark.skip(reason="Requires Gemini API key")
    def test_max_2_regeneration_attempts(self):
        """Test maximum 2 regeneration attempts"""
        # Would require mocking Gemini API
        pass


class TestAgent4Execution:
    """Test Agent 4 execution with full state"""

    def test_adds_explanation_to_recommendations(self, mock_state):
        """Test that explanations are added to recommendations"""
        from agents.agent4_explainer import explainer_agent

        result = explainer_agent.execute(mock_state)

        assert len(result['final_recommendations']) > 0, "Should have recommendations"

        for rec in result['final_recommendations']:
            assert 'explanation' in rec, "Should add explanation to each recommendation"

            explanation = rec['explanation']
            assert 'text' in explanation, "Explanation should have text"
            assert 'trust' in explanation, "Explanation should have trust score"
            assert 'verified' in explanation, "Explanation should have verified flag"
            assert 'violations' in explanation, "Explanation should have violations list"
            assert 'used_llm' in explanation, "Explanation should indicate LLM usage"
            assert 'type' in explanation, "Explanation should have type"

    def test_trust_scores_bounded(self, mock_state):
        """Test that trust scores are bounded [0.0, 1.0]"""
        from agents.agent4_explainer import explainer_agent

        result = explainer_agent.execute(mock_state)

        for rec in result['final_recommendations']:
            if 'explanation' in rec:
                trust = rec['explanation']['trust']
                assert 0.0 <= trust <= 1.0, \
                    f"Trust score must be [0.0, 1.0], got {trust}"

    def test_graceful_handling_empty_recommendations(self, mock_user):
        """Test graceful handling of empty recommendations"""
        from agents.agent4_explainer import explainer_agent

        state = {
            'query': 'test',
            'user_profile': mock_user,
            'final_recommendations': [],  # Empty
            'errors': []
        }

        result = explainer_agent.execute(state)

        # Should not crash
        assert 'agent4_execution_time' in result, "Should track execution time"
        assert len(result['final_recommendations']) == 0, "Should remain empty"

    def test_per_recommendation_error_handling(self, mock_user):
        """Test per-recommendation error handling"""
        from agents.agent4_explainer import explainer_agent

        # Create recommendation with invalid data
        invalid_rec = {
            'rank': 1,
            'product': None,  # Invalid
            'affordability': {},
            'scores': {}
        }

        state = {
            'query': 'test',
            'user_profile': mock_user,
            'final_recommendations': [invalid_rec],
            'errors': []
        }

        try:
            result = explainer_agent.execute(state)

            # Should not crash, should add error explanation
            assert len(result['final_recommendations']) > 0, "Should process recommendation"

            if 'explanation' in result['final_recommendations'][0]:
                explanation = result['final_recommendations'][0]['explanation']
                assert explanation['trust'] == 0.0, "Error explanation should have trust=0.0"
                assert explanation['verified'] == False, "Error explanation should not be verified"
                assert explanation['type'] == 'error', "Should be marked as error type"
        except Exception as e:
            pytest.fail(f"Agent should not crash on invalid recommendation: {e}")

    def test_processes_top_3_recommendations(self, mock_user, mock_recommendation):
        """Test that only top 3 recommendations are explained"""
        from agents.agent4_explainer import explainer_agent

        # Create 5 recommendations
        recommendations = [
            {**mock_recommendation, 'rank': i+1}
            for i in range(5)
        ]

        state = {
            'query': 'test',
            'user_profile': mock_user,
            'final_recommendations': recommendations,
            'errors': []
        }

        result = explainer_agent.execute(state)

        # Should have explanations for top 3 only
        explained_count = sum(1 for rec in result['final_recommendations'] if 'explanation' in rec)
        assert explained_count <= 3, f"Should explain max 3 recommendations, got {explained_count}"


class TestContractEnforcement:
    """Test contract enforcement (trust scores, immutability, etc.)"""

    def test_explanation_object_immutable(self, mock_state):
        """Test that explanation objects are created immutably"""
        from agents.agent4_explainer import explainer_agent

        original_rec = mock_state['final_recommendations'][0].copy()

        result = explainer_agent.execute(mock_state)

        # Explanation should be added, not mutated in-place
        assert 'explanation' in result['final_recommendations'][0], \
            "Explanation should be added"

        # Original product/affordability should not be mutated
        assert result['final_recommendations'][0]['product'] == original_rec['product'], \
            "Product should not be mutated"
        assert result['final_recommendations'][0]['affordability'] == original_rec['affordability'], \
            "Affordability should not be mutated"

    def test_verified_semantics(self, mock_state):
        """Test verified field semantics (factual check, not LLM confidence)"""
        from agents.agent4_explainer import explainer_agent

        result = explainer_agent.execute(mock_state)

        for rec in result['final_recommendations']:
            if 'explanation' in rec:
                explanation = rec['explanation']

                # verified: True → trust >= threshold OR fallback template
                # verified: False → trust < threshold OR violations detected
                if explanation['verified']:
                    # Fallback can be verified with trust=0.85
                    # LLM can be verified with trust >= 0.70
                    assert explanation['trust'] >= 0.70 or explanation['type'] == 'fallback', \
                        f"verified=True requires trust≥0.70 or fallback, got trust={explanation['trust']}, type={explanation['type']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
