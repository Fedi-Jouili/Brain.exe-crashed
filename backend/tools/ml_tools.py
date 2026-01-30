"""
ML/RL Tools - Machine Learning and Reinforcement Learning Operations

This module provides 5 tools for ML/RL operations:

1. calculate_affordability - Financial affordability analysis
2. thompson_sample_ranking - Thompson Sampling product ranking
3. update_thompson_sampling - Update RL parameters based on user actions
4. generate_creative_financing_paths - Creative financing options generation
5. estimate_query_complexity - Query complexity estimation for routing

Architecture:
- Tools wrap ML/RL services with standardized interfaces
- Lazy imports avoid circular dependencies
- Type-safe input/output via Pydantic
- Consistent error handling

Usage Example:
    from tools.ml_tools import calculate_affordability, thompson_sample_ranking

    # Affordability analysis
    result = calculate_affordability.invoke({
        "product": {"price": 1000, "name": "Laptop"},
        "user": {"monthly_income": 5000, "monthly_expenses": 3000},
        "financial_rules": [...]
    })

    # Thompson Sampling ranking
    result = thompson_sample_ranking.invoke({
        "product_ids": ["PROD001", "PROD002", "PROD003"]
    })
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from .base import BaseTool, ToolInput, ToolOutput
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 5: Calculate Affordability
# ============================================================================

class AffordabilityInput(ToolInput):
    """
    Input schema for affordability calculation.

    Attributes:
        product: Product data with price, name, etc.
        user: User financial profile (income, expenses, debt, etc.)
        financial_rules: Retrieved financial rules from RAG
    """
    product: Dict[str, Any] = Field(
        ...,
        description="Product data (must include 'price' key)"
    )
    user: Dict[str, Any] = Field(
        ...,
        description="User financial profile (monthly_income, monthly_expenses, etc.)"
    )
    financial_rules: List[Dict[str, Any]] = Field(
        default=[],
        description="Retrieved financial rules for affordability analysis"
    )

    @validator('product')
    def validate_product_has_price(cls, v):
        """Ensure product has price"""
        if 'price' not in v:
            raise ValueError("product must have 'price' key")
        return v

    @validator('user')
    def validate_user_has_income(cls, v):
        """Ensure user has income"""
        if 'monthly_income' not in v:
            raise ValueError("user must have 'monthly_income' key")
        return v


class CalculateAffordabilityTool(BaseTool):
    """
    Comprehensive affordability analysis using financial rules.

    This tool calculates whether a user can afford a product via:
    - Cash purchase (30% rule)
    - Financing (DTI and PTI checks)
    - Risk assessment
    - Emergency fund impact

    Used by:
        - Agent 2 (Financial Analyzer) - Primary affordability assessment
        - Agent 4 (Explainer) - Financial reasoning explanations

    Financial Rules Applied:
        - 30% Rule: One-time purchase ≤ 30% of disposable income
        - DTI Threshold: Total debt payments ≤ 36% of gross income (safe)
        - PTI Threshold: Product payment ≤ 28% of gross income
        - Emergency Fund: Maintain 3-month buffer
        - Credit Score: Minimum 650 for financing

    Algorithm:
        1. Calculate disposable income (income - expenses)
        2. Check cash affordability (price ≤ 30% disposable)
        3. If not cash affordable, check financing:
           a. Calculate DTI ratio (current + new debt)
           b. Calculate PTI ratio (product payment / income)
           c. Check emergency fund impact
           d. Check credit score requirement
        4. Determine risk level (safe/caution/risky)
        5. Return comprehensive analysis

    Example:
        tool = CalculateAffordabilityTool()
        result = tool.invoke({
            "product": {
                "product_id": "LAPTOP-001",
                "name": "Dell XPS 15",
                "price": 1500.0
            },
            "user": {
                "monthly_income": 5000.0,
                "monthly_expenses": 3000.0,
                "current_debt": 10000.0,
                "credit_score": 720,
                "savings": 8000.0
            },
            "financial_rules": [...]
        })

        if result["success"]:
            analysis = result["data"]
            print(f"Can afford cash: {analysis['can_afford_cash']}")
            print(f"Can afford financing: {analysis['can_afford_financing']}")
            print(f"Risk level: {analysis['risk_level']}")
    """

    name = "calculate_affordability"
    description = "Calculate financial affordability with DTI, PTI, and emergency fund checks"
    input_schema = AffordabilityInput

    def _execute(self, input_data: AffordabilityInput) -> ToolOutput:
        """
        Execute affordability calculation.

        Args:
            input_data: Validated calculation parameters

        Returns:
            ToolOutput with:
                - can_afford_cash: bool
                - can_afford_financing: bool
                - risk_level: "safe" | "caution" | "risky"
                - cash_analysis: dict with cash purchase details
                - financing_analysis: dict with financing details
                - recommendations: list of strings
        """
        try:
            # Lazy import
            from utils.financial import FinancialCalculator

            product = input_data.product
            user = input_data.user
            price = float(product.get("price", 0))
            product_name = product.get("name", "Product")

            logger.info(
                f"Calculating affordability: {product_name} (${price:.2f}) "
                f"for user with income ${user.get('monthly_income', 0):.2f}"
            )

            # Initialize calculator
            calc = FinancialCalculator()

            # Calculate disposable income
            disposable_income = calc.calculate_disposable_income(user)
            safe_cash_limit = calc.calculate_safe_cash_limit(user)

            # Cash affordability (30% rule)
            can_afford_cash = price <= safe_cash_limit

            cash_analysis = {
                "disposable_income": disposable_income,
                "safe_cash_limit": safe_cash_limit,
                "price": price,
                "can_afford": can_afford_cash,
                "percentage_of_disposable": (price / disposable_income * 100) if disposable_income > 0 else float('inf')
            }

            # Financing affordability
            financing_analysis = {}
            can_afford_financing = False

            if not can_afford_cash:
                # Estimate monthly payment (60-month loan at 5% APR)
                monthly_payment = calc._estimate_monthly_payment(price, apr=5.0, months=60)

                # Calculate DTI with new debt
                current_dti = calc.calculate_dti_ratio(user, additional_debt=0)
                new_dti = calc.calculate_dti_ratio(user, additional_debt=monthly_payment)

                # Calculate PTI (Product-to-Income)
                monthly_income = float(user.get('monthly_income', 0))
                pti_ratio = (monthly_payment / monthly_income) if monthly_income > 0 else float('inf')

                # Check credit score
                credit_score = int(user.get('credit_score', 0))
                credit_ok = credit_score >= 650

                # Check emergency fund
                savings = float(user.get('savings', 0))
                emergency_fund_needed = monthly_income * 3  # 3 months
                emergency_fund_ok = savings >= emergency_fund_needed

                # Determine if financing is affordable
                # Safe thresholds: DTI <= 36%, PTI <= 28%
                can_afford_financing = (
                    new_dti <= 0.36 and
                    pti_ratio <= 0.28 and
                    credit_ok and
                    emergency_fund_ok
                )

                financing_analysis = {
                    "monthly_payment": monthly_payment,
                    "current_dti": current_dti,
                    "new_dti": new_dti,
                    "pti_ratio": pti_ratio,
                    "credit_score": credit_score,
                    "credit_ok": credit_ok,
                    "savings": savings,
                    "emergency_fund_needed": emergency_fund_needed,
                    "emergency_fund_ok": emergency_fund_ok,
                    "can_afford": can_afford_financing
                }

            # Determine risk level
            if can_afford_cash:
                risk_level = "safe"
            elif can_afford_financing:
                risk_level = "caution"
            else:
                risk_level = "risky"

            # Generate recommendations
            recommendations = []
            if can_afford_cash:
                recommendations.append("Can afford cash purchase within 30% rule")
            elif can_afford_financing:
                recommendations.append("Cash purchase not recommended, but financing is viable")
                recommendations.append(f"Monthly payment: ${financing_analysis['monthly_payment']:.2f}")
            else:
                recommendations.append("Product exceeds financial capacity")
                if not financing_analysis.get('credit_ok', True):
                    recommendations.append("Credit score below 650 - work on credit first")
                if not financing_analysis.get('emergency_fund_ok', True):
                    recommendations.append("Insufficient emergency fund - save more first")
                if financing_analysis.get('new_dti', 0) > 0.36:
                    recommendations.append(f"DTI would exceed safe limit: {financing_analysis['new_dti']*100:.1f}%")

            logger.info(
                f"Affordability result: cash={can_afford_cash}, "
                f"financing={can_afford_financing}, risk={risk_level}"
            )

            return ToolOutput(
                success=True,
                data={
                    "can_afford_cash": can_afford_cash,
                    "can_afford_financing": can_afford_financing,
                    "risk_level": risk_level,
                    "cash_analysis": cash_analysis,
                    "financing_analysis": financing_analysis,
                    "recommendations": recommendations
                }
            )

        except Exception as e:
            logger.error(f"Affordability calculation failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Affordability calculation failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 6: Thompson Sample Ranking
# ============================================================================

class ThompsonRankingInput(ToolInput):
    """
    Input schema for Thompson Sampling ranking.

    Attributes:
        product_ids: List of product IDs to rank
    """
    product_ids: List[str] = Field(
        ...,
        description="List of product IDs to rank using Thompson Sampling",
        min_items=1
    )


class ThompsonSampleRankingTool(BaseTool):
    """
    Rank products using Thompson Sampling (Multi-Armed Bandit).

    This tool uses the Thompson Sampling algorithm to rank products based on
    learned user preferences. Each product has Beta distribution parameters
    (α, β) that are updated based on user interactions.

    Used by:
        - Agent 3 (Smart Recommender) - RL-based product ranking

    Algorithm:
        1. For each product_id, retrieve parameters (α, β)
        2. Sample score from Beta(α, β) distribution
        3. Sort products by sampled score (descending)
        4. Return ranked list with scores

    Thompson Sampling Properties:
        - Exploration vs Exploitation balance
        - Stochastic ranking (different each time)
        - Converges to optimal ranking over time
        - Handles cold-start with uniform prior (α=1, β=1)

    Example:
        tool = ThompsonSampleRankingTool()
        result = tool.invoke({
            "product_ids": ["LAPTOP-001", "PHONE-002", "TABLET-003"]
        })

        if result["success"]:
            scores = result["data"]["scores"]
            ranked_ids = result["data"]["ranked_ids"]

            for product_id in ranked_ids:
                print(f"{product_id}: {scores[product_id]:.3f}")
    """

    name = "thompson_sample_ranking"
    description = "Rank products using Thompson Sampling reinforcement learning"
    input_schema = ThompsonRankingInput

    def _execute(self, input_data: ThompsonRankingInput) -> ToolOutput:
        """
        Execute Thompson Sampling ranking.

        Args:
            input_data: Validated ranking parameters

        Returns:
            ToolOutput with:
                - ranked_ids: List of product_ids sorted by score
                - scores: Dict mapping product_id to sampled score
                - parameters: Dict mapping product_id to (α, β) params
        """
        try:
            # Lazy import
            from ml.thompson_sampling import ThompsonSamplingEngine

            product_ids = input_data.product_ids
            logger.info(f"Ranking {len(product_ids)} products using Thompson Sampling")

            # Initialize engine
            engine = ThompsonSamplingEngine()

            # Rank products (returns list of (product_id, score) tuples)
            ranked_tuples = engine.rank_product_ids(product_ids)

            # Extract ranked IDs and scores
            ranked_ids = [pid for pid, score in ranked_tuples]
            scores = {pid: float(score) for pid, score in ranked_tuples}

            # Get parameters for each product
            parameters = {}
            for product_id in product_ids:
                params = engine.get_params(product_id)
                parameters[product_id] = {
                    "alpha": float(params["alpha"]),
                    "beta": float(params["beta"]),
                    "total_interactions": int(params["total_interactions"]),
                    "confidence": params["confidence"]
                }

            logger.info(
                f"Thompson Sampling ranking complete. Top 3: {ranked_ids[:3]}"
            )

            return ToolOutput(
                success=True,
                data={
                    "ranked_ids": ranked_ids,
                    "scores": scores,
                    "parameters": parameters
                }
            )

        except Exception as e:
            logger.error(f"Thompson Sampling ranking failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Thompson Sampling ranking failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 7: Update Thompson Sampling Parameters
# ============================================================================

class ThompsonUpdateInput(ToolInput):
    """
    Input schema for Thompson Sampling parameter update.

    Attributes:
        product_id: Product ID to update
        action: User action (view, click, add_to_cart, purchase, skip, etc.)
    """
    product_id: str = Field(
        ...,
        description="Product ID to update parameters for"
    )
    action: str = Field(
        ...,
        description="User action: view, click, add_to_cart, purchase, skip, remove_from_cart, return"
    )

    @validator('action')
    def validate_action(cls, v):
        """Ensure action is valid"""
        valid_actions = ["view", "click", "add_to_cart", "purchase", "skip", "remove_from_cart", "return"]
        if v not in valid_actions:
            raise ValueError(f"action must be one of {valid_actions}, got '{v}'")
        return v


class UpdateThompsonSamplingTool(BaseTool):
    """
    Update Thompson Sampling parameters based on user actions.

    This tool updates the Beta distribution parameters (α, β) for a product
    based on user interactions. Positive actions increase α, negative actions
    increase β.

    Used by:
        - Main API (/api/feedback/action endpoint) - After user interactions

    Signal Weights (from config):
        Positive signals (increase α):
        - view: +0.1
        - click: +0.3
        - add_to_cart: +0.7
        - purchase: +1.0

        Negative signals (increase β):
        - skip: +0.3
        - remove_from_cart: +0.5
        - return: +1.0

    Algorithm:
        1. Get current parameters (α, β) for product
        2. Get signal weight for action
        3. If positive signal: α += weight
        4. If negative signal: β += |weight|
        5. Increment total_interactions
        6. Store updated parameters

    Example:
        tool = UpdateThompsonSamplingTool()

        # User clicked on product
        result = tool.invoke({
            "product_id": "LAPTOP-001",
            "action": "click"
        })

        if result["success"]:
            params = result["data"]
            print(f"Updated: α={params['new_alpha']}, β={params['new_beta']}")
    """

    name = "update_thompson_sampling"
    description = "Update Thompson Sampling parameters based on user actions"
    input_schema = ThompsonUpdateInput

    def _execute(self, input_data: ThompsonUpdateInput) -> ToolOutput:
        """
        Execute Thompson Sampling parameter update.

        Args:
            input_data: Validated update parameters

        Returns:
            ToolOutput with:
                - old_alpha: Previous α value
                - old_beta: Previous β value
                - new_alpha: Updated α value
                - new_beta: Updated β value
                - signal_weight: Weight applied for action
                - total_interactions: Total interactions count
        """
        try:
            # Lazy imports
            from ml.thompson_sampling import ThompsonSamplingEngine
            from core.config import settings

            product_id = input_data.product_id
            action = input_data.action

            logger.info(f"Updating Thompson parameters: {product_id}, action={action}")

            # Initialize engine
            engine = ThompsonSamplingEngine()

            # Get current parameters
            old_params = engine.get_params(product_id)
            old_alpha = old_params["alpha"]
            old_beta = old_params["beta"]

            # Update parameters using engine's update method
            engine.update_params(product_id, action)

            # Get new parameters
            new_params = engine.get_params(product_id)
            new_alpha = new_params["alpha"]
            new_beta = new_params["beta"]

            # Get signal weight from config
            signal_weights = {
                "view": settings.signal_weight_view,
                "click": settings.signal_weight_click,
                "add_to_cart": settings.signal_weight_add_to_cart,
                "purchase": settings.signal_weight_purchase,
                "skip": settings.signal_weight_skip,
                "remove_from_cart": settings.signal_weight_remove_from_cart,
                "return": settings.signal_weight_return
            }
            signal_weight = signal_weights.get(action, 0.0)

            logger.info(
                f"Thompson update complete: {product_id} - "
                f"α: {old_alpha:.2f} → {new_alpha:.2f}, "
                f"β: {old_beta:.2f} → {new_beta:.2f}"
            )

            return ToolOutput(
                success=True,
                data={
                    "product_id": product_id,
                    "action": action,
                    "old_alpha": float(old_alpha),
                    "old_beta": float(old_beta),
                    "new_alpha": float(new_alpha),
                    "new_beta": float(new_beta),
                    "signal_weight": float(signal_weight),
                    "total_interactions": int(new_params["total_interactions"])
                }
            )

        except Exception as e:
            logger.error(f"Thompson parameter update failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Thompson parameter update failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 8: Generate Creative Financing Paths
# ============================================================================

class FinancingPathsInput(ToolInput):
    """
    Input schema for financing paths generation.

    Attributes:
        product: Product data with price
        user: User financial profile
        gap_amount: Amount user cannot afford (price - affordable_amount)
    """
    product: Dict[str, Any] = Field(
        ...,
        description="Product data (must include 'price' key)"
    )
    user: Dict[str, Any] = Field(
        ...,
        description="User financial profile"
    )
    gap_amount: float = Field(
        ...,
        gt=0,
        description="Amount user cannot afford"
    )


class GenerateCreativeFinancingPathsTool(BaseTool):
    """
    Generate creative financing paths for unaffordable products.

    This tool generates alternative financing options when a product
    is not immediately affordable through cash or traditional financing.

    Used by:
        - Agent 2.5 (PathFinder) - Creative affordability solutions

    Financing Paths:
        1. Save-Then-Buy: Calculate months to save
        2. Used/Refurbished: Find lower-cost alternatives
        3. Split Payment: Divide into installments
        4. Trade-In: Factor in trade-in value
        5. Down Payment: Reduce financing amount

    Example:
        tool = GenerateCreativeFinancingPathsTool()
        result = tool.invoke({
            "product": {"price": 2000, "name": "MacBook Pro"},
            "user": {"monthly_income": 4000, "savings": 500},
            "gap_amount": 1000
        })

        if result["success"]:
            paths = result["data"]["paths"]
            for path in paths:
                print(f"{path['path_type']}: {path['description']}")
    """

    name = "generate_creative_financing_paths"
    description = "Generate creative financing options for unaffordable products"
    input_schema = FinancingPathsInput

    def _execute(self, input_data: FinancingPathsInput) -> ToolOutput:
        """
        Execute financing paths generation.

        Args:
            input_data: Validated generation parameters

        Returns:
            ToolOutput with:
                - paths: List of financing path dicts
                - recommended_path: Best path recommendation
        """
        try:
            product = input_data.product
            user = input_data.user
            gap_amount = input_data.gap_amount
            price = float(product.get("price", 0))

            logger.info(
                f"Generating financing paths: price=${price:.2f}, gap=${gap_amount:.2f}"
            )

            paths = []

            # Path 1: Save-Then-Buy
            monthly_savings_capacity = float(user.get("monthly_income", 0)) * 0.1  # 10% of income
            if monthly_savings_capacity > 0:
                months_to_save = int(gap_amount / monthly_savings_capacity) + 1
                paths.append({
                    "path_type": "save_then_buy",
                    "description": f"Save ${monthly_savings_capacity:.2f}/month for {months_to_save} months",
                    "timeline_months": months_to_save,
                    "monthly_amount": monthly_savings_capacity,
                    "total_cost": price,
                    "feasibility": "high" if months_to_save <= 12 else "medium"
                })

            # Path 2: Used/Refurbished Alternative
            used_discount = 0.3  # 30% discount for used
            used_price = price * (1 - used_discount)
            paths.append({
                "path_type": "used_alternative",
                "description": f"Consider used/refurbished at ~${used_price:.2f}",
                "timeline_months": 0,
                "monthly_amount": 0,
                "total_cost": used_price,
                "feasibility": "high"
            })

            # Path 3: Split Payment (if gap is small)
            if gap_amount < price * 0.5:
                split_months = 6
                monthly_payment = price / split_months
                paths.append({
                    "path_type": "split_payment",
                    "description": f"Pay ${monthly_payment:.2f}/month for {split_months} months",
                    "timeline_months": split_months,
                    "monthly_amount": monthly_payment,
                    "total_cost": price,
                    "feasibility": "medium"
                })

            # Path 4: Down Payment + Financing
            down_payment_pct = 0.2  # 20% down
            down_payment = price * down_payment_pct
            financed_amount = price - down_payment
            months = 12
            monthly_payment = financed_amount / months
            paths.append({
                "path_type": "down_payment_financing",
                "description": f"${down_payment:.2f} down, then ${monthly_payment:.2f}/month for {months} months",
                "timeline_months": months,
                "monthly_amount": monthly_payment,
                "total_cost": price,
                "feasibility": "medium"
            })

            # Recommend best path (shortest timeline with high feasibility)
            recommended_path = min(
                [p for p in paths if p["feasibility"] == "high"],
                key=lambda x: x["timeline_months"],
                default=paths[0] if paths else None
            )

            logger.info(f"Generated {len(paths)} financing paths")

            return ToolOutput(
                success=True,
                data={
                    "paths": paths,
                    "recommended_path": recommended_path,
                    "count": len(paths)
                }
            )

        except Exception as e:
            logger.error(f"Financing paths generation failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Financing paths generation failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL 9: Estimate Query Complexity
# ============================================================================

class ComplexityEstimationInput(ToolInput):
    """
    Input schema for query complexity estimation.

    Attributes:
        query: Search query string
        user_profile: Optional user profile dict
        has_image: Whether query includes image
    """
    query: str = Field(
        ...,
        description="Search query string",
        min_length=1
    )
    user_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user profile with financial data"
    )
    has_image: bool = Field(
        default=False,
        description="Whether query includes image upload"
    )


class EstimateQueryComplexityTool(BaseTool):
    """
    Estimate query complexity for routing decisions.

    This tool estimates the complexity of a search query to determine
    which execution path to use (FAST/SMART/DEEP).

    Used by:
        - Main API (/api/search endpoint) - Routing decisions

    Complexity Factors:
        - Query length (0.1-0.3)
        - Financial keywords (0.0-0.9)
        - Price constraints (0.0-0.2)
        - User profile completeness (0.0-0.2)
        - Multimodal input (0.0-0.1)

    Routing Rules:
        - FAST (< 0.3): Simple query, cache hit possible
        - SMART (0.3-0.7): Moderate complexity, Agent 1 only
        - DEEP (≥ 0.7): Complex query, full pipeline needed

    Example:
        tool = EstimateQueryComplexityTool()

        # Simple query
        result = tool.invoke({"query": "laptops"})
        # → FAST path (score < 0.3)

        # Complex query with financial context
        result = tool.invoke({
            "query": "laptop under $1000 with financing",
            "user_profile": {"monthly_income": 5000}
        })
        # → DEEP path (score ≥ 0.7)
    """

    name = "estimate_query_complexity"
    description = "Estimate query complexity for FAST/SMART/DEEP routing decisions"
    input_schema = ComplexityEstimationInput

    def _execute(self, input_data: ComplexityEstimationInput) -> ToolOutput:
        """
        Execute complexity estimation.

        Args:
            input_data: Validated estimation parameters

        Returns:
            ToolOutput with:
                - level: "FAST" | "SMART" | "DEEP"
                - score: float (0.0-1.0+)
                - reasoning: str explaining the decision
                - factors: dict of individual factor contributions
        """
        try:
            # Lazy import
            from ml.complexity_estimator import ComplexityEstimator

            query = input_data.query
            logger.info(f"Estimating complexity for query: '{query}'")

            # Initialize estimator
            estimator = ComplexityEstimator()

            # Estimate complexity
            result = estimator.estimate(
                query=query,
                user_profile=input_data.user_profile,
                has_image=input_data.has_image
            )

            logger.info(
                f"Complexity estimation: level={result['level']}, "
                f"score={result['score']:.2f}"
            )

            return ToolOutput(
                success=True,
                data=result
            )

        except Exception as e:
            logger.error(f"Complexity estimation failed: {e}", exc_info=True)
            return ToolOutput(
                success=False,
                error=f"Complexity estimation failed: {str(e)}",
                data=None
            )


# ============================================================================
# TOOL INSTANCES
# ============================================================================

# Create singleton instances for easy import
calculate_affordability = CalculateAffordabilityTool()
thompson_sample_ranking = ThompsonSampleRankingTool()
update_thompson_sampling = UpdateThompsonSamplingTool()
generate_creative_financing_paths = GenerateCreativeFinancingPathsTool()
estimate_query_complexity = EstimateQueryComplexityTool()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Tool classes
    "CalculateAffordabilityTool",
    "ThompsonSampleRankingTool",
    "UpdateThompsonSamplingTool",
    "GenerateCreativeFinancingPathsTool",
    "EstimateQueryComplexityTool",
    # Tool instances
    "calculate_affordability",
    "thompson_sample_ranking",
    "update_thompson_sampling",
    "generate_creative_financing_paths",
    "estimate_query_complexity",
]
