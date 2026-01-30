"""
Agent 2.5: Budget Pathfinder
🔒 CONTRACT: Generates realistic paths when all products are unaffordable

SCORE CONTRACT (LOCKED):
  • viability_score: 0.0 → 1.0 (NOT 0-100)
  • Maximum 3 paths returned
  • No product mutation
  • Graceful failure only
"""
from typing import Dict, Any, List, Optional
import logging

# Optional imports for type hints (fallback to Any if not available)
try:
    from models.state import AgentState
    from models.schemas import UserProfile, Product, FinancingPath
except ImportError:
    AgentState = Dict[str, Any]
    UserProfile = Any
    Product = Any
    FinancingPath = Any

from utils.financial import FinancialCalculator

logger = logging.getLogger(__name__)


class BudgetPathfinderAgent:
    """
    Agent 2.5: Budget Pathfinder

    🔒 ACTIVATION CONDITION:
        Only runs when state['all_unaffordable'] == True

    🔒 RESPONSIBILITIES:
        1. Extended savings plans (3-6 months)
        2. Extended financing plans (18-36 months, PTI ≤ 20%)
        3. Cheaper cluster alternatives (≥5% cheaper, same cluster_id)

    🔒 OUTPUT CONSTRAINTS:
        • viability_score ∈ [0.0, 1.0] for ALL paths
        • Maximum 3 paths (sorted by viability DESC)
        • Each path includes: type, strategy, description, pros, cons, rank
        • No Thompson logic
        • No score rescaling

    🔒 VIABILITY SCORING RULES:
        Savings: Shorter duration + lower % of disposable income = higher score
        Financing: Lower PTI + lower total interest = higher score
        Alternatives: Cash-affordable + higher savings % = higher score
    """

    def __init__(self):
        self.calculator = FinancialCalculator()
        logger.info("Budget Pathfinder Agent initialized")

    def execute(self, state: AgentState) -> AgentState:
        """
        🔒 CONTRACT-COMPLIANT PATH GENERATION

        Activation: Only when state['all_unaffordable'] == True
        Output: Maximum 3 paths, viability_score ∈ [0.0, 1.0]

        Args:
            state: Current agent state with all_unaffordable flag

        Returns:
            Updated state with alternative_paths (ranked 1-3)
        """
        start_time = self._get_timestamp()

        # 🔒 CONTRACT: Only run if all products unaffordable
        if not state.get('all_unaffordable', False):
            logger.info("Agent 2.5: Skipping (products are affordable)")
            return state

        logger.info("Agent 2.5: Starting budget pathfinding")

        try:
            candidate_products = state.get('candidate_products', [])
            user_profile = state['user_profile']

            if not candidate_products:
                logger.warning("Agent 2.5: No candidate products to work with")
                state['alternative_paths'] = []
                return state

            # Get top 3 most desired products (from Agent 1's search results)
            target_products = candidate_products[:3]

            alternative_paths = []

            # 🔒 STRATEGY 1: Extended Savings Plans (3-6 months)
            logger.info("Generating extended savings plans...")
            for product in target_products:
                savings_paths = self._generate_extended_savings_paths(
                    product=product,
                    profile=user_profile
                )
                alternative_paths.extend(savings_paths)

            # 🔒 STRATEGY 2: Extended Financing Plans (18-36 months, PTI ≤ 20%)
            logger.info("Exploring extended financing terms...")
            for product in target_products:
                if self._has_financing_available(product):
                    financing_paths = self._generate_extended_financing_paths(
                        product=product,
                        profile=user_profile
                    )
                    alternative_paths.extend(financing_paths)

            # 🔒 STRATEGY 3: Cheaper Cluster Alternatives (≥5% cheaper)
            logger.info("Finding cheaper alternatives via clustering...")
            for product in target_products:
                cluster_alternatives = self._find_cheaper_cluster_alternatives(
                    product=product,
                    profile=user_profile,
                    max_alternatives=2
                )
                alternative_paths.extend(cluster_alternatives)

            # 🔒 CONTRACT: Rank and limit to top 3 paths
            ranked_paths = self._rank_and_score_paths(alternative_paths, user_profile)
            top_paths = ranked_paths[:3]  # Maximum 3 paths

            # 🔒 CONTRACT: Add rank field (1-based)
            for i, path in enumerate(top_paths):
                path['rank'] = i + 1

            # Update state
            state['alternative_paths'] = top_paths
            state['agent2_5_execution_time'] = self._get_timestamp() - start_time

            logger.info(f"Agent 2.5: Generated {len(top_paths)} paths (viability: {[round(p['viability_score'], 2) for p in top_paths]})")
            logger.info(f"Agent 2.5 complete in {state['agent2_5_execution_time']:.0f}ms")

            return state

        except Exception as e:
            # 🔒 CONTRACT: Graceful failure (never crash pipeline)
            logger.error(f"Agent 2.5 error: {e}", exc_info=True)
            state['errors'] = state.get('errors', []) + [f"Pathfinder failed: {str(e)}"]
            state['alternative_paths'] = []
            return state

    def _generate_extended_savings_paths(
        self,
        product: Any,
        profile: UserProfile,
        months_options: List[int] = [3, 6]  # 🔒 CONTRACT: 3-6 months only
    ) -> List[Dict[str, Any]]:
        """
        🔒 CONTRACT-COMPLIANT: Generate savings plans (3-6 months)

        Rules:
        - Monthly savings ≤ 30% of disposable income
        - Shorter duration = higher viability
        - Must include pros/cons

        Args:
            product: Target product
            profile: User financial profile
            months_options: Timeframe options (3-6 months)

        Returns:
            List of savings path options with viability_score ∈ [0.0, 1.0]
        """
        paths = []
        price = product.price if hasattr(product, 'price') else product['price']
        product_name = product.name if hasattr(product, 'name') else product['name']
        product_id = product.product_id if hasattr(product, 'product_id') else product.get('product_id', 'unknown')

        disposable_income = self.calculator.calculate_disposable_income(profile)

        if disposable_income <= 0:
            return paths  # Can't save with no disposable income

        for months in months_options:
            required_monthly_savings = price / months
            savings_ratio = required_monthly_savings / disposable_income

            # 🔒 CONTRACT: Monthly savings ≤ 30% disposable income
            if savings_ratio > 0.30:
                continue  # Skip unrealistic savings plans

            # 🔒 CONTRACT: Calculate viability_score ∈ [0.0, 1.0]
            # Shorter duration + lower ratio = higher viability
            viability_score = self._calculate_savings_viability(
                required_monthly_savings,
                disposable_income,
                months
            )

            # Generate pros and cons
            pros = []
            cons = []

            if months <= 3:
                pros.append(f"Quick path to ownership (just {months} months)")
            else:
                cons.append(f"Requires {months} months of saving")

            if savings_ratio < 0.15:
                pros.append(f"Low monthly commitment (${required_monthly_savings:.2f}/month)")
            else:
                cons.append(f"Requires ${required_monthly_savings:.2f}/month ({savings_ratio*100:.0f}% of disposable income)")

            pros.append("No interest or debt")
            pros.append("Builds financial discipline")

            paths.append({
                'type': 'savings_plan',
                'strategy': f'save_{months}mo',
                'product_id': product_id,
                'product_name': product_name,
                'price': price,
                'timeline_months': months,
                'monthly_savings_required': required_monthly_savings,
                'savings_ratio': savings_ratio,
                'description': f"Save ${required_monthly_savings:.2f}/month for {months} months to purchase {product_name}",
                'viability_score': viability_score,  # 🔒 CONTRACT: 0.0-1.0
                'pros': pros,
                'cons': cons
            })

        return paths

    def _generate_extended_financing_paths(
        self,
        product: Any,
        profile: UserProfile,
        months_options: List[int] = [18, 24, 36]  # 🔒 CONTRACT: 18-36 months
    ) -> List[Dict[str, Any]]:
        """
        🔒 CONTRACT-COMPLIANT: Generate extended financing plans (18-36 months)

        Rules:
        - Only PTI ≤ 20% (0.20)
        - Penalize total interest heavily
        - Longer duration = lower viability
        - Must include pros/cons

        Args:
            product: Target product
            profile: User profile
            months_options: Extended term lengths (18-36 months)

        Returns:
            List of financing path options with viability_score ∈ [0.0, 1.0]
        """
        paths = []
        price = product.price if hasattr(product, 'price') else product['price']
        product_name = product.name if hasattr(product, 'name') else product['name']
        product_id = product.product_id if hasattr(product, 'product_id') else product.get('product_id', 'unknown')

        # Default APR for extended financing
        base_apr = 9.9

        for months in months_options:
            # Extended terms have higher APR
            apr = base_apr + (2.0 if months >= 24 else 0.0)

            # Calculate monthly payment
            monthly_payment = self.calculator.calculate_monthly_financing_payment(
                price=price,
                months=months,
                apr=apr / 100  # Convert to decimal
            )

            # Check affordability
            can_afford, metrics = self.calculator.check_financing_affordability(
                profile=profile,
                price=price,
                months=months,
                apr=apr / 100
            )

            pti_ratio = metrics.get('pti_ratio', 1.0)

            # 🔒 CONTRACT: Only PTI ≤ 20% (0.20)
            if pti_ratio > 0.20:
                continue  # Skip unaffordable financing

            total_cost = monthly_payment * months
            total_interest = total_cost - price
            interest_ratio = total_interest / price

            # 🔒 CONTRACT: Calculate viability_score ∈ [0.0, 1.0]
            # Lower PTI + lower interest + shorter duration = higher viability
            viability_score = self._calculate_financing_viability(
                pti_ratio=pti_ratio,
                interest_ratio=interest_ratio,
                months=months
            )

            # Generate pros and cons
            pros = []
            cons = []

            if monthly_payment < profile.monthly_income * 0.10:
                pros.append(f"Low monthly payment (${monthly_payment:.2f}/month)")

            if months <= 24:
                pros.append(f"Reasonable term length ({months} months)")
            else:
                cons.append(f"Long commitment ({months} months)")

            pros.append("Immediate access to product")

            cons.append(f"Total cost: ${total_cost:.2f} (${total_interest:.2f} interest)")
            cons.append("Creates monthly debt obligation")

            if apr >= 10.0:
                cons.append(f"Higher APR ({apr:.1f}%) for extended term")

            paths.append({
                'type': 'extended_financing',
                'strategy': f'finance_{months}mo',
                'product_id': product_id,
                'product_name': product_name,
                'price': price,
                'timeline_months': months,
                'monthly_payment': monthly_payment,
                'apr': apr,
                'total_cost': total_cost,
                'total_interest': total_interest,
                'pti_ratio': pti_ratio,
                'description': f"Finance {product_name} over {months} months at {apr:.1f}% APR (${monthly_payment:.2f}/month, total ${total_cost:.2f})",
                'viability_score': viability_score,  # 🔒 CONTRACT: 0.0-1.0
                'pros': pros,
                'cons': cons
            })

        return paths

    def _find_cheaper_cluster_alternatives(
        self,
        product: Any,
        profile: UserProfile,
        max_alternatives: int = 2
    ) -> List[Dict[str, Any]]:
        """
        🔒 CONTRACT-COMPLIANT: Find cheaper alternatives (≥5% cheaper, same cluster)

        🔒 CLUSTERING INTEGRATION:
        Uses similarity_service.get_cheaper_alternatives() for cluster-based search.
        NO runtime embeddings, NO Qdrant dependency.

        Rules:
        - Same cluster_id
        - ≥5% cheaper than original
        - Prefer cash-affordable options
        - Must include pros/cons

        Args:
            product: Target product
            profile: User profile
            max_alternatives: Max number of alternatives (default 2)

        Returns:
            List of cheaper alternative paths with viability_score ∈ [0.0, 1.0]
        """
        paths = []

        # Get product details
        if hasattr(product, 'cluster_id'):
            cluster_id = product.cluster_id
            target_price = product.price
            product_name = product.name
            product_id = product.product_id
        else:
            cluster_id = product.get('cluster_id')
            target_price = product.get('price')
            product_name = product.get('name')
            product_id = product.get('product_id', 'unknown')

        if cluster_id is None:
            logger.warning(f"Product {product_id} has no cluster_id, skipping cluster alternatives")
            return paths

        try:
            # 🔒 CLUSTERING INTEGRATION: Use similarity service
            from services.similarity_service import get_cheaper_alternatives

            # 🔒 CONTRACT: ≥5% cheaper (max price = 95% of target)
            max_price = target_price * 0.95

            # Get cheaper alternatives from same cluster
            alternatives = get_cheaper_alternatives(
                product_id=product_id,
                max_price=max_price,
                limit=max_alternatives,
                in_stock_only=True
            )

            logger.info(f"Found {len(alternatives)} cheaper alternatives for {product_id} in cluster {cluster_id}")

            for alt in alternatives:
                if len(paths) >= max_alternatives:
                    break  # Limit reached

                alt_price = alt['price']
                alt_name = alt['name']
                alt_id = alt['product_id']

                # Verify ≥5% savings
                savings_amount = target_price - alt_price
                savings_percent = (savings_amount / target_price) * 100

                if savings_percent < 5.0:
                    logger.debug(f"Alternative {alt_id} only {savings_percent:.1f}% cheaper, skipping")
                    continue  # Not enough savings

                # Check if cash affordable
                can_afford_cash, cash_metrics = self.calculator.check_cash_affordability(
                    profile=profile,
                    price=alt_price
                )

                # 🔒 CONTRACT: Calculate viability_score ∈ [0.0, 1.0]
                # Cash-affordable + higher savings % = higher viability
                viability_score = self._calculate_alternative_viability(
                    can_afford_cash=can_afford_cash,
                    savings_percent=savings_percent,
                    alt_price=alt_price,
                    safe_cash_limit=cash_metrics.get('safe_cash_limit', 0)
                )

                # Generate pros and cons
                pros = []
                cons = []

                pros.append(f"${savings_amount:.2f} cheaper ({savings_percent:.0f}% savings)")
                pros.append(f"Similar to {product_name} (same cluster)")

                if can_afford_cash:
                    pros.append("✓ Affordable with cash")
                    pros.append("No debt required")
                else:
                    cons.append("Still not cash-affordable")
                    cons.append("May need financing or saving")

                if alt.get('rating', 0) >= 4.0:
                    pros.append(f"Good ratings ({alt['rating']:.1f}/5)")

                paths.append({
                    'type': 'cluster_alternative',
                    'strategy': f'alternative_cluster_{cluster_id}',
                    'product_id': alt_id,
                    'product_name': alt_name,
                    'price': alt_price,
                    'original_product_id': product_id,
                    'original_product_name': product_name,
                    'original_price': target_price,
                    'savings_amount': savings_amount,
                    'savings_percent': savings_percent,
                    'cluster_id': cluster_id,
                    'can_afford_cash': can_afford_cash,
                    'description': f"Similar to {product_name} but ${savings_amount:.2f} cheaper ({savings_percent:.0f}% savings): {alt_name}",
                    'viability_score': viability_score,  # 🔒 CONTRACT: 0.0-1.0
                    'pros': pros,
                    'cons': cons
                })

            logger.info(f"Generated {len(paths)} cluster alternative paths")

        except FileNotFoundError as e:
            logger.error(f"Clustering artifacts not found: {e}")
            logger.info("Run clustering script: python backend/scripts/cluster_products.py")
        except Exception as e:
            logger.error(f"Error finding cluster alternatives: {e}", exc_info=True)

        return paths

    def _rank_and_score_paths(
        self,
        paths: List[Dict[str, Any]],
        profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """
        🔒 CONTRACT-COMPLIANT: Sort paths by viability_score DESC

        All paths already have viability_score ∈ [0.0, 1.0]
        Simply sort by this score (highest first)

        Args:
            paths: All generated paths
            profile: User profile (unused, for compatibility)

        Returns:
            Sorted list of paths (best first)
        """
        # 🔒 CONTRACT: Sort strictly by viability_score DESC
        return sorted(paths, key=lambda p: p.get('viability_score', 0.0), reverse=True)

    def _calculate_savings_viability(
        self,
        required_monthly: float,
        disposable_income: float,
        months: int
    ) -> float:
        """
        🔒 CONTRACT: Calculate viability for savings plans ∈ [0.0, 1.0]

        Rules:
        - Shorter duration = higher viability
        - Lower % of disposable income = higher viability

        Args:
            required_monthly: Required monthly savings
            disposable_income: User's disposable income
            months: Timeline in months

        Returns:
            Viability score ∈ [0.0, 1.0]
        """
        if disposable_income <= 0:
            return 0.0

        savings_ratio = required_monthly / disposable_income

        # Base score from savings ratio (0-30% range)
        if savings_ratio < 0.10:
            ratio_score = 0.5  # 10% or less = 0.5
        elif savings_ratio < 0.20:
            ratio_score = 0.4  # 10-20% = 0.4
        elif savings_ratio < 0.30:
            ratio_score = 0.3  # 20-30% = 0.3
        else:
            ratio_score = 0.1  # >30% = 0.1 (barely viable)

        # Duration bonus (3 months = +0.5, 6 months = +0.3)
        if months == 3:
            duration_score = 0.5
        elif months == 6:
            duration_score = 0.3
        else:
            duration_score = 0.1

        # 🔒 CONTRACT: Must return 0.0-1.0
        return min(ratio_score + duration_score, 1.0)

    def _calculate_financing_viability(
        self,
        pti_ratio: float,
        interest_ratio: float,
        months: int
    ) -> float:
        """
        🔒 CONTRACT: Calculate viability for financing ∈ [0.0, 1.0]

        Rules:
        - Lower PTI = higher viability
        - Lower total interest = higher viability
        - Shorter duration = higher viability (penalize 36mo)

        Args:
            pti_ratio: Payment-to-Income ratio (e.g., 0.15 = 15%)
            interest_ratio: Total interest / price (e.g., 0.10 = 10%)
            months: Financing duration

        Returns:
            Viability score ∈ [0.0, 1.0]
        """
        # PTI scoring (lower is better)
        if pti_ratio <= 0.10:
            pti_score = 0.4  # Excellent PTI
        elif pti_ratio <= 0.15:
            pti_score = 0.3  # Good PTI
        elif pti_ratio <= 0.20:
            pti_score = 0.2  # Acceptable PTI (max allowed)
        else:
            pti_score = 0.0  # Should not happen (filtered earlier)

        # Interest penalty (lower is better)
        if interest_ratio <= 0.05:
            interest_score = 0.3  # Low interest
        elif interest_ratio <= 0.10:
            interest_score = 0.2  # Moderate interest
        elif interest_ratio <= 0.20:
            interest_score = 0.1  # High interest
        else:
            interest_score = 0.0  # Very high interest

        # Duration penalty (shorter is better)
        if months <= 18:
            duration_score = 0.3
        elif months <= 24:
            duration_score = 0.2
        elif months <= 36:
            duration_score = 0.1
        else:
            duration_score = 0.0

        # 🔒 CONTRACT: Must return 0.0-1.0
        return min(pti_score + interest_score + duration_score, 1.0)

    def _calculate_alternative_viability(
        self,
        can_afford_cash: bool,
        savings_percent: float,
        alt_price: float,
        safe_cash_limit: float
    ) -> float:
        """
        🔒 CONTRACT: Calculate viability for alternatives ∈ [0.0, 1.0]

        Rules:
        - Cash-affordable = huge boost
        - Higher savings % = higher viability
        - Closer to safe_cash_limit = higher viability

        Args:
            can_afford_cash: Whether alternative is cash-affordable
            savings_percent: % savings vs original (e.g., 20.0 = 20%)
            alt_price: Alternative product price
            safe_cash_limit: User's safe cash purchase limit

        Returns:
            Viability score ∈ [0.0, 1.0]
        """
        # Base score from savings percentage
        if savings_percent >= 30:
            savings_score = 0.3  # 30%+ savings
        elif savings_percent >= 20:
            savings_score = 0.25  # 20-30% savings
        elif savings_percent >= 10:
            savings_score = 0.2  # 10-20% savings
        else:
            savings_score = 0.1  # 5-10% savings (minimum per contract)

        # Cash affordability bonus
        if can_afford_cash:
            affordability_score = 0.6  # Huge boost for affordability
        elif safe_cash_limit > 0 and alt_price <= safe_cash_limit * 1.5:
            affordability_score = 0.3  # Close to affordable
        else:
            affordability_score = 0.1  # Still far from affordable

        # 🔒 CONTRACT: Must return 0.0-1.0
        return min(savings_score + affordability_score, 1.0)

    def _has_financing_available(self, product: Any) -> bool:
        """Check if product has financing option"""
        if hasattr(product, 'financing_available'):
            return product.financing_available
        else:
            return product.get('financing_available', False)

    def _get_timestamp(self) -> float:
        """Get current timestamp in milliseconds"""
        import time
        return time.time() * 1000


# Global agent instance
budget_pathfinder_agent = BudgetPathfinderAgent()
