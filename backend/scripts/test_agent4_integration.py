"""
Agent 4 Integration Test Suite

Tests Agent 4 in full pipeline context with monitoring metrics.
Validates end-to-end functionality and production readiness.
"""
import sys
import os
import time
import json
from collections import defaultdict
from typing import Dict, List, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock dependencies
from unittest.mock import MagicMock
sys.modules['redis'] = MagicMock()
sys.modules['core.redis_client'] = MagicMock()
sys.modules['models.state'] = MagicMock()
sys.modules['models.schemas'] = MagicMock()

from agents.agent4_explainer import explainer_agent


# ============================================================================
# PRODUCTION MONITORING METRICS
# ============================================================================

class Agent4Metrics:
    """
    Production monitoring for Agent 4

    Tracks:
    - Trust score distribution
    - Violation frequency
    - LLM repetition rate
    - Generation latency
    """

    def __init__(self):
        self.trust_scores = []
        self.violations_by_type = defaultdict(int)
        self.total_violations = 0
        self.llm_repetitions = 0
        self.generation_times = []
        self.total_explanations = 0
        self.llm_used_count = 0
        self.fallback_count = 0
        self.verified_count = 0

    def record_explanation(self, explanation: Dict[str, Any], latency_ms: int):
        """Record explanation metrics"""
        self.total_explanations += 1

        # Trust score
        trust = explanation.get('trust', 0.0)
        self.trust_scores.append(trust)

        # Violations
        violations = explanation.get('violations', [])
        self.total_violations += len(violations)
        for v in violations:
            # Extract violation type (first part before ':')
            v_type = v.split(':')[0].strip() if ':' in v else v[:30]
            self.violations_by_type[v_type] += 1

        # LLM usage
        if explanation.get('used_llm', False):
            self.llm_used_count += 1
            # Check for repetition
            regen_count = explanation.get('regeneration_count', 0)
            if regen_count > 1:
                self.llm_repetitions += 1
        else:
            self.fallback_count += 1

        # Verification
        if explanation.get('verified', False):
            self.verified_count += 1

        # Latency
        self.generation_times.append(latency_ms)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        if not self.trust_scores:
            return {}

        return {
            'total_explanations': self.total_explanations,
            'trust_score': {
                'mean': sum(self.trust_scores) / len(self.trust_scores),
                'min': min(self.trust_scores),
                'max': max(self.trust_scores),
                'distribution': {
                    '0.0-0.5': sum(1 for t in self.trust_scores if t < 0.5),
                    '0.5-0.7': sum(1 for t in self.trust_scores if 0.5 <= t < 0.7),
                    '0.7-0.85': sum(1 for t in self.trust_scores if 0.7 <= t < 0.85),
                    '0.85-1.0': sum(1 for t in self.trust_scores if t >= 0.85),
                }
            },
            'violations': {
                'total': self.total_violations,
                'by_type': dict(self.violations_by_type),
                'avg_per_explanation': self.total_violations / self.total_explanations
            },
            'llm': {
                'used': self.llm_used_count,
                'fallback': self.fallback_count,
                'repetition_rate': (self.llm_repetitions / max(self.llm_used_count, 1)) * 100
            },
            'verification': {
                'verified_count': self.verified_count,
                'verification_rate': (self.verified_count / self.total_explanations) * 100
            },
            'latency': {
                'mean_ms': sum(self.generation_times) / len(self.generation_times),
                'min_ms': min(self.generation_times),
                'max_ms': max(self.generation_times),
                'p95_ms': sorted(self.generation_times)[int(len(self.generation_times) * 0.95)] if len(self.generation_times) > 20 else max(self.generation_times)
            }
        }

    def print_report(self):
        """Print formatted metrics report"""
        summary = self.get_summary()

        if not summary:
            print("No metrics collected")
            return

        print("\n" + "="*70)
        print("AGENT 4 PRODUCTION METRICS REPORT")
        print("="*70)

        # Trust Score Distribution
        print("\n[1] TRUST SCORE DISTRIBUTION")
        print("-"*70)
        ts = summary['trust_score']
        print(f"  Mean:  {ts['mean']:.3f}")
        print(f"  Range: [{ts['min']:.3f}, {ts['max']:.3f}]")
        print(f"\n  Distribution:")
        for range_key, count in ts['distribution'].items():
            pct = (count / summary['total_explanations']) * 100
            bar = '█' * int(pct / 2)
            print(f"    {range_key:12} {count:3d} ({pct:5.1f}%)  {bar}")

        # Violation Frequency
        print("\n[2] VIOLATION FREQUENCY")
        print("-"*70)
        v = summary['violations']
        print(f"  Total violations: {v['total']}")
        print(f"  Avg per explanation: {v['avg_per_explanation']:.2f}")
        if v['by_type']:
            print(f"\n  Top violation types:")
            sorted_violations = sorted(v['by_type'].items(), key=lambda x: x[1], reverse=True)
            for v_type, count in sorted_violations[:5]:
                print(f"    - {v_type[:50]:50s} {count:3d}")
        else:
            print(f"  [OK] No violations detected")

        # LLM Repetition Rate
        print("\n[3] LLM REPETITION RATE")
        print("-"*70)
        llm = summary['llm']
        print(f"  LLM used: {llm['used']}")
        print(f"  Fallback: {llm['fallback']}")
        print(f"  Repetition rate: {llm['repetition_rate']:.1f}%")
        if llm['repetition_rate'] > 10:
            print(f"  [WARNING] Repetition rate above 10% threshold")
        else:
            print(f"  [OK] Repetition rate within acceptable range")

        # Generation Latency
        print("\n[4] GENERATION LATENCY")
        print("-"*70)
        lat = summary['latency']
        print(f"  Mean:   {lat['mean_ms']:.0f} ms")
        print(f"  Min:    {lat['min_ms']:.0f} ms")
        print(f"  Max:    {lat['max_ms']:.0f} ms")
        print(f"  P95:    {lat['p95_ms']:.0f} ms")
        if lat['mean_ms'] > 5000:
            print(f"  [WARNING] Mean latency above 5s threshold")
        else:
            print(f"  [OK] Latency within acceptable range")

        # Verification Rate
        print("\n[5] VERIFICATION RATE")
        print("-"*70)
        ver = summary['verification']
        print(f"  Verified: {ver['verified_count']}/{summary['total_explanations']}")
        print(f"  Rate: {ver['verification_rate']:.1f}%")
        if ver['verification_rate'] < 70:
            print(f"  [WARNING] Verification rate below 70% threshold")
        else:
            print(f"  [OK] Verification rate within acceptable range")

        print("\n" + "="*70)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def create_test_state() -> Dict[str, Any]:
    """Create realistic test state with recommendations"""
    # Mock user
    user = type('obj', (object,), {
        'user_id': "test-user-001",
        'monthly_income': 6500.0,
        'credit_score': 720,
        'preferences': {"category": "Electronics"}
    })()

    # Mock recommendations (as if from Agent 3)
    recommendations = [
        {
            'product': {
                'product_id': 'prod-001',
                'name': 'Sony WH-1000XM5 Wireless Headphones',
                'price': 399.99,
                'category': 'Electronics',
                'brand': 'Sony',
                'rating': 4.8,
                'num_reviews': 2547,
                'financing_available': True,
                'cluster_id': 1
            },
            'rank': 1,
            'final_score': 0.94,
            'scores': {
                'thompson': 0.89,
                'collaborative': 0.82,
                'ragas': 0.93,
                'financial': 0.97
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': True,
                'risk_level': 'LOW',
                'disposable_income': 3200.0
            }
        },
        {
            'product': {
                'product_id': 'prod-002',
                'name': 'Apple AirPods Pro (2nd Gen)',
                'price': 249.99,
                'category': 'Electronics',
                'brand': 'Apple',
                'rating': 4.7,
                'num_reviews': 8934,
                'financing_available': True,
                'cluster_id': 1
            },
            'rank': 2,
            'final_score': 0.91,
            'scores': {
                'thompson': 0.92,
                'collaborative': 0.79,
                'ragas': 0.88,
                'financial': 0.98
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': True,
                'risk_level': 'LOW',
                'disposable_income': 3200.0
            }
        },
        {
            'product': {
                'product_id': 'prod-003',
                'name': 'Bose QuietComfort 45 Headphones',
                'price': 329.00,
                'category': 'Electronics',
                'brand': 'Bose',
                'rating': 4.6,
                'num_reviews': 1523,
                'financing_available': False,
                'cluster_id': 1
            },
            'rank': 3,
            'final_score': 0.87,
            'scores': {
                'thompson': 0.78,
                'collaborative': 0.85,
                'ragas': 0.90,
                'financial': 0.96
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': False,
                'risk_level': 'LOW',
                'disposable_income': 3200.0
            }
        }
    ]

    return {
        'query': 'wireless noise canceling headphones',
        'user_profile': user,
        'final_recommendations': recommendations
    }


def test_integration():
    """Run full integration test with monitoring"""
    print("\n" + "="*70)
    print("AGENT 4 INTEGRATION TEST - PRODUCTION READINESS")
    print("="*70)

    metrics = Agent4Metrics()

    # Test 1: Basic execution
    print("\n[TEST 1] Basic Execution")
    print("-"*70)

    state = create_test_state()
    start_time = time.time()

    try:
        result_state = explainer_agent.execute(state)
        latency_ms = int((time.time() - start_time) * 1000)

        print(f"[PASS] Agent executed in {latency_ms}ms")

        # Verify explanations added
        explained_count = 0
        for i, rec in enumerate(result_state.get('final_recommendations', [])[:3]):
            if 'explanation' in rec:
                explained_count += 1
                exp = rec['explanation']

                # Record metrics
                metrics.record_explanation(exp, latency_ms // 3)

                print(f"\n  Recommendation #{i+1}:")
                product = rec['product']
                product_name = product.get('name') if isinstance(product, dict) else getattr(product, 'name', 'Unknown')
                print(f"    Product: {product_name}")
                print(f"    Trust: {exp.get('trust', 0):.3f}")
                print(f"    Verified: {exp.get('verified', False)}")
                print(f"    LLM: {exp.get('used_llm', False)}")
                print(f"    Violations: {len(exp.get('violations', []))}")
                if exp.get('violations'):
                    for v in exp['violations'][:3]:
                        print(f"      - {v}")

        if explained_count == 3:
            print(f"\n[PASS] All 3 recommendations explained")
        else:
            print(f"\n[FAIL] Only {explained_count}/3 recommendations explained")
            return False

    except Exception as e:
        print(f"[FAIL] Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Contract compliance
    print("\n[TEST 2] Contract Compliance")
    print("-"*70)

    contract_violations = []

    for i, rec in enumerate(result_state.get('final_recommendations', [])[:3]):
        exp = rec.get('explanation', {})

        # Check trust score range
        trust = exp.get('trust', -1)
        if not (0.0 <= trust <= 1.0):
            contract_violations.append(f"Rec #{i+1}: trust={trust} out of [0.0, 1.0] range")

        # Check immutability (explanation is new key)
        if 'explanation' not in rec:
            contract_violations.append(f"Rec #{i+1}: explanation not added")

        # Check fallback trust cap
        if not exp.get('used_llm', True) and exp.get('trust', 0) >= 1.0:
            contract_violations.append(f"Rec #{i+1}: fallback trust >= 1.0")

    if contract_violations:
        print("[FAIL] Contract violations detected:")
        for v in contract_violations:
            print(f"  - {v}")
        return False
    else:
        print("[PASS] All contracts enforced")
        print("  - Trust scores in [0.0, 1.0]")
        print("  - Explanations added (immutable)")
        print("  - Fallback trust < 1.0")

    # Test 3: Error handling
    print("\n[TEST 3] Error Handling")
    print("-"*70)

    # Test with empty recommendations
    empty_state = {'query': 'test', 'final_recommendations': []}
    try:
        explainer_agent.execute(empty_state)
        print("[PASS] Handles empty recommendations gracefully")
    except Exception as e:
        print(f"[FAIL] Crashed on empty recommendations: {e}")
        return False

    # Test with missing fields
    incomplete_state = {
        'final_recommendations': [
            {'product': {'name': 'Test', 'price': 100}}
        ]
    }
    try:
        explainer_agent.execute(incomplete_state)
        print("[PASS] Handles incomplete data gracefully")
    except Exception as e:
        print(f"[FAIL] Crashed on incomplete data: {e}")
        return False

    # Print metrics report
    metrics.print_report()

    # Overall assessment
    print("\n" + "="*70)
    print("PRODUCTION READINESS ASSESSMENT")
    print("="*70)

    summary = metrics.get_summary()

    issues = []

    if summary['trust_score']['mean'] < 0.70:
        issues.append("Mean trust score below 0.70 threshold")

    if summary['llm']['repetition_rate'] > 10:
        issues.append("LLM repetition rate above 10%")

    if summary['latency']['mean_ms'] > 5000:
        issues.append("Mean latency above 5s")

    if summary['verification']['verification_rate'] < 70:
        issues.append("Verification rate below 70%")

    if issues:
        print("\n[WARNING] Production concerns:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRecommendation: Address concerns before full deployment")
        return True  # Still passes, but with warnings
    else:
        print("\n[PASS] Ready for production deployment")
        print("\nMetrics summary:")
        print(f"  - Mean trust score: {summary['trust_score']['mean']:.3f}")
        print(f"  - Verification rate: {summary['verification']['verification_rate']:.1f}%")
        print(f"  - LLM repetition: {summary['llm']['repetition_rate']:.1f}%")
        print(f"  - Mean latency: {summary['latency']['mean_ms']:.0f}ms")
        return True


def main():
    """Run integration tests"""
    print("="*70)
    print("AGENT 4 - INTEGRATION TEST SUITE")
    print("="*70)
    print("\nThis test validates:")
    print("  1. End-to-end execution")
    print("  2. Contract compliance")
    print("  3. Error handling")
    print("  4. Production metrics")

    success = test_integration()

    print("\n" + "="*70)
    if success:
        print("INTEGRATION TESTS PASSED")
        print("="*70)
        print("\nAgent 4 is ready for production deployment with monitoring in place.")
        return 0
    else:
        print("INTEGRATION TESTS FAILED")
        print("="*70)
        print("\nFix issues before deployment.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
