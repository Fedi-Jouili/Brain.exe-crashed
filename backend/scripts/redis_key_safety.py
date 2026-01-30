"""
Redis Key Safety Verification - CI Guardrail
Enforces strictly allowed key prefixes and TTL rules

Run: python backend/scripts/redis_key_safety.py
Exit Code: 0 if all keys compliant, 1 if violations found
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.redis_client import redis_manager
import logging

logging.basicConfig(level=logging.INFO)

# 🔐 ALLOWED PREFIXES
ALLOWED_PREFIXES = [
    "search:",
    "product:",
    "session:",
    "thompson:",
    "counter:",
    "timing:",
]

# 🕒 TTL RULES
# Keys that MUST NOT expire
PERSISTENT_PREFIXES = [
    "thompson:",
    "counter:",
    "timing:",
]

# Keys that SHOULD expire (warning only, not hard failure for this check)
TEMPORARY_PREFIXES = [
    "search:",
    "session:",
]


def check_key_safety() -> bool:
    """
    Scan all Redis keys and verify compliance
    
    Returns:
        True if all keys are compliant
    """
    print("=" * 80)
    print("🔐 REDIS KEY SAFETY AUDIT")
    print("=" * 80)
    
    try:
        # Scan keys (using iterator to be memory safe)
        violations = []
        checked_count = 0
        
        # Scan ALL keys
        for key in redis_manager.client.scan_iter("*"):
            checked_count += 1
            is_compliant = False
            
            # 1. Check Namespace (Prefix)
            for prefix in ALLOWED_PREFIXES:
                if key.startswith(prefix):
                    is_compliant = True
                    break
            
            if not is_compliant:
                violations.append(f"❌ ILLEGAL NAMESPACE: '{key}' (Prefix not in {ALLOWED_PREFIXES})")
                continue
            
            # 2. Check Persistence Rules
            ttl = redis_manager.client.ttl(key)
            
            # Per-prefix rules
            if key.startswith("thompson:"):
                if ttl != -1: # -1 means no expiry
                    violations.append(f"❌ DANGEROUS TTL: '{key}' has expiry ({ttl}s) but must be persistent")
            
            # Check for accidental permanent cache keys
            if key.startswith("search:") or key.startswith("session:"):
                if ttl == -1:
                    print(f"⚠️  WARNING: '{key}' has no expiry (potential leak)")
        
        print(f"Checked {checked_count} keys.")
        
        if violations:
            print("\n🚫 SAFETY VIOLATIONS:")
            for v in violations:
                print(v)
                
            print("\n" + "=" * 80)
            print("❌ KEY AUDIT FAILED")
            print("Immediate remediation required: Compliance violation")
            print("=" * 80)
            return False
            
        else:
            print("\n✅ KEY AUDIT PASSED")
            print("All keys conform to namespace and safety rules.")
            print("=" * 80)
            return True
            
    except Exception as e:
        print(f"\n❌ Error during audit: {e}")
        return False


if __name__ == "__main__":
    if check_key_safety():
        sys.exit(0)
    else:
        sys.exit(1)
