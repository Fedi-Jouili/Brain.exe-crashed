"""
Example: Using Agent 4 with Production Monitoring

This example demonstrates how to use Agent 4 in production
with real-time monitoring and alerting.
"""

# ============================================================================
# SETUP
# ============================================================================

# Import Agent 4
from agents.agent4_explainer import explainer_agent

# Import monitoring tools
from scripts.monitor_agent4 import (
    log_explanation,
    get_dashboard,
    export_metrics,
    get_alerts,
    monitor
)

import time


# ============================================================================
# EXAMPLE 1: Basic Usage with Monitoring
# ============================================================================

def example_basic_monitoring():
    """Basic Agent 4 usage with monitoring"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage with Monitoring")
    print("="*70)

    # Your state from Agent 3
    state = {
        'query': 'wireless headphones',
        'user_profile': mock_user(),
        'final_recommendations': [
            mock_recommendation("Sony WH-1000XM5", 399.99),
            mock_recommendation("Apple AirPods Pro", 249.99),
            mock_recommendation("Bose QC 45", 329.00)
        ]
    }

    # Execute Agent 4
    start_time = time.time()
    state = explainer_agent.execute(state)
    latency_ms = int((time.time() - start_time) * 1000)

    # Log each explanation to monitor
    for rec in state['final_recommendations']:
        if 'explanation' in rec:
            product_name = rec['product'].get('name', 'Unknown')
            log_explanation(
                explanation=rec['explanation'],
                latency_ms=latency_ms // len(state['final_recommendations']),
                product_name=product_name
            )

    print(f"\nProcessed {len(state['final_recommendations'])} recommendations")
    print(f"Total latency: {latency_ms}ms")


# ============================================================================
# EXAMPLE 2: Production API Endpoint with Monitoring
# ============================================================================

def example_production_api():
    """Simulated API endpoint with full monitoring"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Production API with Monitoring")
    print("="*70)

    # Process 10 requests
    for request_id in range(1, 11):
        # Get recommendations (from Agent 3)
        state = {
            'query': f'search query {request_id}',
            'user_profile': mock_user(),
            'final_recommendations': [
                mock_recommendation(f"Product {request_id}A", 299.99),
                mock_recommendation(f"Product {request_id}B", 399.99),
            ]
        }

        # Execute Agent 4 with timing
        start_time = time.time()
        try:
            state = explainer_agent.execute(state)
            latency_ms = int((time.time() - start_time) * 1000)

            # Log to monitor
            for rec in state['final_recommendations']:
                if 'explanation' in rec:
                    product_name = rec['product'].get('name', 'Unknown')
                    log_explanation(
                        explanation=rec['explanation'],
                        latency_ms=latency_ms // 2,
                        product_name=product_name
                    )

            print(f"Request {request_id}: OK ({latency_ms}ms)")

        except Exception as e:
            print(f"Request {request_id}: ERROR - {e}")
            monitor.record_error(str(e))

    # View dashboard after batch
    print("\n" + "-"*70)
    get_dashboard()


# ============================================================================
# EXAMPLE 3: Alert-Based Monitoring
# ============================================================================

def example_alert_monitoring():
    """Monitor with automated alerts"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Alert-Based Monitoring")
    print("="*70)

    # Process requests
    for i in range(15):
        state = {
            'final_recommendations': [
                mock_recommendation(f"Product {i}", 199.99)
            ]
        }

        start = time.time()
        state = explainer_agent.execute(state)
        latency = int((time.time() - start) * 1000)

        # Log
        for rec in state['final_recommendations']:
            if 'explanation' in rec:
                log_explanation(rec['explanation'], latency, f"Product {i}")

    # Check for alerts
    alerts = get_alerts()

    if alerts:
        print("\n[ALERTS DETECTED]")
        for alert in alerts:
            print(f"  ! {alert}")

            # In production: send to monitoring system
            # send_to_datadog(alert)
            # send_to_slack(alert)
            # send_email_alert(alert)
    else:
        print("\n[OK] No alerts - system healthy")


# ============================================================================
# EXAMPLE 4: Metrics Export for Analysis
# ============================================================================

def example_metrics_export():
    """Export metrics for offline analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Metrics Export")
    print("="*70)

    # Process some requests
    for i in range(20):
        state = {
            'final_recommendations': [
                mock_recommendation(f"Product {i}", 299.99)
            ]
        }

        state = explainer_agent.execute(state)

        for rec in state['final_recommendations']:
            if 'explanation' in rec:
                log_explanation(rec['explanation'], 1500, f"Product {i}")

    # Export metrics
    report_file = export_metrics("example_metrics.json")
    print(f"\nMetrics exported to: {report_file}")
    print("\nReport includes:")
    print("  - Trust score statistics (mean, std, percentiles)")
    print("  - Violation breakdown by type")
    print("  - LLM usage patterns")
    print("  - Latency distribution")
    print("  - Error logs")


# ============================================================================
# EXAMPLE 5: Custom Monitoring Logic
# ============================================================================

def example_custom_monitoring():
    """Custom monitoring with thresholds"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Custom Monitoring Thresholds")
    print("="*70)

    # Your custom thresholds
    TRUST_THRESHOLD = 0.75
    MAX_LATENCY_MS = 3000
    MAX_ERROR_RATE = 0.05

    success_count = 0
    error_count = 0
    low_trust_count = 0
    high_latency_count = 0

    # Process requests
    for i in range(50):
        state = {
            'final_recommendations': [
                mock_recommendation(f"Product {i}", 199.99)
            ]
        }

        start = time.time()
        try:
            state = explainer_agent.execute(state)
            latency = int((time.time() - start) * 1000)

            for rec in state['final_recommendations']:
                if 'explanation' in rec:
                    exp = rec['explanation']

                    # Check trust
                    if exp['trust'] < TRUST_THRESHOLD:
                        low_trust_count += 1

                    # Check latency
                    if latency > MAX_LATENCY_MS:
                        high_latency_count += 1

                    # Log
                    log_explanation(exp, latency, f"Product {i}")

            success_count += 1

        except Exception as e:
            error_count += 1
            monitor.record_error(str(e))

    # Calculate metrics
    total = success_count + error_count
    error_rate = error_count / total if total > 0 else 0

    print(f"\nCustom Metrics:")
    print(f"  Total requests: {total}")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count} (rate: {error_rate*100:.1f}%)")
    print(f"  Low trust: {low_trust_count}")
    print(f"  High latency: {high_latency_count}")

    # Check thresholds
    print(f"\nThreshold Checks:")
    print(f"  Error rate: {error_rate*100:.1f}% {'[OK]' if error_rate < MAX_ERROR_RATE else '[ALERT]'}")
    print(f"  Low trust count: {low_trust_count} {'[OK]' if low_trust_count < 10 else '[ALERT]'}")


# ============================================================================
# HELPER FUNCTIONS (for examples)
# ============================================================================

def mock_user():
    """Create mock user"""
    return type('User', (), {
        'user_id': 'test-user',
        'monthly_income': 5000.0,
        'credit_score': 720,
        'preferences': {}
    })()


def mock_recommendation(product_name: str, price: float):
    """Create mock recommendation"""
    return {
        'product': {
            'product_id': f'prod-{product_name.replace(" ", "-")}',
            'name': product_name,
            'price': price,
            'category': 'Electronics',
            'brand': product_name.split()[0],
            'rating': 4.5,
            'num_reviews': 1000,
            'financing_available': True,
            'cluster_id': 1
        },
        'rank': 1,
        'final_score': 0.9,
        'scores': {
            'thompson': 0.85,
            'collaborative': 0.8,
            'ragas': 0.9,
            'financial': 0.95
        },
        'affordability': {
            'can_afford_cash': True,
            'can_afford_financing': True,
            'risk_level': 'LOW',
            'disposable_income': 2500.0
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGENT 4 PRODUCTION MONITORING - EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate:")
    print("  1. Basic usage with monitoring")
    print("  2. Production API pattern")
    print("  3. Alert-based monitoring")
    print("  4. Metrics export")
    print("  5. Custom monitoring logic")

    # Run examples
    example_basic_monitoring()
    example_production_api()
    example_alert_monitoring()
    example_metrics_export()
    example_custom_monitoring()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Adapt these patterns to your production code")
    print("  2. Set up automated alerting (email, Slack, PagerDuty)")
    print("  3. Integrate with your monitoring stack (Datadog, CloudWatch, etc.)")
    print("  4. Schedule regular metrics exports for analysis")
    print("\n")
