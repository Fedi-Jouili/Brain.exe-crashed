# Python Version Compatibility

**Last Updated**: January 29, 2026

---

## ⚠️ Known Limitation (Python 3.14)

The following components are **NOT compatible with Python 3.14** as of this date:

- **scipy** - Scientific computing library
- **scikit-learn** - Machine learning library (depends on scipy)

### Root Cause

**scipy HiGHS optimization bindings** are not yet released for Python 3.14.

Error manifests as:
```python
KeyboardInterrupt in scipy.optimize._highspy._highs_wrapper.py
```

This is an **upstream blocker** in scipy's optimization module, not a PriceSense issue.

---

## 🎯 Impacted Scripts

The following scripts require **Python 3.11 or 3.12**:

| Script                                | Purpose                    | Dependency           | Workaround                   |
| ------------------------------------- | -------------------------- | -------------------- | ---------------------------- |
| `backend/scripts/cluster_products.py` | K-Means product clustering | scikit-learn → scipy | Run in Python 3.11/3.12 venv |

---

## ✅ Workaround (Approved Solution)

### Offline ML Preprocessing

Run clustering and other offline ML preprocessing using **Python 3.11 or Python 3.12**.

Generated artifacts (JSON, embeddings, cluster_id) are **runtime-agnostic** and can be used by Python 3.14 services.

### Step-by-Step Instructions

#### Windows

```powershell
# 1. Create Python 3.11 virtual environment (one-time setup)
python3.11 -m venv .venv-py311

# 2. Activate the environment
.venv-py311\Scripts\Activate.ps1

# 3. Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# 4. Run clustering
python backend/scripts/cluster_products.py

# 5. Deactivate when done
deactivate

# 6. Return to Python 3.14 environment for runtime services
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
# 1. Create Python 3.11 virtual environment (one-time setup)
python3.11 -m venv .venv-py311

# 2. Activate the environment
source .venv-py311/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# 4. Run clustering
python backend/scripts/cluster_products.py

# 5. Deactivate when done
deactivate

# 6. Return to Python 3.14 environment for runtime services
source .venv/bin/activate
```

---

## 🔒 Runtime Safety

The following components **remain fully compatible with Python 3.14**:

- ✅ FastAPI REST API (`backend/main.py`)
- ✅ All 5 agents (Agent1-4, Agent2.5)
- ✅ LangGraph workflow orchestration
- ✅ Gemini LLM integration
- ✅ CLIP embeddings (runtime inference)
- ✅ Qdrant vector database
- ✅ Redis caching
- ✅ Thompson Sampling

**Key Principle**: Clustering is **offline data preparation**, not runtime execution.

---

## 📊 Output Contract (Guaranteed Stable)

### Clustering Output Format

After running `cluster_products.py` with Python 3.11/3.12, the following files are generated:

#### `backend/data/products_clustered.json`

```json
[
  {
    "product_id": "LAPTOP_BUDGET_001",
    "name": "Budget Laptop Basic 14\"",
    "description": "Affordable laptop with Intel Celeron, 4GB RAM, 128GB SSD for basic tasks",
    "price": 329.99,
    "category": "Electronics",
    "subcategory": "Laptops",
    "brand": "Acer",
    "rating": 3.8,
    "num_reviews": 80,
    "in_stock": true,
    "financing_available": true,
    "embedding": [0.123, -0.456, ...],  // 512-dimensional CLIP vector
    "cluster_id": 3                      // Integer 0-9
  },
  // ... more products
]
```

**Schema Guarantees**:
- Every product has `cluster_id` ∈ [0, 9]
- Every product has `embedding` (512-dimensional array)
- All original product fields preserved
- JSON is valid and parseable by Python 3.14

#### `backend/data/cluster_analysis.txt`

Human-readable cluster statistics:
- Product count per cluster
- Average price per cluster
- Category distribution
- Sample products

#### `backend/data/cluster_centroids.npy` (Optional)

NumPy array of cluster centroids for future incremental clustering.

---

## 🔗 Agent 2.5 (Pathfinder) Integration Contract

### Cluster Usage Rules (MUST REMAIN STABLE)

**What `cluster_id` Represents**:
- Semantic similarity based on CLIP embeddings
- Products with the same `cluster_id` are considered **comparable alternatives**

**Agent 2.5 SHOULD**:
1. Detect unaffordable product
2. Filter products with the **same `cluster_id`**
3. Sort alternatives by price (ascending)
4. Recommend cheaper options **within the same cluster**

**Agent 2.5 MUST NOT**:
- Compare products across different clusters
- Ignore `cluster_id` when suggesting alternatives
- Assume `cluster_id` correlates with price

**Determinism**:
- K-Means uses `random_state=42` for reproducibility
- Same input → same cluster assignments
- Agent 2.5 can rely on stable cluster groupings

---

## 🛠️ Troubleshooting

### "Cannot import sklearn" on Python 3.14

**Expected**: This is the known limitation.

**Solution**: Use Python 3.11 or 3.12 virtual environment (see workaround above).

### "Cluster file not found"

**Cause**: Clustering script hasn't been run yet.

**Solution**:
```bash
# Activate Python 3.11 environment
.venv-py311\Scripts\Activate.ps1  # Windows
source .venv-py311/bin/activate   # Linux/macOS

# Run clustering
python backend/scripts/cluster_products.py
```

### "ModuleNotFoundError: No module named 'sklearn'"

**Cause**: Dependencies not installed in Python 3.11 environment.

**Solution**:
```bash
# In Python 3.11 environment
pip install scikit-learn numpy
```

---

## 📋 Pre-Flight Checklist

Before running runtime services (Python 3.14):

- [ ] Python 3.11/3.12 virtual environment created
- [ ] `cluster_products.py` executed successfully
- [ ] `backend/data/products_clustered.json` exists
- [ ] File contains products with `cluster_id` field
- [ ] `cluster_analysis.txt` generated for review
- [ ] Python 3.14 environment activated for runtime

---

## 🔮 Future Outlook

### When Python 3.14 Support Arrives

Once scipy releases Python 3.14-compatible bindings:

1. Update scipy: `pip install --upgrade scipy`
2. Verify: `python -c "from sklearn.cluster import KMeans; print('✅ OK')"`
3. Run clustering in Python 3.14 environment
4. Archive this workaround documentation

**Estimated Timeline**: Q2-Q3 2026 (based on typical scipy release cycles)

### Monitoring Upstream Progress

Track scipy Python 3.14 support:
- GitHub: https://github.com/scipy/scipy/issues
- PyPI: https://pypi.org/project/scipy/
- Changelog: https://docs.scipy.org/doc/scipy/release.html

---

## 📚 Related Documentation

- [API_STATUS.md](../API_STATUS.md) - FastAPI implementation status
- [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) - Development setup
- [cluster_products.py](../backend/scripts/cluster_products.py) - Clustering script
- [cluster_analysis.txt](../backend/data/cluster_analysis.txt) - Generated cluster stats (after running)

---

## ✅ Summary

| Component             | Python 3.14 Compatible?   | Notes                           |
| --------------------- | ------------------------- | ------------------------------- |
| **Data Preparation**  | ❌ No (requires 3.11/3.12) | One-time offline execution      |
| **Runtime API**       | ✅ Yes                     | FastAPI, agents, LangGraph      |
| **Clustering Output** | ✅ Yes (consumable)        | JSON files are version-agnostic |
| **Agent 2.5 Logic**   | ✅ Yes                     | Reads `cluster_id` at runtime   |

**Bottom Line**: Use Python 3.11/3.12 for clustering, Python 3.14 for everything else.
