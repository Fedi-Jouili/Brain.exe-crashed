# Agent 2.5 (Budget Pathfinder) - Quick Reference

## 🔒 CONTRACT-COMPLIANT IMPLEMENTATION

### Activation
```python
if state['all_unaffordable'] == True:
    # Agent 2.5 runs automatically
```

### Output Format
```python
{
    'alternative_paths': [
        {
            'type': 'savings_plan' | 'extended_financing' | 'cluster_alternative',
            'strategy': str,
            'product_id': str,
            'product_name': str,
            'price': float,
            'description': str,
            'viability_score': float,  # 🔒 ALWAYS 0.0-1.0
            'pros': List[str],
            'cons': List[str],
            'rank': int  # 1-based ranking
        }
        # ... up to 3 paths total
    ]
}
```

---

## 📊 Viability Score Ranges

### Savings Plans (3-6 months)
- **Range:** 0.2 - 1.0
- **Best:** 3 months + <10% disposable income = 1.0
- **Worst:** 6 months + >30% disposable income = 0.2

### Extended Financing (18-36 months)
- **Range:** 0.1 - 1.0
- **Best:** 18mo + PTI≤10% + interest≤5% = 1.0
- **Worst:** 36mo + PTI=20% + interest>20% = 0.2

### Cluster Alternatives (≥5% cheaper)
- **Range:** 0.2 - 0.9
- **Best:** Cash-affordable + 30%+ savings = 0.9
- **Worst:** Not affordable + 5% savings = 0.2

---

## 🎯 Strategy Selection Rules

### When to Use Each Path Type

**Savings Plan** - Best for:
- Short-term goals (3-6 months)
- Users with steady income
- Products ≤6 months of disposable income

**Extended Financing** - Best for:
- Immediate need
- PTI ≤ 20%
- Good credit score (lower APR)

**Cluster Alternative** - Best for:
- Flexible users
- Similar products available
- Price-sensitive scenarios

---

## ✅ Contract Guarantees

1. ✅ **viability_score ∈ [0.0, 1.0]** - Enforced by `min(..., 1.0)` in all calculations
2. ✅ **Maximum 3 paths** - Enforced by `ranked_paths[:3]`
3. ✅ **Sorted DESC** - Enforced by `sorted(key=viability_score, reverse=True)`
4. ✅ **Ranked 1-3** - Added after sorting
5. ✅ **Required fields** - All paths include type, strategy, description, viability_score, pros, cons, rank
6. ✅ **Graceful failure** - Try/except wrapper, returns empty list on error
7. ✅ **No mutations** - Products passed through unchanged
8. ✅ **No Thompson logic** - Pure affordability analysis

---

## 🧪 Testing

### Contract Validation
```bash
python scripts/test_agent2_5_contract.py
```

**Expected:** 6/6 tests PASS

### Test Coverage
1. ✓ viability_score range [0.0, 1.0]
2. ✓ Maximum 3 paths
3. ✓ Ranking and sorting
4. ✓ Required fields
5. ✓ Activation condition
6. ✓ Graceful failure

---

## 📝 Example Usage

```python
from agents.agent2_5_pathfinder import budget_pathfinder_agent

# Unaffordable scenario
state = {
    'user_profile': {
        'monthly_income': 3500,
        'monthly_expenses': 2800,
        'savings': 1500,
        'current_debt': 5000,
        'credit_score': 680
    },
    'candidate_products': [
        {'product_id': 'p1', 'name': 'MacBook Pro', 'price': 2499,
         'cluster_id': 3, 'financing_available': True}
    ],
    'all_unaffordable': True  # 🔒 Triggers Agent 2.5
}

result = budget_pathfinder_agent.execute(state)

for path in result['alternative_paths']:
    print(f"Rank {path['rank']}: {path['type']}")
    print(f"  Viability: {path['viability_score']:.2f}")
    print(f"  {path['description']}")
```

---

## ⚡ Performance

- **Execution Time:** <100ms (without Qdrant)
- **Memory:** Minimal (generates max 3 paths)
- **Dependencies:**
  - Required: `utils.financial`
  - Optional: `core.qdrant_client` (for cluster alternatives)

---

## 🔧 Configuration

No configuration required. All parameters are hard-coded per contract:
- Savings: 3-6 months, ≤30% disposable income
- Financing: 18-36 months, PTI ≤20%
- Alternatives: ≥5% cheaper, same cluster

---

## 🚨 Error Handling

Agent 2.5 **never crashes** the pipeline:
- Invalid data → empty path list
- Missing cluster_id → skip cluster alternatives
- Qdrant unavailable → skip cluster alternatives
- Empty products → empty path list
- Any exception → logged + empty path list

---

## ✨ Status

**PRODUCTION-READY** ✅

All contract requirements met.
All tests passing.
No known issues.
