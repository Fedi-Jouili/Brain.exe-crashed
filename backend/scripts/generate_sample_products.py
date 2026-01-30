"""Generate sample products_clustered.json for testing"""
import json
import random

products = []
for i in range(80):
    products.append({
        "product_id": f"LAPTOP_{i:03d}",
        "name": f"Laptop Model {i}",
        "description": f"High performance laptop {i}",
        "price": round(500 + random.random() * 2000, 2),
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": ["Dell", "HP", "Lenovo", "ASUS"][i % 4],
        "rating": round(3.5 + random.random() * 1.5, 1),
        "num_reviews": random.randint(50, 500),
        "in_stock": True,
        "financing_available": True,
        "cluster_id": i % 10,
        "embedding": [random.gauss(0, 0.1) for _ in range(512)]
    })

with open('backend/data/products_clustered.json', 'w') as f:
    json.dump(products, f, indent=2)

print(f"Generated {len(products)} products with embeddings and cluster_ids")
