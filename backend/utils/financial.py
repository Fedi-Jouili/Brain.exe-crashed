"""
Financial calculations and affordability analysis
"""
from typing import Dict, Tuple, List, Any
import logging

# Optional imports
try:
    from models.schemas import UserProfile, RiskLevel, FinancingPath
except ImportError:
    UserProfile = Any
    RiskLevel = Any
    FinancingPath = Any

try:
    from core.config import settings
except ImportError:
    # Fallback settings
    class Settings:
        disposable_income_ratio = 0.3
        dti_threshold_safe = 0.36
        dti_threshold_caution = 0.43
        dti_threshold = 0.43
        pti_threshold = 0.28
        emergency_fund_months = 3
        emergency_fund_months_min = 3
        credit_score_threshold = 650
    settings = Settings()

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """Performs financial calculations and affordability checks"""

    @staticmethod
    def _get_attr(obj: Any, attr: str, default: Any = 0):
        """Helper to get attribute from dict or object"""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    @staticmethod
    def _create_financing_path(**kwargs) -> Any:
        """Create FinancingPath object or dict based on availability"""
        if FinancingPath is Any:
            return kwargs
        return FinancingPath(**kwargs)

    @staticmethod
    def _create_risk_level(level: str) -> Any:
        """Create RiskLevel enum or string based on availability"""
        if RiskLevel is Any:
            return level
        return getattr(RiskLevel, level)

    # ========================================================================
    # BASIC CALCULATIONS
    # ========================================================================

    @staticmethod
    def calculate_disposable_income(profile: UserProfile) -> float:
        """
        Calculate disposable income

        Returns:
            Monthly disposable income (income - expenses)
        """
        income = FinancialCalculator._get_attr(profile, 'monthly_income', 0)
        expenses = FinancialCalculator._get_attr(profile, 'monthly_expenses', 0)
        return max(0, income - expenses)

    @staticmethod
    def calculate_safe_cash_limit(profile: UserProfile) -> float:
        """
        Calculate safe cash purchase limit (30% of disposable income)

        Returns:
            Maximum safe one-time purchase amount
        """
        disposable = FinancialCalculator.calculate_disposable_income(profile)
        return disposable * settings.disposable_income_ratio

    @staticmethod
    def calculate_dti_ratio(profile: UserProfile, additional_debt: float = 0) -> float:
        """
        Calculate Debt-to-Income ratio

        Args:
            profile: User financial profile
            additional_debt: Additional monthly debt payment to add

        Returns:
            DTI ratio (0 to 1+)
        """
        current_debt = FinancialCalculator._get_attr(profile, 'current_debt', 0)
        monthly_income = FinancialCalculator._get_attr(profile, 'monthly_income', 0)

        # Estimate monthly debt payment (assuming 5% APR, 60-month term)
        if current_debt > 0:
            monthly_debt_payment = current_debt * 0.0188  # Approximate monthly payment
        else:
            monthly_debt_payment = 0

        total_monthly_debt = monthly_debt_payment + additional_debt
        dti_ratio = total_monthly_debt / monthly_income if monthly_income > 0 else 0

        return dti_ratio

    @staticmethod
    def calculate_emergency_fund_coverage(profile: UserProfile, purchase_amount: float = 0) -> float:
        """
        Calculate emergency fund coverage in months

        Args:
            profile: User financial profile
            purchase_amount: Amount to deduct from savings

        Returns:
            Number of months of expenses covered by emergency fund
        """
        savings = FinancialCalculator._get_attr(profile, 'savings', 0)
        monthly_expenses = FinancialCalculator._get_attr(profile, 'monthly_expenses', 0)

        remaining_savings = max(0, savings - purchase_amount)

        if monthly_expenses > 0:
            months_covered = remaining_savings / monthly_expenses
        else:
            months_covered = float('inf')

        return months_covered

    @staticmethod
    def calculate_monthly_financing_payment(
        price: float,
        months: int,
        apr: float = 0.0
    ) -> float:
        """
        Calculate monthly payment for financing

        Args:
            price: Total price
            months: Number of months
            apr: Annual Percentage Rate (default 0% for promotional financing)

        Returns:
            Monthly payment amount
        """
        if apr == 0:
            return price / months
        else:
            # Standard loan payment formula
            monthly_rate = apr / 12
            payment = price * (monthly_rate * (1 + monthly_rate) ** months) / \
                     ((1 + monthly_rate) ** months - 1)
            return payment

    @staticmethod
    def calculate_pti_ratio(monthly_payment: float, monthly_income: float) -> float:
        """
        Calculate Payment-to-Income ratio

        Args:
            monthly_payment: Monthly payment amount
            monthly_income: Monthly income

        Returns:
            PTI ratio (0 to 1)
        """
        return monthly_payment / monthly_income if monthly_income > 0 else 0

    # ========================================================================
    # AFFORDABILITY CHECKS
    # ========================================================================

    @staticmethod
    def check_cash_affordability(profile: UserProfile, price: float) -> Tuple[bool, Dict[str, float]]:
        """
        Check if user can afford cash purchase

        Returns:
            (can_afford, metrics_dict)
        """
        savings = FinancialCalculator._get_attr(profile, 'savings', 0)
        safe_limit = FinancialCalculator.calculate_safe_cash_limit(profile)
        emergency_fund_after = savings - price
        emergency_months = FinancialCalculator.calculate_emergency_fund_coverage(profile, price)

        can_afford = (
            price <= safe_limit and
            emergency_fund_after >= 0 and
            emergency_months >= settings.emergency_fund_months_min
        )

        metrics = {
            'safe_cash_limit': safe_limit,
            'emergency_fund_after': emergency_fund_after,
            'emergency_fund_months': emergency_months,
            'exceeds_safe_limit': price > safe_limit,
            'depletes_emergency_fund': emergency_months < settings.emergency_fund_months_min
        }

        return can_afford, metrics

    @staticmethod
    def check_financing_affordability(
        profile: UserProfile,
        price: float,
        months: int = 12,
        apr: float = 0.0
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Check if user can afford financing

        Returns:
            (can_afford, metrics_dict)
        """
        monthly_income = FinancialCalculator._get_attr(profile, 'monthly_income', 0)
        credit_score = FinancialCalculator._get_attr(profile, 'credit_score', 0)

        monthly_payment = FinancialCalculator.calculate_monthly_financing_payment(price, months, apr)
        pti_ratio = FinancialCalculator.calculate_pti_ratio(monthly_payment, monthly_income)
        dti_ratio = FinancialCalculator.calculate_dti_ratio(profile, monthly_payment)

        can_afford = (
            pti_ratio <= settings.pti_threshold and
            dti_ratio <= settings.dti_threshold and
            credit_score >= settings.credit_score_threshold
        )

        metrics = {
            'monthly_payment': monthly_payment,
            'pti_ratio': pti_ratio,
            'dti_ratio': dti_ratio,
            'exceeds_pti_threshold': pti_ratio > settings.pti_threshold,
            'exceeds_dti_threshold': dti_ratio > settings.dti_threshold,
            'insufficient_credit_score': credit_score < settings.credit_score_threshold
        }

        return can_afford, metrics

    @staticmethod
    def assess_risk_level(
        cash_affordable: bool,
        financing_affordable: bool,
        cash_metrics: Dict[str, float],
        financing_metrics: Dict[str, float]
    ) -> Tuple[RiskLevel, List[str]]:
        """
        Assess overall risk level

        Returns:
            (risk_level, risk_factors_list)
        """
        risk_factors = []

        # Check cash risk factors
        if cash_metrics.get('exceeds_safe_limit'):
            risk_factors.append("Cash purchase exceeds safe limit (30% of disposable income)")

        if cash_metrics.get('depletes_emergency_fund'):
            risk_factors.append("Purchase would deplete emergency fund below 3 months coverage")

        # Check financing risk factors
        if financing_metrics.get('exceeds_pti_threshold'):
            risk_factors.append("Monthly payment exceeds 15% of income")

        if financing_metrics.get('exceeds_dti_threshold'):
            risk_factors.append("Debt-to-income ratio would exceed 43%")

        if financing_metrics.get('insufficient_credit_score'):
            risk_factors.append("Credit score below 650 (financing may not be available)")

        # Determine risk level
        num_factors = len(risk_factors)

        if num_factors == 0:
            risk_level = FinancialCalculator._create_risk_level("SAFE")
        elif num_factors <= 2:
            risk_level = FinancialCalculator._create_risk_level("CAUTION")
        else:
            risk_level = FinancialCalculator._create_risk_level("RISKY")

        return risk_level, risk_factors

    # ========================================================================
    # CREATIVE FINANCING PATHS
    # ========================================================================

    @staticmethod
    def generate_savings_path(profile: UserProfile, price: float) -> FinancingPath:
        """
        Generate a savings plan to afford the product

        Returns:
            FinancingPath with savings details
        """
        monthly_savings = FinancialCalculator.calculate_safe_cash_limit(profile)
        months_needed = int(price / monthly_savings) + 1 if monthly_savings > 0 else 999

        # Calculate feasibility (prefer under 6 months)
        if months_needed <= 3:
            feasibility = 1.0
        elif months_needed <= 6:
            feasibility = 0.8
        elif months_needed <= 12:
            feasibility = 0.5
        else:
            feasibility = 0.2

        return FinancialCalculator._create_financing_path(
            path_type="save",
            title=f"Save for {months_needed} months",
            description=f"Save ${monthly_savings:.2f}/month for {months_needed} months, then purchase with cash (no debt!).",
            monthly_amount=monthly_savings,
            duration_months=months_needed,
            total_cost=price,
            feasibility_score=feasibility,
            requirements=["Discipline to save monthly", "No immediate need for product"]
        )

    @staticmethod
    def generate_financing_path(
        profile: UserProfile,
        price: float,
        months: int = 12,
        apr: float = 0.0
    ) -> FinancingPath:
        """
        Generate a financing plan

        Returns:
            FinancingPath with financing details
        """
        monthly_income = FinancialCalculator._get_attr(profile, 'monthly_income', 0)

        monthly_payment = FinancialCalculator.calculate_monthly_financing_payment(price, months, apr)
        pti_ratio = FinancialCalculator.calculate_pti_ratio(monthly_payment, monthly_income)
        disposable = FinancialCalculator.calculate_disposable_income(profile)

        # Calculate feasibility
        if pti_ratio <= 0.10:
            feasibility = 1.0
        elif pti_ratio <= settings.pti_threshold:
            feasibility = 0.8
        else:
            feasibility = 0.3

        percentage_of_disposable = (monthly_payment / disposable * 100) if disposable > 0 else 0

        requirements = [f"Credit score >= {settings.credit_score_threshold}"]
        if apr > 0:
            requirements.append(f"Accept {apr*100:.1f}% APR")

        return FinancialCalculator._create_financing_path(
            path_type="finance",
            title=f"{months}-month financing at {apr*100:.1f}% APR",
            description=f"Pay ${monthly_payment:.2f}/month for {months} months. Only {pti_ratio*100:.1f}% of your monthly income ({percentage_of_disposable:.1f}% of disposable income).",
            monthly_amount=monthly_payment,
            duration_months=months,
            total_cost=price * (1 + apr * months / 12) if apr > 0 else price,
            feasibility_score=feasibility,
            requirements=requirements
        )

    @staticmethod
    def generate_extended_financing_path(
        profile: UserProfile,
        price: float,
        months: int = 24,
        apr: float = 0.0
    ) -> FinancingPath:
        """
        Generate extended financing (18-24 months)

        Returns:
            FinancingPath with extended financing details
        """
        return FinancialCalculator.generate_financing_path(profile, price, months, apr)
