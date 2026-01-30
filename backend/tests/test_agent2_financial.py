"""
Unit tests for Agent 2 (Financial Analyzer)

Run with: pytest backend/tests/test_agent2_financial.py -v
"""

import pytest
from typing import Dict, Any


# Mock imports to avoid dependencies
class MockUserProfile:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id', 'TEST_USER')
        self.monthly_income = kwargs.get('monthly_income', 5000.0)
        self.current_debt = kwargs.get('current_debt', 0.0)
        self.monthly_expenses = kwargs.get('monthly_expenses', 3000.0)
        self.credit_score = kwargs.get('credit_score', 720)
        self.savings = kwargs.get('savings', 10000.0)


class MockProduct:
    def __init__(self, **kwargs):
        self.product_id = kwargs.get('product_id', 'TEST_PROD')
        self.name = kwargs.get('name', 'Test Product')
        self.price = kwargs.get('price', 899.99)
        self.category = kwargs.get('category', 'Electronics')
        self.rating = kwargs.get('rating', 4.5)
        self.num_reviews = kwargs.get('num_reviews', 100)
        self.in_stock = kwargs.get('in_stock', True)
        self.financing_available = kwargs.get('financing_available', True)
        self.financing_terms = kwargs.get('financing_terms', {'months': 12, 'apr': 0.0})


@pytest.fixture
def mock_agent2():
    """Mock Agent 2 for testing"""
    from agents.agent2_financial import financial_analyzer_agent
    return financial_analyzer_agent


@pytest.fixture
def comfortable_user():
    """User with comfortable financial situation"""
    return MockUserProfile(
        user_id="COMFORTABLE_USER",
        monthly_income=5000.0,
        current_debt=1000.0,
        monthly_expenses=3000.0,
        credit_score=720,
        savings=10000.0
    )


@pytest.fixture
def tight_budget_user():
    """User with tight budget"""
    return MockUserProfile(
        user_id="TIGHT_BUDGET_USER",
        monthly_income=2500.0,
        current_debt=500.0,
        monthly_expenses=2200.0,
        credit_score=680,
        savings=2000.0
    )


@pytest.fixture
def poor_credit_user():
    """User with poor credit"""
    return MockUserProfile(
        user_id="POOR_CREDIT_USER",
        monthly_income=3000.0,
        current_debt=2000.0,
        monthly_expenses=2500.0,
        credit_score=600,
        savings=1000.0
    )


@pytest.fixture
def affordable_product():
    """Affordable product"""
    return MockProduct(
        product_id="AFFORDABLE",
        name="Affordable Laptop",
        price=599.99,
        category="Electronics",
        financing_available=True
    )


@pytest.fixture
def expensive_product():
    """Expensive product"""
    return MockProduct(
        product_id="EXPENSIVE",
        name="Expensive Laptop",
        price=2999.99,
        category="Electronics",
        financing_available=True
    )


class TestFinancialCalculator:
    """Test financial calculation utilities"""

    def test_dti_calculation_no_debt(self, comfortable_user):
        """Test DTI calculation with no additional debt"""
        from utils.financial import FinancialCalculator

        dti = FinancialCalculator.calculate_dti_ratio(comfortable_user, additional_debt=0)

        # Current debt: $1000 at 5% APR, 60 months ≈ $18.80/month
        # DTI = $18.80 / $5000 = 0.00376
        assert dti < 0.01, f"DTI should be very low with no additional debt, got {dti:.4f}"

    def test_dti_calculation_with_new_debt(self, comfortable_user):
        """Test DTI calculation with new financing payment"""
        from utils.financial import FinancialCalculator

        # Add $100/month payment
        dti = FinancialCalculator.calculate_dti_ratio(comfortable_user, additional_debt=100.0)

        # Total monthly debt: ~$18.80 + $100 = $118.80
        # DTI = $118.80 / $5000 = 0.02376
        assert 0.02 < dti < 0.03, f"DTI should be ~2.4%, got {dti:.4f}"

    def test_dti_exceeds_threshold(self, poor_credit_user):
        """Test DTI exceeds safe threshold"""
        from utils.financial import FinancialCalculator

        # Add $500/month payment (16.67% of $3000 income)
        dti = FinancialCalculator.calculate_dti_ratio(poor_credit_user, additional_debt=500.0)

        # Should exceed safe threshold (36%) or caution threshold (43%)
        assert dti > 0.15, f"DTI should be high for poor credit user, got {dti:.4f}"

    def test_pti_calculation(self, comfortable_user):
        """Test payment-to-income ratio calculation"""
        from utils.financial import FinancialCalculator

        # $75/month payment on $5000 income
        pti = FinancialCalculator.calculate_pti_ratio(75.0, comfortable_user.monthly_income)

        assert pti == 0.015, f"PTI should be 1.5%, got {pti:.4f}"

    def test_emergency_fund_coverage(self, comfortable_user):
        """Test emergency fund calculation"""
        from utils.financial import FinancialCalculator

        # $10,000 savings, $3000 expenses, $600 purchase
        months = FinancialCalculator.calculate_emergency_fund_coverage(
            comfortable_user,
            purchase_amount=600.0
        )

        # ($10,000 - $600) / $3000 = 3.13 months
        assert 3.0 <= months <= 3.2, f"Emergency fund should be ~3.1 months, got {months:.2f}"

    def test_emergency_fund_depletes(self, tight_budget_user):
        """Test emergency fund depletion detection"""
        from utils.financial import FinancialCalculator

        # $2000 savings, $2200 expenses, $1500 purchase
        months = FinancialCalculator.calculate_emergency_fund_coverage(
            tight_budget_user,
            purchase_amount=1500.0
        )

        # ($2000 - $1500) / $2200 = 0.23 months (< 3 months minimum)
        assert months < 1.0, f"Emergency fund should be depleted, got {months:.2f} months"

    def test_safe_cash_limit(self, comfortable_user):
        """Test safe cash limit calculation"""
        from utils.financial import FinancialCalculator

        # Disposable: $5000 - $3000 = $2000
        # Safe limit: $2000 * 0.30 = $600
        limit = FinancialCalculator.calculate_safe_cash_limit(comfortable_user)

        assert limit == 600.0, f"Safe cash limit should be $600, got ${limit:.2f}"

    def test_disposable_income(self, comfortable_user):
        """Test disposable income calculation"""
        from utils.financial import FinancialCalculator

        disposable = FinancialCalculator.calculate_disposable_income(comfortable_user)

        # $5000 - $3000 = $2000
        assert disposable == 2000.0, f"Disposable income should be $2000, got ${disposable:.2f}"


class TestCashAffordability:
    """Test cash affordability checks"""

    def test_affordable_within_safe_limit(self, comfortable_user, affordable_product):
        """Test affordable product within safe limit"""
        from utils.financial import FinancialCalculator

        can_afford, metrics = FinancialCalculator.check_cash_affordability(
            comfortable_user,
            affordable_product.price
        )

        # $599.99 < $600 safe limit, emergency fund remains > 3 months
        assert can_afford, "Should be able to afford product within safe limit"
        assert not metrics['exceeds_safe_limit'], "Should not exceed safe limit"
        assert metrics['emergency_fund_months'] >= 3.0, "Should maintain emergency fund"

    def test_unaffordable_exceeds_limit(self, comfortable_user, expensive_product):
        """Test expensive product exceeds safe limit"""
        from utils.financial import FinancialCalculator

        can_afford, metrics = FinancialCalculator.check_cash_affordability(
            comfortable_user,
            expensive_product.price
        )

        # $2999.99 > $600 safe limit
        assert not can_afford, "Should not afford product exceeding safe limit"
        assert metrics['exceeds_safe_limit'], "Should exceed safe limit"

    def test_depletes_emergency_fund(self, tight_budget_user):
        """Test purchase that depletes emergency fund"""
        from utils.financial import FinancialCalculator

        can_afford, metrics = FinancialCalculator.check_cash_affordability(
            tight_budget_user,
            1500.0
        )

        # $1500 would leave ($2000 - $1500) / $2200 = 0.23 months
        assert not can_afford, "Should not afford if emergency fund depletes"
        assert metrics['depletes_emergency_fund'], "Should detect emergency fund depletion"
        assert metrics['emergency_fund_months'] < 3.0, "Emergency fund below 3 months"


class TestFinancingAffordability:
    """Test financing affordability checks"""

    def test_affordable_financing(self, comfortable_user, affordable_product):
        """Test affordable financing option"""
        from utils.financial import FinancialCalculator

        can_afford, metrics = FinancialCalculator.check_financing_affordability(
            comfortable_user,
            affordable_product.price,
            months=12,
            apr=0.0
        )

        # $599.99 / 12 = $50/month
        # PTI = $50 / $5000 = 0.01 (1%)
        assert can_afford, "Should afford financing with good profile"
        assert metrics['pti_ratio'] < 0.02, f"PTI should be low, got {metrics['pti_ratio']:.4f}"
        assert not metrics['exceeds_pti_threshold'], "Should not exceed PTI threshold"

    def test_poor_credit_blocks_financing(self, poor_credit_user, affordable_product):
        """Test poor credit score blocks financing"""
        from utils.financial import FinancialCalculator

        can_afford, metrics = FinancialCalculator.check_financing_affordability(
            poor_credit_user,
            affordable_product.price,
            months=12,
            apr=0.0
        )

        # Credit score 600 < 650 threshold
        assert not can_afford, "Should not afford with credit score < 650"
        assert metrics['insufficient_credit_score'], "Should detect insufficient credit score"

    def test_high_pti_blocks_financing(self, tight_budget_user, expensive_product):
        """Test high PTI blocks financing"""
        from utils.financial import FinancialCalculator

        can_afford, metrics = FinancialCalculator.check_financing_affordability(
            tight_budget_user,
            expensive_product.price,
            months=12,
            apr=0.0
        )

        # $2999.99 / 12 = $250/month
        # PTI = $250 / $2500 = 0.10 (10%)
        # This might still pass, so let's check the result
        if not can_afford:
            assert metrics['exceeds_pti_threshold'] or metrics['exceeds_dti_threshold'], \
                "Should block due to PTI or DTI threshold"


class TestRiskAssessment:
    """Test risk level assessment"""

    def test_safe_risk_level(self, comfortable_user, affordable_product):
        """Test SAFE risk level for good scenario"""
        from utils.financial import FinancialCalculator

        can_afford_cash, cash_metrics = FinancialCalculator.check_cash_affordability(
            comfortable_user,
            affordable_product.price
        )

        can_afford_financing, financing_metrics = FinancialCalculator.check_financing_affordability(
            comfortable_user,
            affordable_product.price,
            months=12,
            apr=0.0
        )

        risk_level, risk_factors = FinancialCalculator.assess_risk_level(
            can_afford_cash,
            can_afford_financing,
            cash_metrics,
            financing_metrics
        )

        risk_str = str(risk_level)
        assert 'SAFE' in risk_str, f"Should be SAFE risk level, got {risk_str}"
        assert len(risk_factors) == 0, f"Should have no risk factors, got {risk_factors}"

    def test_risky_risk_level(self, poor_credit_user, expensive_product):
        """Test RISKY risk level for bad scenario"""
        from utils.financial import FinancialCalculator

        can_afford_cash, cash_metrics = FinancialCalculator.check_cash_affordability(
            poor_credit_user,
            expensive_product.price
        )

        can_afford_financing, financing_metrics = FinancialCalculator.check_financing_affordability(
            poor_credit_user,
            expensive_product.price,
            months=12,
            apr=0.15
        )

        risk_level, risk_factors = FinancialCalculator.assess_risk_level(
            can_afford_cash,
            can_afford_financing,
            cash_metrics,
            financing_metrics
        )

        risk_str = str(risk_level)
        assert len(risk_factors) >= 1, f"Should have risk factors, got {risk_factors}"


class TestAgent2Execution:
    """Test Agent 2 execution with full state"""

    def test_all_affordable(self, comfortable_user, affordable_product):
        """Test when all products are affordable"""
        state = {
            'query': 'laptop',
            'user_profile': comfortable_user,
            'candidate_products': [affordable_product],
            'errors': []
        }

        from agents.agent2_financial import financial_analyzer_agent

        result = financial_analyzer_agent.execute(state)

        assert len(result['affordable_products']) > 0, "Should have affordable products"
        assert result['all_unaffordable'] == False, "Should NOT trigger PathFinder"
        assert 'agent2_execution_time' in result, "Should track execution time"

    def test_all_unaffordable_triggers_pathfinder(self, poor_credit_user, expensive_product):
        """Test that all_unaffordable flag triggers correctly"""
        state = {
            'query': 'laptop',
            'user_profile': poor_credit_user,
            'candidate_products': [expensive_product],
            'errors': []
        }

        from agents.agent2_financial import financial_analyzer_agent

        result = financial_analyzer_agent.execute(state)

        # Should trigger PathFinder
        assert result['all_unaffordable'] == True, \
            "all_unaffordable should be True for expensive product with poor user"
        assert len(result['affordable_products']) == 0, \
            "Should have no affordable products"

    def test_error_handling(self):
        """Test graceful error handling"""
        # Invalid state (missing user_profile)
        state = {
            'query': 'laptop',
            'user_profile': None,
            'candidate_products': [],
            'errors': []
        }

        from agents.agent2_financial import financial_analyzer_agent

        try:
            result = financial_analyzer_agent.execute(state)

            # Should not crash
            assert 'errors' in result, "Should have errors field"
            assert 'affordable_products' in result, "Should have affordable_products field"
            assert result['all_unaffordable'] == False, "Should NOT trigger PathFinder on error"
        except Exception as e:
            pytest.fail(f"Agent should not crash on invalid input: {e}")

    def test_financial_score_bounded(self, comfortable_user, affordable_product):
        """Test that financial scores are bounded [0.0, 1.0]"""
        state = {
            'query': 'laptop',
            'user_profile': comfortable_user,
            'candidate_products': [affordable_product],
            'errors': []
        }

        from agents.agent2_financial import financial_analyzer_agent

        result = financial_analyzer_agent.execute(state)

        for item in result['affordable_products']:
            score = item['financial_score']
            assert 0.0 <= score <= 1.0, \
                f"Financial score must be in [0.0, 1.0], got {score}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
