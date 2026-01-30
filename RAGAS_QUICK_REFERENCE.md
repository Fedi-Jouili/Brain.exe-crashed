# RAGAS Evaluator - Quick Reference Card

**One-page guide for developers**

---

## 🚀 Installation (1 command)
```bash
pip install -r backend/requirements_ragas.txt
```

---

## 📝 Basic Usage (5 lines)
```python
from ragas_evaluator import RAGASEvaluator

evaluator = RAGASEvaluator()
scores = evaluator.evaluate_single(
    question="Why is this affordable?",
    answer="It's affordable because DTI is 38%",
    contexts=["DTI should be below 43%"]
)
# Returns: {'context_precision': 0.95, 'faithfulness': 0.92, 'answer_relevancy': 0.88}
```

---

## 🎯 4 Methods

| Method                                                                 | Purpose                    | Returns               | Time   |
| ---------------------------------------------------------------------- | -------------------------- | --------------------- | ------ |
| `evaluate_single(question, answer, contexts, ground_truth)`            | Evaluate one QA pair       | Dict (scores 0-1)     | ~600ms |
| `evaluate_batch(questions, answers, contexts_list, ground_truths)`     | Evaluate multiple QA pairs | Dict (avg scores 0-1) | ~5-7s  |
| `calculate_query_product_relevancy(query, product_name, product_desc)` | Query-product match        | Float (0-100)         | ~600ms |
| `_neutral_scores()`                                                    | Fallback on error          | Dict (all 0.5)        | 0ms    |

---

## 📊 Metric Meanings

| Metric                | Question                        | Threshold |
| --------------------- | ------------------------------- | --------- |
| **context_precision** | Are retrieved docs relevant?    | > 0.85    |
| **faithfulness**      | Does answer stick to context?   | > 0.90    |
| **answer_relevancy**  | Is answer relevant to question? | > 0.85    |
| **context_recall**    | Did we get all needed info?     | > 0.80    |

---

## 🤖 Agent Integration

### Agent 2 (Financial) - Validate RAG
```python
scores = evaluator.evaluate_single(question, answer, contexts)
if scores["faithfulness"] < 0.90:
    regenerate_answer()  # Potential hallucination
```

### Agent 3 (Recommender) - Score Products
```python
relevancy = evaluator.calculate_query_product_relevancy(query, name, desc)
composite = 0.4*thompson + 0.2*financial + 0.2*(relevancy/100) + 0.2*vector
```

### Agent 4 (Explainer) - Verify Explanation
```python
for attempt in range(3):
    explanation = generate_with_gemini(question, contexts)
    scores = evaluator.evaluate_single(question, explanation, contexts)
    if scores["faithfulness"] >= 0.90:
        return explanation  # Approved
# Use fallback if all fail
```

---

## ⚡ Performance

- **Single eval**: 600-800ms (RAGAS uses LLM internally)
- **Batch (10)**: 5-7 seconds (more efficient)
- **Import**: <2 seconds

**Optimization**: Use batch evaluation when possible, cache results

---

## 🎯 Thresholds Quick Guide

| Score     | Quality   | Action             |
| --------- | --------- | ------------------ |
| 0.90-1.00 | Excellent | ✅ Accept           |
| 0.85-0.89 | Good      | ✅ Accept (monitor) |
| 0.70-0.84 | Moderate  | ⚠️ Flag for review  |
| 0.50-0.69 | Poor      | ❌ Regenerate       |
| 0.00-0.49 | Very poor | ❌ Use fallback     |

---

## 🛠️ Error Handling

**All errors return neutral scores (0.5)**:
```python
try:
    scores = evaluator.evaluate_single(...)
    if scores["faithfulness"] == 0.5:
        logger.warning("Evaluation failed - check inputs")
except:
    # Never crashes
    pass
```

**Common issues**:
- Empty contexts → 0.5
- None inputs → 0.5
- Mismatched batch lengths → 0.5

---

## 📋 Testing

```bash
# Quick validation
python backend/validate_ragas.py

# Full tests (11 tests, ~45 seconds)
pytest backend/test_ragas_evaluator.py -v

# Run examples
python backend/ragas_evaluator.py
```

---

## 📚 Full Documentation

- **Integration guide**: `backend/ragas_integration_guide.md` (600+ lines)
- **Implementation summary**: `RAGAS_IMPLEMENTATION_SUMMARY.md` (700+ lines)
- **README**: `RAGAS_README.md` (complete overview)

---

## 🔥 Common Patterns

### Pattern 1: Validate RAG Quality
```python
scores = evaluator.evaluate_single(question, answer, contexts)
if scores["faithfulness"] < 0.90 or scores["context_precision"] < 0.85:
    # Quality too low - take action
    logger.warning("Low quality RAG output")
    return fallback_answer()
```

### Pattern 2: Rank Products
```python
products_with_scores = []
for product in products:
    relevancy = evaluator.calculate_query_product_relevancy(
        query, product["name"], product["description"]
    )
    products_with_scores.append((product, relevancy))

# Sort by relevancy
products_with_scores.sort(key=lambda x: x[1], reverse=True)
```

### Pattern 3: Verify with Retries
```python
max_retries = 2
for attempt in range(max_retries + 1):
    answer = generate_answer(question, contexts)
    scores = evaluator.evaluate_single(question, answer, contexts)

    if scores["faithfulness"] >= 0.90:
        return answer  # Success

    logger.warning(f"Attempt {attempt+1} failed: {scores['faithfulness']:.3f}")

# All retries failed
return fallback_answer()
```

---

## ⚠️ Important Notes

1. **RAGAS is slow** (600-800ms per call) - uses LLM internally
2. **Always check for 0.5** - indicates evaluation failure
3. **Use batch evaluation** for multiple items (more efficient)
4. **Cache results** for identical questions
5. **Never crash** - error handling returns neutral scores

---

## 🎓 Key Concept

**RAGAS = "AI evaluating AI"**

RAGAS uses an LLM to judge the quality of another LLM's output. This is why:
- It's slow (~600ms) - makes 2-3 LLM API calls
- It's semantic - understands meaning, not just keywords
- It's subjective - scores are judgment calls, not exact

---

## ✅ Checklist

Before deploying:
- [ ] Install: `pip install -r backend/requirements_ragas.txt`
- [ ] Validate: `python backend/validate_ragas.py`
- [ ] Test: `pytest backend/test_ragas_evaluator.py -v`
- [ ] Try examples: `python backend/ragas_evaluator.py`
- [ ] Integrate into agents (see guide)
- [ ] Monitor scores in production logs

---

**Questions?** See full documentation in `backend/ragas_integration_guide.md`

**Status**: ✅ Production-Ready
