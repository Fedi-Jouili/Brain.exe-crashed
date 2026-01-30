# RAGAS Evaluator - Integration Guide

## 📋 Overview

This guide explains how to integrate the RAGAS evaluation module into your multi-agent RAG system. The module provides quality scoring for:

- **Agent 2**: Financial rule retrieval validation
- **Agent 3**: Query-product relevancy scoring
- **Agent 4**: Explanation faithfulness verification

## 🚀 Installation

### Requirements

```bash
pip install ragas>=0.1.0 datasets>=2.14.0
```

Or use the provided requirements file:

```bash
pip install -r requirements_ragas.txt
```

### Verify Installation

```python
from ragas_evaluator import RAGASEvaluator

evaluator = RAGASEvaluator()
print("✅ RAGAS evaluator ready!")
```

## ⚡ Quick Start

### Basic Usage (5 lines)

```python
from ragas_evaluator import RAGASEvaluator

evaluator = RAGASEvaluator()

scores = evaluator.evaluate_single(
    question="Why is this affordable?",
    answer="It's affordable because DTI is 38%, below the 43% threshold",
    contexts=["DTI should be below 43%", "Your DTI: 38%"]
)

print(scores)
# Output:
# {
#     'context_precision': 0.95,
#     'faithfulness': 0.92,
#     'answer_relevancy': 0.88
# }
```

### Expected Output

All scores are in **0.0-1.0 range** where:
- **0.0-0.5**: Poor quality
- **0.5-0.7**: Moderate quality
- **0.7-0.85**: Good quality
- **0.85-1.0**: Excellent quality

---

## 🤖 Integration into Agents

### Agent 2: Financial Analyzer (RAG Validation)

**Purpose**: Validate that retrieved financial rules are relevant and answers are faithful

**Where to integrate**: After RAG retrieval, before returning results

**Code to add**:

```python
# In Agent 2's execute() method

from ragas_evaluator import RAGASEvaluator

class Agent2FinancialAnalyzer(BaseTool):
    def __init__(self):
        super().__init__()
        self.ragas_evaluator = RAGASEvaluator()  # Initialize once

    def execute(self, state: AgentState) -> AgentState:
        # ... existing code ...

        # After RAG retrieval
        retrieved_contexts = [...]  # Your retrieved financial rules
        generated_answer = state.get("financial_analysis")
        question = f"Is this ${price} product affordable for ${income} income?"

        # RAGAS validation
        ragas_scores = self.ragas_evaluator.evaluate_single(
            question=question,
            answer=generated_answer,
            contexts=retrieved_contexts
        )

        # Log scores
        logger.info(f"RAGAS Scores: {ragas_scores}")

        # Validation thresholds
        if ragas_scores["faithfulness"] < 0.90:
            logger.warning("⚠️ Low faithfulness - potential hallucination detected")
            # Option 1: Flag for review
            state["quality_warning"] = "Low faithfulness score"
            # Option 2: Regenerate answer
            # generated_answer = self.regenerate_answer(...)

        if ragas_scores["context_precision"] < 0.85:
            logger.warning("⚠️ Low context precision - irrelevant retrieval")
            # Option: Retrieve additional contexts
            # retrieved_contexts = self.retrieve_more_contexts(...)

        # Store scores in state
        state["ragas_scores"] = ragas_scores

        return state
```

**Thresholds for Agent 2**:
| Metric              | Threshold | Action if Below                   |
| ------------------- | --------- | --------------------------------- |
| `faithfulness`      | > 0.90    | Regenerate answer or flag warning |
| `context_precision` | > 0.85    | Retrieve additional contexts      |
| `answer_relevancy`  | > 0.85    | Rephrase question or regenerate   |

---

### Agent 3: Recommender (Product Relevancy Scoring)

**Purpose**: Calculate how relevant each product is to the search query (20% of final score)

**Where to integrate**: In the re-ranking logic, alongside Thompson/Financial/Vector scores

**Code to add**:

```python
# In Agent 3's _calculate_composite_score() method

from ragas_evaluator import RAGASEvaluator

class Agent3Recommender(BaseTool):
    def __init__(self):
        super().__init__()
        self.ragas_evaluator = RAGASEvaluator()  # Initialize once

    def _calculate_composite_score(
        self,
        product: Dict,
        user_profile: UserProfile,
        query: str
    ) -> float:
        """
        Calculate composite score with 4 components:
        - Thompson Sampling: 40%
        - Financial Affordability: 20%
        - RAGAS Relevancy: 20% (NEW!)
        - Vector Similarity: 20%
        """

        # Existing scores (normalize to 0.0-1.0)
        thompson_score = self._get_thompson_score(product["id"])
        financial_score = self._get_financial_score(product, user_profile)
        vector_score = self._get_vector_similarity(product, query)

        # NEW: RAGAS Relevancy Score
        ragas_relevancy_raw = self.ragas_evaluator.calculate_query_product_relevancy(
            query=query,
            product_name=product["name"],
            product_description=product.get("description", "")
        )

        # Normalize from 0-100 to 0.0-1.0
        ragas_relevancy_normalized = ragas_relevancy_raw / 100.0

        # Composite score (weighted sum)
        composite_score = (
            0.40 * thompson_score +
            0.20 * financial_score +
            0.20 * ragas_relevancy_normalized +  # NEW!
            0.20 * vector_score
        )

        # Log for debugging
        logger.debug(
            f"Product {product['id']}: "
            f"Thompson={thompson_score:.3f} "
            f"Financial={financial_score:.3f} "
            f"RAGAS={ragas_relevancy_normalized:.3f} "
            f"Vector={vector_score:.3f} "
            f"→ Composite={composite_score:.3f}"
        )

        return composite_score
```

**Alternative: Batch Processing (Faster)**

If re-ranking 10+ products, use batch evaluation:

```python
def _calculate_all_ragas_scores(self, products: List[Dict], query: str) -> Dict[str, float]:
    """Calculate RAGAS scores for all products at once (more efficient)"""

    questions = [query] * len(products)  # Same query repeated
    answers = [
        f"{p['name']}: {p.get('description', '')}"
        for p in products
    ]
    contexts_list = [
        [f"{p['name']}: {p.get('description', '')}"]
        for p in products
    ]

    # Batch evaluation (faster than loop)
    avg_scores = self.ragas_evaluator.evaluate_batch(
        questions, answers, contexts_list
    )

    # Note: This returns AVERAGE scores, not per-product
    # For per-product, still use loop with calculate_query_product_relevancy()

    return avg_scores
```

**Weighting Rationale**:
| Component               | Weight  | Justification                             |
| ----------------------- | ------- | ----------------------------------------- |
| Thompson Sampling       | 40%     | Reinforcement learning from user behavior |
| Financial Affordability | 20%     | User can't buy unaffordable products      |
| **RAGAS Relevancy**     | **20%** | **Semantic match to search intent**       |
| Vector Similarity       | 20%     | Embedding-based similarity                |

---

### Agent 4: Explainer (Explanation Verification)

**Purpose**: Verify Gemini-generated explanations are faithful to context (no hallucinations)

**Where to integrate**: After LLM generation, before returning explanation

**Code to add**:

```python
# In Agent 4's execute() method

from ragas_evaluator import RAGASEvaluator

class Agent4Explainer(BaseTool):
    def __init__(self):
        super().__init__()
        self.ragas_evaluator = RAGASEvaluator()  # Initialize once
        self.max_regeneration_attempts = 2

    def execute(self, state: AgentState) -> AgentState:
        # ... existing code ...

        # Get context and question
        question = "Why is this product recommended?"
        contexts = self._build_privacy_safe_context(state)

        # Generate explanation with Gemini
        for attempt in range(self.max_regeneration_attempts + 1):
            explanation = self._generate_with_gemini(question, contexts)

            # RAGAS verification
            ragas_scores = self.ragas_evaluator.evaluate_single(
                question=question,
                answer=explanation,
                contexts=contexts
            )

            logger.info(f"Explanation attempt {attempt+1}: {ragas_scores}")

            # Check faithfulness threshold
            if ragas_scores["faithfulness"] >= 0.90:
                logger.info("✅ Explanation faithful to context")

                # Calculate trust score (existing logic)
                trust_score = self._calculate_trust_score(explanation, state)

                # Store RAGAS scores
                state["ragas_scores"] = ragas_scores
                state["explanation"] = explanation
                state["trust_score"] = trust_score

                return state
            else:
                logger.warning(
                    f"⚠️ Attempt {attempt+1}: Low faithfulness "
                    f"({ragas_scores['faithfulness']:.3f} < 0.90)"
                )

                if attempt < self.max_regeneration_attempts:
                    logger.info("Regenerating explanation...")
                    # Add more explicit instructions to prompt
                    contexts.append("IMPORTANT: Only use information from the context above")

        # All attempts failed - use fallback
        logger.error("❌ All regeneration attempts failed - using fallback")
        state["explanation"] = self._generate_fallback_explanation(state)
        state["trust_score"] = 0.85  # Fallback trust
        state["ragas_scores"] = {"faithfulness": 0.5}  # Neutral

        return state
```

**Verification Flow**:

```
1. Generate explanation with Gemini
2. Evaluate faithfulness with RAGAS
3. If faithfulness < 0.90:
   → Regenerate with stronger prompt (max 2 retries)
4. If all attempts fail:
   → Use rule-based fallback
5. Store RAGAS scores in state
```

**Thresholds for Agent 4**:
| Metric             | Threshold | Action if Below             |
| ------------------ | --------- | --------------------------- |
| `faithfulness`     | > 0.90    | Regenerate (max 2 attempts) |
| `answer_relevancy` | > 0.85    | Rephrase prompt             |

---

## 📊 Performance Notes

### Execution Times

| Operation             | Time (Typical) | Time (Range) |
| --------------------- | -------------- | ------------ |
| Single evaluation     | 600-800ms      | 500-1200ms   |
| Batch (10 items)      | 5-7 seconds    | 4-10 seconds |
| Module import         | <2 seconds     | 1-3 seconds  |
| Relevancy calculation | 600-800ms      | 500-1200ms   |

**Why so slow?** RAGAS uses an LLM internally to judge quality. Each evaluation makes 2-3 LLM API calls behind the scenes.

### Optimization Tips

1. **Use batch evaluation when possible**:
   ```python
   # ❌ Slow (3 LLM calls)
   for item in items:
       evaluator.evaluate_single(...)

   # ✅ Faster (1 batched LLM call)
   evaluator.evaluate_batch(questions, answers, contexts_list)
   ```

2. **Cache results**:
   ```python
   # Cache RAGAS scores for identical questions
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def get_cached_ragas_score(question, answer, contexts_tuple):
       return evaluator.evaluate_single(question, answer, list(contexts_tuple))
   ```

3. **Async evaluation** (if needed):
   ```python
   import asyncio

   async def evaluate_async(evaluator, question, answer, contexts):
       loop = asyncio.get_event_loop()
       return await loop.run_in_executor(
           None, evaluator.evaluate_single, question, answer, contexts
       )
   ```

### Expected Latency for 10 Products

| Approach                 | Time         | Recommendation                     |
| ------------------------ | ------------ | ---------------------------------- |
| Sequential (10 × single) | ~6-8 seconds | ❌ Too slow for production          |
| Batch (1 call)           | ~5-7 seconds | ⚠️ Acceptable for offline ranking   |
| Per-product relevancy    | ~6-8 seconds | ✅ Best for Agent 3 (most accurate) |

**Production Strategy**:
- Use `calculate_query_product_relevancy()` for Agent 3 (per-product scores)
- Pre-compute and cache scores for popular queries
- Consider async processing for large product catalogs

---

## 🎯 Metric Thresholds

### Production Thresholds (from architecture)

| Metric              | Threshold  | Interpretation                               |
| ------------------- | ---------- | -------------------------------------------- |
| `context_precision` | **> 0.85** | Retrieved docs are relevant to question      |
| `faithfulness`      | **> 0.90** | Answer sticks to context (no hallucinations) |
| `answer_relevancy`  | **> 0.85** | Answer addresses the question                |
| `context_recall`    | **> 0.80** | All necessary info was retrieved             |

### Score Interpretation Guide

| Score Range | Quality   | Agent Action                  |
| ----------- | --------- | ----------------------------- |
| 0.90 - 1.00 | Excellent | ✅ Accept as-is                |
| 0.85 - 0.89 | Good      | ✅ Accept (log for monitoring) |
| 0.70 - 0.84 | Moderate  | ⚠️ Flag for review             |
| 0.50 - 0.69 | Poor      | ❌ Regenerate or use fallback  |
| 0.00 - 0.49 | Very Poor | ❌ Fail gracefully (fallback)  |

### Agent-Specific Thresholds

**Agent 2 (Financial)** - Strictest thresholds (financial accuracy critical):
- Faithfulness: **> 0.90** (no tolerance for financial hallucinations)
- Context Precision: **> 0.85** (must retrieve relevant rules)

**Agent 3 (Recommender)** - Moderate thresholds (relevancy scoring):
- Relevancy (0-100): **> 50** = relevant, **> 70** = highly relevant

**Agent 4 (Explainer)** - Strict thresholds (user-facing explanations):
- Faithfulness: **> 0.90** (regenerate if lower)
- Answer Relevancy: **> 0.85** (must address user question)

---

## 🔧 Troubleshooting

### Issue 1: `ImportError: No module named 'ragas'`

**Solution**:
```bash
pip install ragas datasets
```

If still failing:
```bash
pip install --upgrade ragas datasets
python -c "from ragas_evaluator import RAGASEvaluator; print('✅ Import successful')"
```

---

### Issue 2: Evaluation returns all 0.5 scores

**Cause**: Error during evaluation (check logs for details)

**Common reasons**:
1. Empty contexts list
2. Invalid input types (e.g., contexts not a list)
3. RAGAS internal LLM API failure

**Solution**:
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check inputs
assert isinstance(contexts, list), "contexts must be a list"
assert len(contexts) > 0, "contexts cannot be empty"
assert all(isinstance(c, str) for c in contexts), "contexts must contain strings"
```

---

### Issue 3: Evaluation takes too long (>10 seconds per call)

**Cause**: RAGAS uses an LLM internally, which can be slow

**Solutions**:

1. **Use batch evaluation**:
   ```python
   # Instead of loop
   scores = evaluator.evaluate_batch(questions, answers, contexts_list)
   ```

2. **Cache results**:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def cached_eval(q, a, c_tuple):
       return evaluator.evaluate_single(q, a, list(c_tuple))
   ```

3. **Reduce context length**:
   ```python
   # Limit to 3-5 most relevant contexts
   contexts = contexts[:5]
   ```

---

### Issue 4: Scores seem inaccurate

**Cause**: RAGAS uses an LLM to judge quality, which can be subjective

**Validation**:

1. **Test with known examples**:
   ```python
   # Correct answer (should score high)
   scores1 = evaluator.evaluate_single(
       "What is 2+2?",
       "4",
       ["2+2 equals 4"]
   )
   assert scores1["faithfulness"] > 0.85

   # Hallucinated answer (should score low)
   scores2 = evaluator.evaluate_single(
       "What is 2+2?",
       "5, according to Orwell's 1984",
       ["2+2 equals 4"]
   )
   assert scores2["faithfulness"] < scores1["faithfulness"]
   ```

2. **Check context quality**:
   ```python
   # RAGAS quality depends on context relevance
   # Bad context → bad scores
   ```

3. **Use multiple metrics**:
   ```python
   # Don't rely on one metric alone
   if (scores["faithfulness"] > 0.9 and
       scores["answer_relevancy"] > 0.85):
       print("✅ High quality answer")
   ```

---

### Issue 5: Memory usage increases over time

**Cause**: RAGAS may cache models internally

**Solution**:
```python
# Reinitialize evaluator periodically (e.g., every 1000 evaluations)
if evaluation_count % 1000 == 0:
    evaluator = RAGASEvaluator()
    import gc
    gc.collect()
```

---

## 📚 Additional Examples

### Example 1: Validate Retrieval Quality

```python
evaluator = RAGASEvaluator()

question = "What are affordable laptops?"
retrieved_docs = [
    "Laptops under $500: Chromebook, basic Windows laptops",
    "High-end laptops: MacBook Pro, Dell XPS 15",
    "Gaming laptops: ASUS ROG, MSI Gaming"
]
answer = "Affordable laptops include Chromebooks and basic Windows laptops under $500"

scores = evaluator.evaluate_single(question, answer, retrieved_docs)

print(f"Context Precision: {scores['context_precision']:.3f}")
# High score = retrieved docs are relevant to "affordable"
```

### Example 2: Compare Two Explanations

```python
evaluator = RAGASEvaluator()

question = "Why is this laptop recommended?"
contexts = ["Your budget is $800", "This laptop costs $750"]

# Explanation A (faithful)
scores_a = evaluator.evaluate_single(
    question,
    "This laptop is recommended because it costs $750, within your $800 budget",
    contexts
)

# Explanation B (hallucinated)
scores_b = evaluator.evaluate_single(
    question,
    "This laptop is recommended because it has excellent reviews and was awarded Best Laptop 2024",
    contexts
)

print(f"Faithful: {scores_a['faithfulness']:.3f}")
print(f"Hallucinated: {scores_b['faithfulness']:.3f}")
# Faithful should score higher
```

### Example 3: Monitor Over Time

```python
import time

evaluator = RAGASEvaluator()
history = []

for i in range(10):
    scores = evaluator.evaluate_single(...)
    history.append({
        "timestamp": time.time(),
        "scores": scores
    })

# Calculate average faithfulness
avg_faithfulness = sum(h["scores"]["faithfulness"] for h in history) / len(history)
print(f"Average faithfulness: {avg_faithfulness:.3f}")

# Alert if below threshold
if avg_faithfulness < 0.85:
    print("⚠️ Quality degradation detected!")
```

---

## 🎓 Best Practices

1. **Always handle errors gracefully**:
   ```python
   scores = evaluator.evaluate_single(...)
   if scores.get("faithfulness", 0) == 0.5:
       logger.warning("RAGAS evaluation failed - using fallback")
   ```

2. **Log all evaluations**:
   ```python
   logger.info(f"RAGAS: {scores} | Question: {question[:50]}")
   ```

3. **Use thresholds consistently**:
   ```python
   # Define once
   FAITHFULNESS_THRESHOLD = 0.90
   RELEVANCY_THRESHOLD = 0.85

   # Use everywhere
   if scores["faithfulness"] < FAITHFULNESS_THRESHOLD:
       regenerate()
   ```

4. **Monitor performance**:
   ```python
   import time
   start = time.time()
   scores = evaluator.evaluate_single(...)
   duration = time.time() - start
   logger.info(f"RAGAS took {duration:.2f}s")
   ```

5. **Test thoroughly**:
   ```bash
   pytest test_ragas_evaluator.py -v
   ```

---

## 🚀 Ready to Integrate?

1. ✅ Install dependencies: `pip install -r requirements_ragas.txt`
2. ✅ Run tests: `pytest test_ragas_evaluator.py -v`
3. ✅ Try examples: `python ragas_evaluator.py`
4. ✅ Integrate into Agent 2, 3, or 4 using code above
5. ✅ Monitor scores in production logs

**Questions?** Check the code comments in `ragas_evaluator.py` for detailed implementation notes.
