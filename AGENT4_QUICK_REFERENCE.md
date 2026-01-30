# Agent 4 Quick Reference

## File Location
`backend/agents/agent4_explainer.py`

## Import
```python
from agents.agent4_explainer import explainer_agent
```

## Usage
```python
# After Agent 3 generates recommendations
state = explainer_agent.execute(state)

# Access explanation for first recommendation
rec = state['final_recommendations'][0]
explanation = rec['explanation']

print(f"Text: {explanation['text']}")
print(f"Trust: {explanation['trust']:.2f}")
print(f"Verified: {explanation['verified']}")
```

## Explanation Object
```python
{
    'text': str,                    # Human-readable explanation
    'trust': float,                 # [0.0, 1.0] range
    'verified': bool,               # trust >= threshold
    'violations': List[str],        # Structured violation messages
    'used_llm': bool,               # True=Gemini, False=fallback
    'regeneration_count': int,      # LLM attempts made
    'type': str                     # Classification: affordability-led | value-led | learning-led
}
```

## Contracts (MUST ENFORCE)

### 1. Trust Scores in [0.0, 1.0]
```python
# ✅ Correct
trust = 0.92  # Normalized

# ❌ Wrong
trust = 92.0  # Percentage
```

### 2. Immutability
```python
# ✅ Correct
rec['explanation'] = {...}

# ❌ Wrong
rec['trust_score'] = 0.92  # In-place mutation
```

### 3. Privacy Boundaries
```python
# ✅ Correct
financial_standing = "excellent"  # Derived label

# ❌ Wrong
monthly_income = 5000.0  # Raw number to LLM
credit_score = 750
```

### 4. Fallback Trust Cap
```python
# ✅ Correct
fallback_trust = 0.85  # < 1.0 (epistemic humility)

# ❌ Wrong
fallback_trust = 1.0  # Overconfident
```

### 5. LLM Repetition Detection
```python
# ✅ Implemented
if explanation == previous_explanation:
    logger.warning("LLM repeated, stopping retry")
    break
```

## Verification Checks

| Check                 | Impact | Example                     |
| --------------------- | ------ | --------------------------- |
| Product name          | -0.10  | Name not mentioned          |
| Price (>1% error)     | -0.20  | Mentioned $499, actual $399 |
| Rating (>0.5 error)   | -0.15  | Mentioned 5.0, actual 4.2   |
| Affordability claim   | -0.15  | Claimed affordable when not |
| Hallucinated features | -0.05  | "Includes free..."          |
| Brand missing         | -0.05  | Brand not mentioned         |
| Category missing      | -0.05  | Category not mentioned      |

## Configuration

```python
# backend/core/config.py
llm_model = "gemini-1.5-flash"
llm_temperature = 0.3
llm_max_tokens = 150

# Agent 4 constants
trust_threshold = 0.70  # 70% minimum
fallback_trust = 0.85   # Fallback cap
max_regeneration_attempts = 2
```

## Environment Variables
```bash
# .env file
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Explanation Types

| Type                  | Trigger                                  | Example                                           |
| --------------------- | ---------------------------------------- | ------------------------------------------------- |
| **affordability-led** | !can_afford_cash && can_afford_financing | "Financing options available for this product..." |
| **learning-led**      | thompson_score > 0.8                     | "This popular choice is highly rated by users..." |
| **value-led**         | Default                                  | "Great value with strong ratings and features..." |

## Testing

```bash
# Run contract validation tests
cd backend
python scripts/test_agent4_contracts.py

# Expected output:
# ✅ PASS: Trust Score Range [0.0, 1.0]
# ✅ PASS: Immutability
# ✅ PASS: Fallback Trust Cap
# ✅ PASS: No Raw Financial Data
# ✅ PASS: Violation Format
# ✅ PASS: Verified Semantics
```

## Common Issues

### Issue: Trust scores > 1.0
**Fix:** Check verification penalties don't produce negative scores
```python
trust_score = max(0.0, min(1.0, trust_score))  # Clamp
```

### Issue: LLM repetition loop
**Fix:** Already implemented - repetition detection breaks loop
```python
if explanation == previous_explanation:
    break
```

### Issue: Raw financial data leaking to LLM
**Fix:** Use _gather_context() which anonymizes
```python
# Converts: credit_score=750 → financial_standing="excellent"
```

### Issue: Fallback trust = 1.0
**Fix:** Already enforced at 0.85
```python
assert fallback_trust < 1.0  # Contract validation
```

## Logging

```python
# Initialization
logger.info("Gemini LLM initialized: gemini-1.5-flash")

# Execution
logger.info("Agent 4: Starting explanation generation")
logger.info("Explained #1: trust=0.92, violations=0, verified=True")

# Warnings
logger.warning("Low trust (0.65), will retry. Violations: [...]")
logger.warning("LLM repeated same output, stopping retry")

# Errors
logger.error("Failed to explain recommendation #1: API error")
```

## Monitoring Metrics

Track these in production:

| Metric              | Target | Alert If |
| ------------------- | ------ | -------- |
| Trust score avg     | > 0.80 | < 0.70   |
| Verification rate   | > 85%  | < 70%    |
| LLM repetition rate | < 5%   | > 10%    |
| Generation latency  | < 2s   | > 5s     |
| Fallback rate       | < 20%  | > 50%    |

## Pipeline Integration

```python
# services/orchestrator.py

state = agent1.execute(state)   # Discovery
state = agent2.execute(state)   # Financial Analysis
state = agent3.execute(state)   # Recommendations
state = explainer_agent.execute(state)  # ← Agent 4 Explanations

return state
```

## Example Output

```json
{
  "text": "Sony WH-1000XM5 Wireless Headphones is an Electronics from Sony with a strong 4.8/5 rating (2547 reviews). You can afford this with cash. This is our top recommendation for your needs.",
  "trust": 0.92,
  "verified": true,
  "violations": [],
  "used_llm": false,
  "regeneration_count": 0,
  "type": "value-led"
}
```

## Semantic Clarification

### `verified` Field

| Scenario       | `verified` | `trust` | Meaning                     |
| -------------- | ---------- | ------- | --------------------------- |
| LLM high trust | `True`     | ≥ 0.70  | Factual verification passed |
| LLM low trust  | `False`    | < 0.70  | Violations detected         |
| Fallback       | `True`     | 0.85    | Template is consistent      |
| Error          | `False`    | 0.0     | Generation failed           |

**Key:** `verified=True` does NOT mean "LLM is confident" - it means "factual checks passed"

## Contract Validation

Runs automatically on import:

```python
# Validates on module load
✓ Trust threshold in valid range
✓ Fallback trust enforces epistemic humility
✓ Fallback trust in reasonable range
✅ Agent 4 contracts validated
```

## Quick Debugging

```python
# Check if explanation was generated
if 'explanation' not in rec:
    print("Agent 4 didn't run or failed")

# Check trust score
if rec['explanation']['trust'] < 0.70:
    print(f"Low trust: {rec['explanation']['violations']}")

# Check if LLM was used
if not rec['explanation']['used_llm']:
    print("Using fallback explanation (LLM unavailable)")

# Check violations
for violation in rec['explanation']['violations']:
    print(f"Violation: {violation}")
```

## CI Integration

```yaml
# .github/workflows/backend-ci.yml

- name: Test Agent 4 Contracts
  run: python backend/scripts/test_agent4_contracts.py

- name: Verify Trust Scores
  run: |
    if grep -r "trust.*[2-9][0-9]\." backend/agents/agent4_explainer.py; then
      echo "ERROR: Trust scores must be in [0.0, 1.0] range"
      exit 1
    fi
```

## Best Practices

1. **Always check `verified` before displaying** - Low trust explanations may contain errors
2. **Log violations in production** - Track common failure patterns
3. **Monitor trust score distribution** - Adjust verification rules if needed
4. **Never bypass privacy boundaries** - Financial data stays server-side
5. **Test both LLM and fallback modes** - Ensure graceful degradation

## Summary

- **Contract:** All scores in [0.0, 1.0] range
- **Safety:** LLM repetition detection + fallback mode
- **Privacy:** No raw financial data to LLM
- **Philosophy:** Fallback trust = 0.85 (epistemic humility)
- **Quality:** Structured violations for debugging

**Agent 4 is production-ready with full contract enforcement.**
