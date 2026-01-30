# Agent 2 Quick Reference

## Test Command
```bash
cd backend
python scripts/test_agent2_standalone.py
```

## Expected Output
```
Results: 6/6 tests passed
SUCCESS: All tests passed!
Agent 2 is production-ready.
```

## Files Modified
1. **backend/agents/agent2_financial.py** - Agent 2 implementation
2. **backend/utils/financial.py** - Financial calculator utilities
3. **backend/scripts/test_agent2_standalone.py** - Standalone test suite (NEW)

## Key Features
- ✅ RAG-enhanced financial rule retrieval (Qdrant)
- ✅ Cash + financing affordability analysis
- ✅ 0-100 financial scoring (deterministic)
- ✅ SAFE/CAUTION/RISKY risk assessment
- ✅ Graceful error handling (never crashes)
- ✅ Optional dependencies (works without Qdrant/models)
- ✅ Dict/Pydantic compatibility

## API

### Input
```python
state = {
    "query": "laptop",
    "user_profile": {
        "monthly_income": 5000.0,
        "monthly_expenses": 3000.0,
        "savings": 10000.0,
        "current_debt": 0.0,
        "credit_score": 720
    },
    "candidate_products": [...]  # From Agent 1
}
```

### Output
```python
{
    "affordable_products": [
        {
            "product": {...},
            "affordability": {
                "can_afford_cash": True,
                "can_afford_financing": True,
                "risk_level": "SAFE",
                "recommendation": "..."
            },
            "financial_score": 100.0
        }
    ],
    "all_unaffordable": False
}
```

## Financial Score (0-100)
**Weighted Components**:
- Cash affordability: 40%
- Financing affordability: 30%
- Risk level: 30% (SAFE=30, CAUTION=15, RISKY=0)

## Risk Levels
- **SAFE**: 0 risk factors
- **CAUTION**: 1-2 risk factors
- **RISKY**: 3+ risk factors

## Error Handling
- Invalid products → Skip (log error)
- Missing price → Skip product
- Qdrant unavailable → Empty financial rules
- All errors → Appended to `state['errors']`

## Production Guarantees
✅ No breaking changes
✅ Never crashes
✅ Returns empty list on total failure
✅ Works without optional dependencies
✅ Backward compatible with existing pipeline
