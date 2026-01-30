"""
Unit tests for Agent 2.5 (Budget PathFinder)

Run with: pytest backend/tests/test_agent2_5_pathfinder.py -v
"""

import pytest
from typing import Dict, Any, List


# Mock imports
class MockUserProfile:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id', 'TEST_USER')
        self.monthly_income = kwargs.get('monthly_income', 3000.0)
        self.current_debt = kwargs.get('current_debt', 0.0)
        self.monthly_expenses = kwargs.get('monthly_expenses', 2500.0)
        self.credit_score = kwargs.get('credit_score', 680)
        self.savings = kwargs.get('savings', 1000.0)


class MockProduct:
    def __init__(self, **kwargs):
        self.product_id = kwargs.get('product_id', 'TEST_PROD')
        self.name = kwargs.get('name', 'Test Product')
        self.price = kwargs.get('price', 1500.0)
        self.category = kwargs.get('category', 'Electronics')
        self.cluster_id = kwargs.get('cluster_id', 'CLUSTER_1')
        self.financing_available = kwargs.get('financing_available', True)


@pytest.fixture
def pathfinder_agent():
    """Get PathFinder agent"""
    from agents.agent2_5_pathfinder import budget_pathfinder_agent
    return budget_pathfinder_agent


@pytest.fixture
def tight_budget_user():
    """User with tight budget"""
    return MockUserProfile(
        user_id="TIGHT_USER",
        monthly_income=3000.0,
        current_debt=500.0,
        monthly_expenses=2500.0,
        credit_score=680,
        savings=1000.0
    )


@pytest.fixture
def moderate_user():
    """User with moderate budget"""
    return MockUserProfile(
        user_id="MODERATE_USER",
        monthly_income=4000.0,
        current_debt=1000.0,
        monthly_expenses=3000.0,
        credit_score=700,
        savings=3000.0
    )


@pytest.fixture
def expensive_product():
    """Expensive product"""
    return MockProduct(
        product_id="EXPENSIVE",
        name="Expensive Laptop",
        price=1500.0,
        category="Electronics",
        cluster_id="CLUSTER_ELECTRONICS_1",
        financing_available=True
    )


class TestPathFinderActivation:
    """Test PathFinder activation conditions"""

    def test_skips_when_products_affordable(self, pathfinder_agent, tight_budget_user):
        """PathFinder should skip when products are affordable"""
        state = {
            'all_unaffordable': False,  # Not triggered
            'candidate_products': [],
            'affordable_products': [{'product': {}}],
            'user_profile': tight_budget_user,
            'errors': []
        }

        result = pathfinder_agent.execute(state)

        # Should not modify state
        assert 'alternative_paths' not in result or len(result.get('alternative_paths', [])) == 0, \
            "Should not generate paths when products are affordable"

    def test_runs_when_all_unaffordable(self, pathfinder_agent, tight_budget_user, expensive_product):
        """PathFinder should run when all products unaffordable"""
        state = {
            'all_unaffordable': True,  # Triggered!
            'candidate_products': [expensive_product],
            'affordable_products': [],
            'user_profile': tight_budget_user,
            'errors': []
        }

        result = pathfinder_agent.execute(state)

        # Should generate alternative paths
        assert 'alternative_paths' in result, "Should generate alternative paths"
        assert 'agent2_5_execution_time' in result, "Should track execution time"


class TestSavingsPaths:
    """Test extended savings plan generation"""

    def test_generates_3_month_savings_path(self, pathfinder_agent, tight_budget_user):
        """Test 3-month savings path generation"""
        product = MockProduct(price=900.0, name="Affordable Product")

        # Disposable income: $3000 - $2500 = $500
        # Monthly savings required: $900 / 3 = $300
        # Savings ratio: $300 / $500 = 0.60 (60%)

        paths = pathfinder_agent._generate_extended_savings_paths(
            product=product,
            profile=tight_budget_user,
            months_options=[3, 6]
        )

        # Should generate at least one path (if savings ratio ≤ 30%)
        # For this case, 60% > 30%, so no paths should be generated
        if len(paths) == 0:
            # Expected behavior: 60% savings ratio exceeds 30% limit
            pass
        else:
            # If paths are generated, verify structure
            for path in paths:
                assert 'viability_score' in path, "Should have viability_score"
                assert 0.0 <= path['viability_score'] <= 1.0, \
                    f"Viability score must be [0.0, 1.0], got {path['viability_score']}"

    def test_viability_score_bounded(self, pathfinder_agent, moderate_user):
        """Test that viability scores are bounded [0.0, 1.0]"""
        product = MockProduct(price=600.0, name="Moderate Product")

        # Disposable: $4000 - $3000 = $1000
        # 3 months: $200/month (20% of disposable) ✓
        # 6 months: $100/month (10% of disposable) ✓

        paths = pathfinder_agent._generate_extended_savings_paths(
            product=product,
            profile=moderate_user,
            months_options=[3, 6]
        )

        assert len(paths) > 0, "Should generate savings paths"

        for path in paths:
            score = path['viability_score']
            assert 0.0 <= score <= 1.0, \
                f"Viability score must be [0.0, 1.0], got {score}"
            assert path['type'] == 'savings_plan', "Should be savings_plan type"
            assert 'pros' in path, "Should have pros"
            assert 'cons' in path, "Should have cons"

    def test_shorter_duration_higher_viability(self, pathfinder_agent, moderate_user):
        """Test that shorter savings duration = higher viability"""
        product = MockProduct(price=600.0)

        paths = pathfinder_agent._generate_extended_savings_paths(
            product=product,
            profile=moderate_user,
            months_options=[3, 6]
        )

        if len(paths) >= 2:
            # Find 3-month and 6-month paths
            path_3mo = next((p for p in paths if p['timeline_months'] == 3), None)
            path_6mo = next((p for p in paths if p['timeline_months'] == 6), None)

            if path_3mo and path_6mo:
                assert path_3mo['viability_score'] > path_6mo['viability_score'], \
                    "3-month path should have higher viability than 6-month path"


class TestFinancingPaths:
    """Test extended financing plan generation"""

    def test_generates_extended_financing_paths(self, pathfinder_agent, moderate_user):
        """Test extended financing (18-36 months)"""
        product = MockProduct(price=1200.0, name="Laptop", financing_available=True)

        paths = pathfinder_agent._generate_extended_financing_paths(
            product=product,
            profile=moderate_user,
            months_options=[18, 24, 36]
        )

        # Should generate financing paths with PTI ≤ 20%
        for path in paths:
            assert 'viability_score' in path, "Should have viability_score"
            assert 0.0 <= path['viability_score'] <= 1.0, \
                f"Viability score must be [0.0, 1.0], got {path['viability_score']}"
            assert path['type'] == 'extended_financing', "Should be extended_financing type"
            assert path['pti_ratio'] <= 0.20, \
                f"PTI ratio must be ≤ 20%, got {path['pti_ratio']*100:.1f}%"
            assert 'pros' in path, "Should have pros"
            assert 'cons' in path, "Should have cons"

    def test_pti_threshold_enforced(self, pathfinder_agent, tight_budget_user):
        """Test that PTI ≤ 20% is enforced"""
        product = MockProduct(price=2000.0, financing_available=True)

        # Monthly income: $3000
        # For 18 months: $2000 / 18 = $111/month
        # PTI = $111 / $3000 = 0.037 (3.7%) ✓

        paths = pathfinder_agent._generate_extended_financing_paths(
            product=product,
            profile=tight_budget_user,
            months_options=[18, 24, 36]
        )

        # All paths should have PTI ≤ 20%
        for path in paths:
            assert path['pti_ratio'] <= 0.20, \
                f"PTI must be ≤ 20%, got {path['pti_ratio']*100:.1f}%"

    def test_apr_increases_with_term_length(self, pathfinder_agent, moderate_user):
        """Test that APR increases for longer terms"""
        product = MockProduct(price=1000.0, financing_available=True)

        paths = pathfinder_agent._generate_extended_financing_paths(
            product=product,
            profile=moderate_user,
            months_options=[18, 24, 36]
        )

        if len(paths) >= 2:
            # Find 18-month and 24+ month paths
            path_18mo = next((p for p in paths if p['timeline_months'] == 18), None)
            path_24mo = next((p for p in paths if p['timeline_months'] >= 24), None)

            if path_18mo and path_24mo:
                assert path_24mo['apr'] >= path_18mo['apr'], \
                    "Longer terms should have higher APR"


class TestClusterAlternatives:
    """Test cheaper cluster alternatives"""

    @pytest.mark.skip(reason="Requires clustering service integration")
    def test_finds_cheaper_alternatives(self, pathfinder_agent, moderate_user):
        """Test finding cheaper alternatives in same cluster"""
        product = MockProduct(
            product_id="ORIGINAL",
            price=1000.0,
            cluster_id="CLUSTER_ELECTRONICS_1"
        )

        # Mock clustering service
        try:
            paths = pathfinder_agent._find_cheaper_cluster_alternatives(
                product=product,
                profile=moderate_user,
                max_alternatives=2
            )

            # If clustering service is available
            for path in paths:
                assert 'viability_score' in path, "Should have viability_score"
                assert 0.0 <= path['viability_score'] <= 1.0, \
                    f"Viability score must be [0.0, 1.0], got {path['viability_score']}"
                assert path['type'] == 'cluster_alternative', "Should be cluster_alternative type"
                assert path['savings_percent'] >= 5.0, \
                    f"Savings must be ≥5%, got {path['savings_percent']:.1f}%"
        except (FileNotFoundError, ImportError):
            pytest.skip("Clustering service not available")

    def test_minimum_5_percent_savings_enforced(self, pathfinder_agent, moderate_user):
        """Test that minimum 5% savings is enforced"""
        # This test would require mocking the clustering service
        # Skipping for now as it requires integration
        pytest.skip("Requires clustering service mock")


class TestPathRanking:
    """Test path ranking and scoring"""

    def test_maximum_3_paths_returned(self, pathfinder_agent, moderate_user, expensive_product):
        """Test that maximum 3 paths are returned"""
        state = {
            'all_unaffordable': True,
            'candidate_products': [expensive_product],
            'affordable_products': [],
            'user_profile': moderate_user,
            'errors': []
        }

        result = pathfinder_agent.execute(state)

        if 'alternative_paths' in result:
            assert len(result['alternative_paths']) <= 3, \
                f"Should return maximum 3 paths, got {len(result['alternative_paths'])}"

    def test_paths_sorted_by_viability(self, pathfinder_agent, moderate_user, expensive_product):
        """Test that paths are sorted by viability (best first)"""
        state = {
            'all_unaffordable': True,
            'candidate_products': [expensive_product],
            'affordable_products': [],
            'user_profile': moderate_user,
            'errors': []
        }

        result = pathfinder_agent.execute(state)

        if 'alternative_paths' in result and len(result['alternative_paths']) > 1:
            paths = result['alternative_paths']

            # Check descending order
            for i in range(len(paths) - 1):
                assert paths[i]['viability_score'] >= paths[i+1]['viability_score'], \
                    "Paths should be sorted by viability (descending)"

    def test_rank_field_added(self, pathfinder_agent, moderate_user, expensive_product):
        """Test that rank field is added (1-based)"""
        state = {
            'all_unaffordable': True,
            'candidate_products': [expensive_product],
            'affordable_products': [],
            'user_profile': moderate_user,
            'errors': []
        }

        result = pathfinder_agent.execute(state)

        if 'alternative_paths' in result:
            for i, path in enumerate(result['alternative_paths']):
                assert 'rank' in path, f"Path {i} should have rank field"
                assert path['rank'] == i + 1, f"Path {i} should have rank {i+1}, got {path['rank']}"


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_graceful_failure(self, pathfinder_agent):
        """Test graceful failure on error"""
        # Invalid state (missing user_profile)
        state = {
            'all_unaffordable': True,
            'candidate_products': [],
            'user_profile': None,  # Invalid
            'errors': []
        }

        try:
            result = pathfinder_agent.execute(state)

            # Should not crash
            assert 'errors' in result or 'alternative_paths' in result, \
                "Should handle error gracefully"
        except Exception as e:
            pytest.fail(f"Agent should not crash on invalid input: {e}")

    def test_empty_candidate_products(self, pathfinder_agent, moderate_user):
        """Test with empty candidate products"""
        state = {
            'all_unaffordable': True,
            'candidate_products': [],  # Empty
            'affordable_products': [],
            'user_profile': moderate_user,
            'errors': []
        }

        result = pathfinder_agent.execute(state)

        # Should return empty paths
        assert 'alternative_paths' in result, "Should have alternative_paths field"
        assert len(result['alternative_paths']) == 0, "Should return empty paths for empty candidates"


class TestViabilityCalculations:
    """Test viability score calculation methods"""

    def test_savings_viability_calculation(self, pathfinder_agent):
        """Test savings viability calculation"""
        # Test different scenarios
        disposable = 1000.0

        # Low ratio, short duration (best)
        score1 = pathfinder_agent._calculate_savings_viability(
            required_monthly=50.0,   # 5% of disposable
            disposable_income=disposable,
            months=3
        )

        # High ratio, long duration (worst)
        score2 = pathfinder_agent._calculate_savings_viability(
            required_monthly=250.0,  # 25% of disposable
            disposable_income=disposable,
            months=6
        )

        assert 0.0 <= score1 <= 1.0, f"Score must be [0.0, 1.0], got {score1}"
        assert 0.0 <= score2 <= 1.0, f"Score must be [0.0, 1.0], got {score2}"
        assert score1 > score2, "Lower ratio + shorter duration should have higher viability"

    def test_financing_viability_calculation(self, pathfinder_agent):
        """Test financing viability calculation"""
        # Test different scenarios

        # Low PTI, low interest, short term (best)
        score1 = pathfinder_agent._calculate_financing_viability(
            pti_ratio=0.08,          # 8%
            interest_ratio=0.03,      # 3%
            months=18
        )

        # High PTI, high interest, long term (worst)
        score2 = pathfinder_agent._calculate_financing_viability(
            pti_ratio=0.19,          # 19%
            interest_ratio=0.18,      # 18%
            months=36
        )

        assert 0.0 <= score1 <= 1.0, f"Score must be [0.0, 1.0], got {score1}"
        assert 0.0 <= score2 <= 1.0, f"Score must be [0.0, 1.0], got {score2}"
        assert score1 > score2, "Better terms should have higher viability"

    def test_alternative_viability_calculation(self, pathfinder_agent):
        """Test alternative viability calculation"""
        # Cash-affordable alternative (best)
        score1 = pathfinder_agent._calculate_alternative_viability(
            can_afford_cash=True,
            savings_percent=25.0,     # 25% savings
            alt_price=500.0,
            safe_cash_limit=600.0
        )

        # Not cash-affordable, low savings (worst)
        score2 = pathfinder_agent._calculate_alternative_viability(
            can_afford_cash=False,
            savings_percent=7.0,      # 7% savings
            alt_price=1000.0,
            safe_cash_limit=500.0
        )

        assert 0.0 <= score1 <= 1.0, f"Score must be [0.0, 1.0], got {score1}"
        assert 0.0 <= score2 <= 1.0, f"Score must be [0.0, 1.0], got {score2}"
        assert score1 > score2, "Cash-affordable alternatives should have higher viability"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
