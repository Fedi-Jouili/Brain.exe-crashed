# K-Means Clustering - Pre-Flight Checklist

**Use this checklist before running clustering and after completion to verify success.**

---

## ✅ Pre-Execution Checklist

Before running `cluster_products.py`:

### Environment Setup

- [ ] Python 3.11 or 3.12 installed on system
- [ ] Virtual environment `.venv-py311` created
- [ ] Virtual environment activated
- [ ] Dependencies installed (numpy, scikit-learn, torch, clip)

**Verify**:
```bash
# Check Python version
python --version  # Should show 3.11.x or 3.12.x

# Check scikit-learn import
python -c "from sklearn.cluster import KMeans; print('✅ OK')"
```

### File Structure

- [ ] `backend/scripts/cluster_products.py` exists
- [ ] `backend/core/embeddings.py` exists (for CLIP)
- [ ] `backend/data/` directory exists (created automatically if missing)

---

## 🎯 During Execution

Watch for these stages:

### Stage 1: Product Generation
```
1️⃣ Generating sample products...
✅ Generated 80 products
```
**Expected**: 80 products across 9 categories

### Stage 2: CLIP Embeddings
```
2️⃣ Generating CLIP embeddings...
  Generated 20/80 embeddings
  Generated 40/80 embeddings
  Generated 60/80 embeddings
  Generated 80/80 embeddings
✅ All embeddings generated
```
**Duration**: 2-5 minutes (first run downloads CLIP model)

### Stage 3: K-Means Clustering
```
3️⃣ Performing K-Means clustering...
  Embedding shape: (80, 512)
  Fitting K-Means model...
✅ Clustering complete
  Cluster distribution:
    Cluster 0: X products (X.X%)
    ...
    Cluster 9: X products (X.X%)
```
**Expected**: 10 clusters with varied distribution

### Stage 4: Analysis
```
4️⃣ Analyzing clusters...
[Detailed cluster statistics]
```
**Expected**: Price ranges, category distributions per cluster

### Stage 5: Saving Outputs
```
5️⃣ Saving outputs...
✅ Saved 80 products to backend/data/products_clustered.json
   File size: ~2.45 MB
✅ Saved analysis to backend/data/cluster_analysis.txt
```

---

## ✅ Post-Execution Verification

After clustering completes:

### File Verification

- [ ] `backend/data/products_clustered.json` exists
- [ ] `backend/data/cluster_analysis.txt` exists
- [ ] `backend/data/cluster_centroids.npy` exists (optional)

**Check file sizes**:
```powershell
Get-ChildItem backend/data/products_clustered.json | Select-Object Name, Length
# Expected: ~2-3 MB
```

### Data Integrity Checks

Run these verification commands:

#### 1. Check JSON is valid
```bash
python -c "import json; data=json.load(open('backend/data/products_clustered.json')); print(f'✅ {len(data)} products loaded')"
```
**Expected**: `✅ 80 products loaded`

#### 2. Verify cluster_id field exists
```bash
python -c "import json; data=json.load(open('backend/data/products_clustered.json')); print('✅ All have cluster_id') if all('cluster_id' in p for p in data) else print('❌ Missing cluster_id')"
```
**Expected**: `✅ All have cluster_id`

#### 3. Verify cluster_id range
```bash
python -c "import json; data=json.load(open('backend/data/products_clustered.json')); ids=set(p['cluster_id'] for p in data); print(f'✅ Clusters: {sorted(ids)}')"
```
**Expected**: `✅ Clusters: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`

#### 4. Verify embeddings are 512-dimensional
```bash
python -c "import json; data=json.load(open('backend/data/products_clustered.json')); print(f'✅ Embedding dimension: {len(data[0][\"embedding\"])}')"
```
**Expected**: `✅ Embedding dimension: 512`

#### 5. Check cluster distribution
```bash
python -c "import json; from collections import Counter; data=json.load(open('backend/data/products_clustered.json')); counts=Counter(p['cluster_id'] for p in data); print('✅ Distribution:'); [print(f'  Cluster {k}: {v} products') for k,v in sorted(counts.items())]"
```
**Expected**: Distribution across 10 clusters

### Schema Validation

- [ ] All products have `product_id`
- [ ] All products have `name`
- [ ] All products have `price`
- [ ] All products have `embedding` (512 floats)
- [ ] All products have `cluster_id` (0-9)

**Complete schema check**:
```bash
python -c "
import json
data = json.load(open('backend/data/products_clustered.json'))
required = ['product_id', 'name', 'price', 'embedding', 'cluster_id']
sample = data[0]
print('Schema Check:')
for field in required:
    has_field = field in sample
    print(f'  {field}: {\"✅\" if has_field else \"❌\"}'
)
if field == 'embedding':
    print(f'    → Dimension: {len(sample[field])}')
if field == 'cluster_id':
    print(f'    → Value: {sample[field]} (type: {type(sample[field]).__name__})')
"
```

---

## ✅ Agent 2.5 Integration Verification

Test that clustered data works with Agent 2.5 workflow:

### Cluster Query Test

```python
# Test finding alternatives in same cluster
import json

# Load clustered products
products = json.load(open('backend/data/products_clustered.json'))

# Find a product
target = products[0]
print(f"Target Product: {target['name']}")
print(f"Price: ${target['price']}")
print(f"Cluster ID: {target['cluster_id']}")

# Find alternatives in same cluster
same_cluster = [
    p for p in products
    if p['cluster_id'] == target['cluster_id']
    and p['product_id'] != target['product_id']
]

# Sort by price
same_cluster.sort(key=lambda p: p['price'])

print(f"\nAlternatives in Cluster {target['cluster_id']}:")
for alt in same_cluster[:5]:
    print(f"  - {alt['name']}: ${alt['price']}")
```

**Expected**: List of similar products from same cluster

---

## ✅ Qdrant Population Readiness

Before loading into Qdrant:

- [ ] `products_clustered.json` validated
- [ ] Cluster IDs are integers 0-9
- [ ] Embeddings are 512-dimensional floats
- [ ] No missing or null values in required fields

**Qdrant ingestion test** (if Qdrant is running):
```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import json

client = QdrantClient("localhost", port=6333)

# Test collection creation
client.recreate_collection(
    collection_name="products_test",
    vectors_config=VectorParams(size=512, distance=Distance.COSINE)
)

# Load one product
products = json.load(open('backend/data/products_clustered.json'))
product = products[0]

# Test upload
client.upsert(
    collection_name="products_test",
    points=[{
        "id": 1,
        "vector": product['embedding'],
        "payload": {
            "product_id": product['product_id'],
            "cluster_id": product['cluster_id'],
            "name": product['name'],
            "price": product['price']
        }
    }]
)

print("✅ Qdrant ingestion test passed")
```

---

## 🔄 Return to Python 3.14 Environment

After verification:

```powershell
# Deactivate Python 3.11 environment
deactivate

# Activate Python 3.14 runtime environment
.\.venv\Scripts\Activate.ps1

# Verify Python version
python --version  # Should show 3.14.x
```

---

## ❌ Common Issues

### Issue: "KeyboardInterrupt in scipy"
**Cause**: Running on Python 3.14
**Fix**: Activate `.venv-py311` environment

### Issue: "Cannot import sklearn"
**Cause**: Dependencies not installed
**Fix**: `pip install scikit-learn numpy`

### Issue: "CLIP model not found"
**Cause**: First run downloads model
**Fix**: Wait for download (one-time, ~350MB)

### Issue: "File size 0 KB"
**Cause**: Script failed silently
**Fix**: Check terminal output for errors

### Issue: "Cluster IDs all same value"
**Cause**: Invalid embeddings
**Fix**: Regenerate embeddings, check CLIP model

---

## 📊 Success Metrics

After completing ALL checklists above:

- [x] 80 products clustered into 10 groups
- [x] Each product has valid `cluster_id` (0-9)
- [x] Each product has 512-dim `embedding`
- [x] Cluster distribution is balanced (5-15 products per cluster)
- [x] Analysis file generated with cluster statistics
- [x] Files ready for Qdrant population
- [x] Agent 2.5 can query by `cluster_id`
- [x] Returned to Python 3.14 environment for runtime

---

## 🎯 Final Validation

**Complete success checklist**:

```bash
# In project root directory
# Verify files exist
test -f backend/data/products_clustered.json && echo "✅ Clustered products" || echo "❌ Missing"
test -f backend/data/cluster_analysis.txt && echo "✅ Analysis file" || echo "❌ Missing"

# Verify JSON is valid
python -c "import json; data=json.load(open('backend/data/products_clustered.json')); print(f'✅ {len(data)} products')" 2>/dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# Verify schema
python -c "import json; data=json.load(open('backend/data/products_clustered.json')); assert all('cluster_id' in p for p in data); print('✅ Schema valid')" 2>/dev/null || echo "❌ Invalid schema"

# All checks passed
echo ""
echo "================================================================================"
echo "  ✅ CLUSTERING VERIFICATION COMPLETE"
echo "================================================================================"
```

---

**If all checks pass**: Proceed to populate Qdrant and test Agent 2.5!

**If any checks fail**: Review error messages and re-run clustering script.

**Documentation**: See [CLUSTERING_README.md](../CLUSTERING_README.md) and [docs/PYTHON_VERSION_COMPATIBILITY.md](../docs/PYTHON_VERSION_COMPATIBILITY.md)

---

**Last Updated**: January 29, 2026
