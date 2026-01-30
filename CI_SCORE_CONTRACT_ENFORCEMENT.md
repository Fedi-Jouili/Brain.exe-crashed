# 🔒 CI/CD Score Contract Enforcement

## Overview

The PriceSense backend CI pipeline is configured to **prevent score drift** by enforcing the formal scoring contract on every commit.

## CI Workflow

**File:** `.github/workflows/backend-ci.yml`

### Trigger Conditions

- **Push** to `main` or `develop` branches
- **Pull Request** targeting `main` or `develop`
- **Manual** workflow dispatch
- **Path filters:** Only runs when `backend/**` or workflow file changes

### Build Matrix

- Python 3.10
- Python 3.11
- **fail-fast: true** - Stops immediately on first failure

---

## 🔒 Score Contract Tests

### Test Suite 1: Agent 2 (Financial Analyzer)

**File:** `backend/scripts/test_agent2_standalone.py`

**Contract:**
- `financial_score` ∈ [0.0, 1.0]
- No score rescaling
- Graceful failure only

**Tests:** 6/6
- Affordable user scoring
- Unaffordable user detection
- Score sorting (0.0-1.0 range)
- Risk level assessment
- Error handling
- Empty product list

**Build Fails If:**
- Any score < 0.0 or > 1.0
- Scores not in descending order
- Test crashes instead of graceful failure

---

### Test Suite 2: Agent 2.5 (Budget Pathfinder)

**File:** `backend/scripts/test_agent2_5.py`

**Contract:**
- `viability_score` ∈ [0.0, 1.0]
- Maximum 3 paths
- Sorted by viability DESC
- Activation only when `all_unaffordable=True`
- No product mutation

**Tests:** 8/8
- Activation condition
- Maximum 3 paths constraint
- Viability score range
- Sorting by viability
- No product mutation
- Graceful error handling
- Required fields
- State keys

**Build Fails If:**
- Any viability_score < 0.0 or > 1.0
- More than 3 paths returned
- Paths not sorted DESC
- Agent runs when `all_unaffordable=False`
- Input products mutated

---

### Test Suite 3: Formal Score Contract

**File:** `backend/scripts/test_score_contract.py`

**Contract:**
- Agent 2: `financial_score` ∈ [0.0, 1.0]
- Agent 3: Weights = Thompson 0.4, Financial 0.3, RAGAS 0.2, Diversity 0.1
- All scores normalized to [0.0, 1.0] before weighting

**Tests:** 2/2
- Agent 2 score range validation
- Agent 3 weight compliance

**Build Fails If:**
- Agent 2 returns scores outside [0.0, 1.0]
- Agent 3 weights don't sum to 1.0
- Agent 3 weights modified from contract

---

## CI Pipeline Flow

```
┌─────────────────────────────────────────┐
│  1. Checkout Code                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  2. Setup Python 3.10 & 3.11            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  3. Install Dependencies                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  4. Verify Test Files Exist             │
│     ❌ FAIL if any test file missing    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  5. Test Agent 2                        │
│     ✓ 6/6 tests must pass               │
│     ❌ Exit 1 on ANY failure            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  6. Test Agent 2.5                      │
│     ✓ 8/8 tests must pass               │
│     ❌ Exit 1 on ANY failure            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  7. Test Score Contract                 │
│     ✓ 2/2 agents must comply            │
│     ❌ Exit 1 on ANY failure            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  8. Code Quality (flake8)               │
│     Advisory only, doesn't block build  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  ✅ CI SUCCESS                          │
│  Safe to merge                          │
└─────────────────────────────────────────┘
```

---

## Build Failure Scenarios

### Scenario 1: Score Out of Range

```
❌ AGENT 2 CONTRACT VIOLATION DETECTED
   Path 1: viability_score = 1.2 (> 1.0)

Build MUST fail to prevent score drift.
```

**Action:** Fix scoring function to return values in [0.0, 1.0]

---

### Scenario 2: Weight Modification

```
❌ AGENT 3 CONTRACT VIOLATION DETECTED
   Financial weight: 0.25 (expected 0.3)

Build MUST fail to prevent score drift.
```

**Action:** Restore locked weights to contract values

---

### Scenario 3: Max Paths Exceeded

```
❌ AGENT 2.5 CONTRACT VIOLATION DETECTED
   5 paths returned (maximum is 3)

Build MUST fail to prevent score drift.
```

**Action:** Enforce `ranked_paths[:3]` limit

---

### Scenario 4: Product Mutation

```
❌ AGENT 2.5 CONTRACT VIOLATION DETECTED
   Input products were mutated

Build MUST fail to prevent score drift.
```

**Action:** Remove code that modifies input products

---

## Local Testing

Before pushing, run tests locally:

```bash
# Test Agent 2
cd backend
python scripts/test_agent2_standalone.py

# Test Agent 2.5
python scripts/test_agent2_5.py

# Test Score Contract
python scripts/test_score_contract.py
```

All tests must pass (exit code 0) before committing.

---

## Enforcement Rules

### 🚨 CI MUST FAIL if:

1. **Any score exceeds its defined range**
   - Agent 2: financial_score not in [0.0, 1.0]
   - Agent 2.5: viability_score not in [0.0, 1.0]

2. **Any agent returns >3 alternatives**
   - Agent 2.5: Must return ≤3 paths

3. **Any test is removed or skipped**
   - All test files must exist
   - All tests must run

4. **Any agent mutates upstream state**
   - Input products must remain unchanged
   - State mutation detected = build failure

5. **Contract weights modified**
   - Agent 3 weights must remain locked

---

## Quality Bars

✅ **Python 3.10+ Matrix**
- Tests run on Python 3.10 and 3.11
- Ensures compatibility across versions

✅ **Fail-Fast Enabled**
- Stops immediately on first failure
- Saves CI time

✅ **No Flaky Randomness**
- All tests are deterministic
- No random data or timing dependencies

✅ **Clear Logs**
- Detailed output for each test
- Contract requirements displayed
- Violation messages actionable

---

## CI Status Badge

Add to README.md:

```markdown
![Backend CI](https://github.com/YOUR_ORG/PriceSense/actions/workflows/backend-ci.yml/badge.svg)
```

---

## Maintenance

### Adding New Score Contracts

1. Create test file in `backend/scripts/`
2. Add to CI workflow as new step
3. Update this documentation

### Modifying Existing Contracts

❌ **NOT ALLOWED**

The score contract is **LOCKED**. Any modification requires:
1. Formal approval
2. Breaking change documentation
3. Migration plan
4. Updated test suites

---

## Summary

**Purpose:** Prevent score drift and maintain system integrity

**Mechanism:** Automated testing on every commit

**Enforcement:** CI fails if ANY contract violation detected

**Philosophy:** Correctness is mandatory. Convenience is irrelevant.

---

## Status

✅ **Implemented:** Agent 2 (6 tests), Agent 2.5 (8 tests), Score Contract (2 tests)

📊 **Coverage:** 16/16 contract validation tests passing

🔒 **Enforcement:** Active on all commits to main/develop branches
