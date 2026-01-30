"""
Agent 4 Production Monitoring Dashboard

Real-time metrics tracking for Agent 4 in production.
Monitors: trust scores, violations, repetitions, latency.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class Agent4Monitor:
    """
    Production monitoring dashboard for Agent 4

    Tracks and visualizes:
    - Trust score distribution (real-time)
    - Violation frequency (by type)
    - LLM repetition rate
    - Generation latency (percentiles)
    """

    def __init__(self, log_dir: str = "logs/agent4"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Metrics storage
        self.metrics = {
            'trust_scores': [],
            'violations': defaultdict(int),
            'latencies': [],
            'llm_repetitions': 0,
            'llm_calls': 0,
            'fallback_calls': 0,
            'verified_count': 0,
            'total_explanations': 0,
            'errors': []
        }

        self.session_start = time.time()
        self.last_report_time = time.time()

    def record(self, explanation: Dict[str, Any], latency_ms: int, product_name: str = "Unknown"):
        """
        Record explanation metrics

        Args:
            explanation: Explanation object from Agent 4
            latency_ms: Generation time in milliseconds
            product_name: Product name for context
        """
        self.metrics['total_explanations'] += 1

        # Trust score
        trust = explanation.get('trust', 0.0)
        self.metrics['trust_scores'].append({
            'value': trust,
            'timestamp': time.time(),
            'product': product_name
        })

        # Violations
        for violation in explanation.get('violations', []):
            v_type = violation.split(':')[0].strip() if ':' in violation else violation[:40]
            self.metrics['violations'][v_type] += 1

        # LLM usage
        if explanation.get('used_llm', False):
            self.metrics['llm_calls'] += 1
            regen_count = explanation.get('regeneration_count', 0)
            if regen_count > 1:
                self.metrics['llm_repetitions'] += 1
        else:
            self.metrics['fallback_calls'] += 1

        # Verification
        if explanation.get('verified', False):
            self.metrics['verified_count'] += 1

        # Latency
        self.metrics['latencies'].append({
            'value': latency_ms,
            'timestamp': time.time()
        })

        # Auto-report every 10 explanations
        if self.metrics['total_explanations'] % 10 == 0:
            self.print_dashboard()

    def record_error(self, error_msg: str):
        """Record error for monitoring"""
        self.metrics['errors'].append({
            'message': error_msg,
            'timestamp': time.time()
        })

    def get_stats(self) -> Dict[str, Any]:
        """Calculate current statistics"""
        if not self.metrics['trust_scores']:
            return {}

        trust_values = [t['value'] for t in self.metrics['trust_scores']]
        latency_values = [l['value'] for l in self.metrics['latencies']]

        return {
            'session_duration_min': (time.time() - self.session_start) / 60,
            'total_explanations': self.metrics['total_explanations'],
            'trust_score': {
                'current': trust_values[-1] if trust_values else 0,
                'mean': sum(trust_values) / len(trust_values),
                'min': min(trust_values),
                'max': max(trust_values),
                'std': self._std(trust_values),
                'distribution': {
                    '< 0.5 (Low)': sum(1 for t in trust_values if t < 0.5),
                    '0.5-0.7 (Med)': sum(1 for t in trust_values if 0.5 <= t < 0.7),
                    '0.7-0.85 (Good)': sum(1 for t in trust_values if 0.7 <= t < 0.85),
                    '>= 0.85 (Excellent)': sum(1 for t in trust_values if t >= 0.85),
                }
            },
            'violations': {
                'total': sum(self.metrics['violations'].values()),
                'unique_types': len(self.metrics['violations']),
                'top_5': sorted(self.metrics['violations'].items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'llm': {
                'calls': self.metrics['llm_calls'],
                'fallbacks': self.metrics['fallback_calls'],
                'repetitions': self.metrics['llm_repetitions'],
                'repetition_rate_%': (self.metrics['llm_repetitions'] / max(self.metrics['llm_calls'], 1)) * 100
            },
            'verification': {
                'verified': self.metrics['verified_count'],
                'unverified': self.metrics['total_explanations'] - self.metrics['verified_count'],
                'rate_%': (self.metrics['verified_count'] / self.metrics['total_explanations']) * 100
            },
            'latency_ms': {
                'current': latency_values[-1] if latency_values else 0,
                'mean': sum(latency_values) / len(latency_values),
                'min': min(latency_values),
                'max': max(latency_values),
                'p50': self._percentile(latency_values, 50),
                'p95': self._percentile(latency_values, 95),
                'p99': self._percentile(latency_values, 99)
            },
            'errors': {
                'count': len(self.metrics['errors']),
                'recent': self.metrics['errors'][-5:] if self.metrics['errors'] else []
            }
        }

    def print_dashboard(self, force: bool = False):
        """
        Print real-time dashboard

        Args:
            force: Force print even if recently printed
        """
        # Rate limit to once per 5 seconds unless forced
        if not force and (time.time() - self.last_report_time) < 5:
            return

        self.last_report_time = time.time()

        stats = self.get_stats()
        if not stats:
            return

        print("\n" + "="*80)
        print(f"AGENT 4 PRODUCTION DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # Session info
        print(f"\nSession: {stats['session_duration_min']:.1f} min | Explanations: {stats['total_explanations']}")

        # Trust score
        print("\n[TRUST SCORE]")
        ts = stats['trust_score']
        print(f"  Current: {ts['current']:.3f} | Mean: {ts['mean']:.3f} | Range: [{ts['min']:.3f}, {ts['max']:.3f}]")
        print(f"  Distribution:")
        for level, count in ts['distribution'].items():
            pct = (count / stats['total_explanations']) * 100
            bar = '#' * int(pct / 2)
            print(f"    {level:20s} {count:4d} ({pct:5.1f}%) {bar}")

        # Violations
        print("\n[VIOLATIONS]")
        v = stats['violations']
        print(f"  Total: {v['total']} | Unique types: {v['unique_types']}")
        if v['top_5']:
            print(f"  Top types:")
            for v_type, count in v['top_5']:
                print(f"    - {v_type[:60]:60s} {count:3d}")

        # LLM usage
        print("\n[LLM USAGE]")
        llm = stats['llm']
        print(f"  Calls: {llm['calls']} | Fallbacks: {llm['fallbacks']}")
        print(f"  Repetition rate: {llm['repetition_rate_%']:.1f}%", end="")
        if llm['repetition_rate_%'] > 10:
            print(" [!!! HIGH]")
        else:
            print(" [OK]")

        # Verification
        print("\n[VERIFICATION]")
        ver = stats['verification']
        print(f"  Verified: {ver['verified']}/{stats['total_explanations']} ({ver['rate_%']:.1f}%)", end="")
        if ver['rate_%'] < 70:
            print(" [!!! LOW]")
        else:
            print(" [OK]")

        # Latency
        print("\n[LATENCY]")
        lat = stats['latency_ms']
        print(f"  Current: {lat['current']:.0f}ms | Mean: {lat['mean']:.0f}ms")
        print(f"  P50: {lat['p50']:.0f}ms | P95: {lat['p95']:.0f}ms | P99: {lat['p99']:.0f}ms", end="")
        if lat['p95'] > 5000:
            print(" [!!! SLOW]")
        else:
            print(" [OK]")

        # Errors
        if stats['errors']['count'] > 0:
            print("\n[ERRORS]")
            print(f"  Total: {stats['errors']['count']}")
            if stats['errors']['recent']:
                print(f"  Recent:")
                for err in stats['errors']['recent']:
                    print(f"    - {err['message'][:70]}")

        print("\n" + "="*80)

    def export_report(self, filename: str = None):
        """Export detailed JSON report"""
        if filename is None:
            filename = f"agent4_metrics_{int(time.time())}.json"

        filepath = self.log_dir / filename

        stats = self.get_stats()
        stats['exported_at'] = datetime.now().isoformat()

        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"\nMetrics exported to: {filepath}")
        return filepath

    def check_alerts(self) -> List[str]:
        """Check for production alerts"""
        alerts = []
        stats = self.get_stats()

        if not stats:
            return alerts

        # Trust score alerts
        if stats['trust_score']['mean'] < 0.70:
            alerts.append(f"LOW_TRUST: Mean trust {stats['trust_score']['mean']:.3f} < 0.70")

        # Verification rate
        if stats['verification']['rate_%'] < 70:
            alerts.append(f"LOW_VERIFICATION: Rate {stats['verification']['rate_%']:.1f}% < 70%")

        # LLM repetition
        if stats['llm']['repetition_rate_%'] > 10:
            alerts.append(f"HIGH_REPETITION: Rate {stats['llm']['repetition_rate_%']:.1f}% > 10%")

        # Latency
        if stats['latency_ms']['p95'] > 5000:
            alerts.append(f"HIGH_LATENCY: P95 {stats['latency_ms']['p95']:.0f}ms > 5000ms")

        # Errors
        if stats['errors']['count'] > 10:
            alerts.append(f"ERRORS: {stats['errors']['count']} errors detected")

        return alerts

    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _percentile(self, values: List[float], p: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (p / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]


# Global monitor instance
monitor = Agent4Monitor()


def log_explanation(explanation: Dict[str, Any], latency_ms: int, product_name: str = "Unknown"):
    """
    Log explanation to monitor

    Usage in production:
        from scripts.monitor_agent4 import log_explanation

        explanation = rec['explanation']
        log_explanation(explanation, latency_ms, product.name)
    """
    monitor.record(explanation, latency_ms, product_name)


def get_dashboard():
    """Get current dashboard"""
    monitor.print_dashboard(force=True)


def export_metrics(filename: str = None):
    """Export metrics report"""
    return monitor.export_report(filename)


def get_alerts() -> List[str]:
    """Get current alerts"""
    return monitor.check_alerts()


if __name__ == "__main__":
    # Demo usage
    print("Agent 4 Production Monitor - Demo")
    print("="*80)

    # Simulate some metrics
    import random

    for i in range(25):
        # Simulate explanation
        explanation = {
            'text': f'Explanation {i+1}',
            'trust': random.uniform(0.7, 0.95),
            'verified': random.choice([True, True, True, False]),
            'violations': [] if random.random() > 0.3 else ['Price mismatch: test'],
            'used_llm': random.choice([True, False]),
            'regeneration_count': random.choice([1, 1, 1, 2]),
            'type': random.choice(['value-led', 'affordability-led', 'learning-led'])
        }

        latency = random.randint(500, 2500)
        monitor.record(explanation, latency, f'Product-{i+1}')

    # Final dashboard
    monitor.print_dashboard(force=True)

    # Check alerts
    alerts = monitor.check_alerts()
    if alerts:
        print("\n[ALERTS]")
        for alert in alerts:
            print(f"  ! {alert}")
    else:
        print("\n[OK] No alerts")

    # Export
    monitor.export_report("demo_metrics.json")
