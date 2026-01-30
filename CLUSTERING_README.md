# K-Means Product Clustering

**Purpose**: Group PriceSense products into semantic clusters for Agent 2.5 alternative recommendations.

---

## Quick Start

### Prerequisites

- **Python 3.11 or 3.12** (required for clustering)
- Python 3.14 can be used for runtime services

### Option 1: Automated Setup (Windows)

```powershell
# Run the setup script
.\setup_py311_clustering.ps1

# This will:
# 1. Check for Python 3.11
# 2. Create .venv-py311 virtual environment
# 3. Install dependencies
# 4. Activate the environment

# Then run clustering
python backend/scripts/cluster_products.py
```

### Option 2: Manual Setup

#### Windows

```powershell
# Create Python 3.11 virtual environment
python3.11 -m venv .venv-py311

# Activate
.venv-py311\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install numpy scikit-learn torch torchvision pillow ftfy regex tqdm clip

# Run clustering
python backend/scripts/cluster_products.py

# When done, deactivate
deactivate

# Return to Python 3.14 environment
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
# Create Python 3.11 virtual environment
python3.11 -m venv .venv-py311

# Activate
source .venv-py311/bin/activate

# Install dependencies
pip install --upgrade pip
pip install numpy scikit-learn torch torchvision pillow ftfy regex tqdm clip

# Run clustering
python backend/scripts/cluster_products.py

# When done, deactivate
deactivate

# Return to Python 3.14 environment
source .venv/bin/activate
```

---

## What Gets Generated

After running `cluster_products.py`:

### 1. `backend/data/products_clustered.json`

**Size**: ~2-3 MB
**Format**: JSON array of products

Each product includes:
- All original fields (`product_id`, `name`, `price`, etc.)
- `embedding`: 512-dimensional CLIP vector
- `cluster_id`: Integer 0-9 indicating cluster membership

```json
{
  "product_id": "LAPTOP_BUDGET_001",
  "name": "Budget Laptop Basic 14\"",
  "price": 329.99,
  "cluster_id": 3,
  "embedding": [0.123, -0.456, ...]
}
```

### 2. `backend/data/cluster_analysis.txt`

**Human-readable cluster statistics**:
- Product count per cluster
- Average price per cluster
- Category distribution
- Top brands
- Sample products

### 3. `backend/data/cluster_centroids.npy` (Optional)

**NumPy array** of cluster centroids for future use.

---

## Expected Output

```
================================================================================
🎯 K-MEANS PRODUCT CLUSTERING
================================================================================

1️⃣ Generating sample products...
✅ Generated 80 products

2️⃣ Generating CLIP embeddings...
  Generated 20/80 embeddings
  Generated 40/80 embeddings
  Generated 60/80 embeddings
  Generated 80/80 embeddings
✅ All embeddings generated

3️⃣ Performing K-Means clustering...
  Embedding shape: (80, 512)
  Fitting K-Means model...
✅ Clustering complete
  Cluster distribution:
    Cluster 0: 12 products (15.0%)
    Cluster 1: 9 products (11.2%)
    ...
  K-Means inertia: 1247.32

4️⃣ Analyzing clusters...
[Detailed cluster analysis]

5️⃣ Saving outputs...
✅ Saved 80 products to backend/data/products_clustered.json
   File size: 2.45 MB
✅ Saved analysis to backend/data/cluster_analysis.txt

================================================================================
✅ CLUSTERING COMPLETE!
================================================================================
```

---

## How Agent 2.5 Uses Clusters

**Scenario**: User wants a $1,500 laptop but can only afford $800.

**Agent 2.5 Workflow**:
1. Detects unaffordable product (e.g., "Gaming Laptop RTX 3060" in Cluster 2)
2. Filters all products with `cluster_id == 2`
3. Sorts by price ascending
4. Recommends cheaper alternatives:
   - "Mid-range Developer Laptop" - $899
   - "Business Ultrabook" - $849

**Why clusters work**:
- Products in the same cluster are semantically similar (CLIP embeddings)
- Cheaper alternatives maintain feature relevance
- User gets comparable products within budget

---

## Cluster Configuration

**File**: `backend/scripts/cluster_products.py`

### Adjusting Cluster Count

```python
# Near top of file
DEFAULT_N_CLUSTERS = 10  # Change to 5, 15, 20, etc.
```

**Recommended values**:
- **5 clusters**: Broader categories (budget, mid, premium)
- **10 clusters**: Balanced granularity (default)
- **20 clusters**: Fine-grained similarity

**After changing**: Re-run `python backend/scripts/cluster_products.py`

### Product Data

**Currently**: 80 sample products across 9 categories

**To add more products**: Edit `generate_sample_products()` function

**To use real data**: Replace with database query or CSV import

---

## Troubleshooting

### "Cannot import sklearn"

**Problem**: Running on Python 3.14
**Solution**: Use Python 3.11/3.12 environment (see setup above)

### "CLIP model download slow"

**Expected**: First run downloads ~350MB CLIP model
**Location**: `~/.cache/clip/`
**Solution**: Wait for download to complete (one-time only)

### "Cluster file not found"

**Problem**: Clustering script hasn't been run
**Solution**: Run `python backend/scripts/cluster_products.py` in Python 3.11 environment

### "Module not found" errors

**Problem**: Dependencies not installed in Python 3.11 environment
**Solution**:
```bash
# Activate Python 3.11 environment first
.venv-py311\Scripts\Activate.ps1

# Install missing package
pip install <package-name>
```

---

## Why Python 3.11/3.12?

**Python 3.14 Limitation**: scipy (required by scikit-learn) has not yet released Python 3.14-compatible bindings.

**Impact**: K-Means clustering requires scikit-learn → scipy

**Solution**: Use Python 3.11/3.12 for **offline data preparation** only.

**Runtime services** (FastAPI, agents, LangGraph) remain on Python 3.14.

**See**: [docs/PYTHON_VERSION_COMPATIBILITY.md](../docs/PYTHON_VERSION_COMPATIBILITY.md)

---

## Next Steps

After clustering completes successfully:

1. ✅ Review `cluster_analysis.txt` to understand cluster characteristics
2. ✅ Use `products_clustered.json` in `populate_qdrant.py`
3. ✅ Return to Python 3.14 environment for runtime services
4. ✅ Test Agent 2.5 with clustered products

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ OFFLINE DATA PREPARATION (Python 3.11/3.12)                │
│                                                             │
│  cluster_products.py                                       │
│         ↓                                                   │
│  Generate CLIP embeddings (512-dim)                        │
│         ↓                                                   │
│  K-Means clustering (10 clusters)                          │
│         ↓                                                   │
│  products_clustered.json + cluster_analysis.txt            │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ (JSON files are version-agnostic)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ RUNTIME SERVICES (Python 3.14)                              │
│                                                             │
│  populate_qdrant.py → Load clustered products              │
│         ↓                                                   │
│  Qdrant Vector Database (with cluster_id)                  │
│         ↓                                                   │
│  Agent 2.5 → Query by cluster_id → Find alternatives       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Contract (Guaranteed Stable)

**Schema**:
```python
{
  "product_id": str,           # Unique identifier
  "name": str,                 # Product name
  "description": str,          # Product description
  "price": float,              # Price in USD
  "category": str,             # Category
  "subcategory": str,          # Subcategory
  "brand": str,                # Brand name
  "rating": float,             # Rating 0-5
  "num_reviews": int,          # Review count
  "in_stock": bool,            # Availability
  "financing_available": bool, # Financing option
  "embedding": list[float],    # 512-dim CLIP vector
  "cluster_id": int            # 0 to (n_clusters-1)
}
```

**Guarantees**:
- ✅ Every product has `cluster_id`
- ✅ Every product has 512-dim `embedding`
- ✅ `cluster_id` is deterministic (same input → same clusters)
- ✅ JSON is valid Python 3.14-compatible format

---

## References

- **Implementation**: [backend/scripts/cluster_products.py](../backend/scripts/cluster_products.py)
- **Compatibility Guide**: [docs/PYTHON_VERSION_COMPATIBILITY.md](../docs/PYTHON_VERSION_COMPATIBILITY.md)
- **Setup Script**: [setup_py311_clustering.ps1](../setup_py311_clustering.ps1)

---

**Last Updated**: January 29, 2026
