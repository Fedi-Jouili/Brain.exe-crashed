"""
K-Means Product Clustering for PriceSense
Groups products by CLIP embedding similarity

Run: python backend/scripts/cluster_products.py

Output:
- products_clustered.json (products with cluster_id assigned)
- cluster_analysis.txt (cluster statistics)

Usage:
1. Run this script to cluster products
2. Use output in populate_qdrant.py

NOTE:
This script is intended for OFFLINE DATA PREPARATION.
It must be executed with Python 3.11 or 3.12 due to scipy limitations.
Runtime services are unaffected.

See docs/PYTHON_VERSION_COMPATIBILITY.md for details.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.embeddings import MultimodalEmbedder
import numpy as np
from sklearn.cluster import KMeans
import json
import logging
from typing import List, Dict, Any
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_N_CLUSTERS = 10

# Initialize CLIP embedder
logger.info("Initializing CLIP embedder...")
clip_embedder = MultimodalEmbedder(model_name="ViT-B/32")
logger.info("✅ CLIP embedder initialized")

# Output file paths
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "products_clustered.json"
OUTPUT_FILE.parent.mkdir(exist_ok=True)


# ============================================================================
# PRODUCT GENERATION (Sample Data)
# ============================================================================

def generate_sample_products() -> List[Dict[str, Any]]:
    """
    Generate diverse sample electronics products

    Returns 80-100 products across categories:
    - Laptops (budget, mid-range, gaming, premium)
    - Accessories (mice, keyboards, headphones)
    - Monitors
    - Tablets

    Returns:
        List of product dicts
    """
    products = []

    # ========================================================================
    # BUDGET LAPTOPS ($300-$600)
    # ========================================================================

    budget_laptops = [
        ("Budget Laptop Basic 14\"", "Affordable laptop with Intel Celeron, 4GB RAM, 128GB SSD for basic tasks", 329.99, "Acer"),
        ("Student Laptop Essential", "AMD Ryzen 3, 8GB RAM, 256GB SSD, perfect for students", 449.99, "HP"),
        ("Chromebook Plus", "MediaTek processor, 4GB RAM, 64GB storage, Chrome OS", 299.99, "ASUS"),
        ("Home Office Laptop", "Intel Pentium, 8GB RAM, 256GB SSD, Windows 11", 399.99, "Lenovo"),
        ("Everyday Laptop 15.6\"", "Intel Core i3, 8GB RAM, 256GB SSD, full HD display", 549.99, "Dell"),
    ]

    for i, (name, desc, price, brand) in enumerate(budget_laptops):
        products.append({
            "product_id": f"LAPTOP_BUDGET_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Laptops",
            "brand": brand,
            "rating": round(3.8 + (i * 0.1), 1),
            "num_reviews": 80 + (i * 30),
            "in_stock": True,
            "financing_available": True
        })

    # ========================================================================
    # MID-RANGE LAPTOPS ($700-$1200)
    # ========================================================================

    midrange_laptops = [
        ("Professional Laptop 15", "Intel Core i5-1135G7, 16GB RAM, 512GB SSD, business features", 899.99, "Dell"),
        ("Developer Laptop Pro", "AMD Ryzen 7 5700U, 32GB RAM, 1TB SSD, excellent for coding", 1199.99, "Lenovo"),
        ("Creator Laptop", "Intel Core i7-1165G7, 16GB RAM, 1TB SSD, color-accurate display", 1099.99, "HP"),
        ("Business Ultrabook", "AMD Ryzen 5 5500U, 16GB RAM, 512GB SSD, lightweight", 849.99, "ASUS"),
        ("All-Day Laptop", "Intel Core i7-1255U, 16GB RAM, 512GB SSD, 15-hour battery", 1049.99, "Dell"),
        ("Multimedia Laptop", "Intel Core i5-1235U, 16GB RAM, 512GB SSD, great speakers", 949.99, "HP"),
        ("2-in-1 Convertible", "Intel Core i5-1240P, 16GB RAM, 512GB SSD, touchscreen", 999.99, "Lenovo"),
        ("Thin & Light Pro", "AMD Ryzen 5 6600U, 16GB RAM, 512GB SSD, under 3 lbs", 899.99, "ASUS"),
    ]

    for i, (name, desc, price, brand) in enumerate(midrange_laptops):
        products.append({
            "product_id": f"LAPTOP_MID_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Laptops",
            "brand": brand,
            "rating": round(4.2 + (i * 0.05), 1),
            "num_reviews": 150 + (i * 40),
            "in_stock": True,
            "financing_available": True
        })

    # ========================================================================
    # GAMING LAPTOPS ($1200-$2500)
    # ========================================================================

    gaming_laptops = [
        ("Gaming Laptop RTX 3050", "Intel Core i5-11400H, RTX 3050, 16GB RAM, 512GB SSD, 144Hz display", 1299.99, "ASUS ROG"),
        ("Gaming Beast RTX 3060", "AMD Ryzen 7 5800H, RTX 3060, 16GB RAM, 1TB SSD, RGB keyboard", 1599.99, "MSI"),
        ("Pro Gaming RTX 3070", "Intel Core i7-12700H, RTX 3070, 32GB RAM, 1TB SSD, 165Hz", 1899.99, "Razer"),
        ("Ultimate Gaming RTX 3080", "AMD Ryzen 9 5900HX, RTX 3080, 32GB RAM, 2TB SSD, QHD 240Hz", 2399.99, "Alienware"),
        ("Esports Laptop 144Hz", "Intel Core i7-11800H, RTX 3060, 16GB RAM, 512GB SSD, fast response", 1499.99, "Acer Predator"),
        ("Streaming Laptop", "AMD Ryzen 7 6800H, RTX 3070, 32GB RAM, 1TB SSD, dual screen", 1799.99, "ASUS ROG"),
    ]

    for i, (name, desc, price, brand) in enumerate(gaming_laptops):
        products.append({
            "product_id": f"LAPTOP_GAMING_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Gaming Laptops",
            "brand": brand,
            "rating": round(4.5 + (i * 0.04), 1),
            "num_reviews": 200 + (i * 50),
            "in_stock": True,
            "financing_available": True
        })

    # ========================================================================
    # PREMIUM LAPTOPS ($2000-$3500)
    # ========================================================================

    premium_laptops = [
        ("MacBook Air M2", "Apple M2 chip, 16GB RAM, 512GB SSD, Liquid Retina display", 1499.99, "Apple"),
        ("MacBook Pro 14\" M2 Pro", "Apple M2 Pro, 32GB RAM, 1TB SSD, ProMotion XDR", 2499.99, "Apple"),
        ("Dell XPS 15 Plus", "Intel Core i7-12700H, 32GB RAM, 1TB SSD, 4K OLED", 2199.99, "Dell"),
        ("ThinkPad X1 Carbon Gen 11", "Intel Core i7-1365U, 32GB RAM, 1TB SSD, carbon fiber", 2099.99, "Lenovo"),
        ("Surface Laptop Studio", "Intel Core i7-11370H, 32GB RAM, 1TB SSD, 120Hz touchscreen", 2399.99, "Microsoft"),
    ]

    for i, (name, desc, price, brand) in enumerate(premium_laptops):
        products.append({
            "product_id": f"LAPTOP_PREMIUM_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Premium Laptops",
            "brand": brand,
            "rating": round(4.7 + (i * 0.02), 1),
            "num_reviews": 400 + (i * 80),
            "in_stock": True,
            "financing_available": True
        })

    # ========================================================================
    # ACCESSORIES - MICE ($20-$150)
    # ========================================================================

    mice = [
        ("Wireless Mouse Basic", "2.4GHz wireless, 1600 DPI, 12-month battery", 24.99, "Logitech"),
        ("Gaming Mouse RGB", "16000 DPI, programmable buttons, RGB lighting", 69.99, "Razer"),
        ("Ergonomic Mouse Vertical", "Vertical design, wireless, reduces wrist strain", 39.99, "Logitech"),
        ("Pro Gaming Mouse Wireless", "25600 DPI, wireless charging, ultra-lightweight 60g", 149.99, "Logitech G Pro"),
        ("Productivity Mouse MX Master", "Multi-device, silent clicks, 4000 DPI, USB-C charging", 99.99, "Logitech MX"),
    ]

    for i, (name, desc, price, brand) in enumerate(mice):
        products.append({
            "product_id": f"MOUSE_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Computer Accessories",
            "brand": brand,
            "rating": round(4.0 + (i * 0.15), 1),
            "num_reviews": 500 + (i * 200),
            "in_stock": True,
            "financing_available": False
        })

    # ========================================================================
    # ACCESSORIES - KEYBOARDS ($30-$200)
    # ========================================================================

    keyboards = [
        ("Wireless Keyboard Slim", "Bluetooth, rechargeable, scissor switches, quiet", 49.99, "Logitech"),
        ("Mechanical Keyboard RGB", "Cherry MX Red switches, per-key RGB, aluminum frame", 129.99, "Corsair"),
        ("Gaming Keyboard TKL", "Hot-swappable switches, 80% layout, PBT keycaps", 99.99, "Keychron"),
        ("Ergonomic Keyboard Split", "Split design, tenting, mechanical switches", 189.99, "Kinesis"),
        ("Budget Mechanical Keyboard", "Blue switches, white LED backlight, full-size", 59.99, "Redragon"),
    ]

    for i, (name, desc, price, brand) in enumerate(keyboards):
        products.append({
            "product_id": f"KEYBOARD_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Computer Accessories",
            "brand": brand,
            "rating": round(4.1 + (i * 0.12), 1),
            "num_reviews": 300 + (i * 150),
            "in_stock": True,
            "financing_available": False
        })

    # ========================================================================
    # ACCESSORIES - HEADPHONES ($50-$400)
    # ========================================================================

    headphones = [
        ("Wireless Headphones ANC", "Active noise cancelling, 30h battery, Bluetooth 5.0", 79.99, "Sony"),
        ("Gaming Headset 7.1", "Surround sound, detachable mic, RGB lighting", 99.99, "HyperX"),
        ("Premium ANC Headphones", "Industry-leading noise cancellation, 40h battery, LDAC", 349.99, "Sony WH-1000XM5"),
        ("Studio Headphones", "Flat frequency response, wired, professional monitoring", 149.99, "Audio-Technica"),
        ("True Wireless Earbuds Pro", "ANC, spatial audio, 6h battery, wireless charging", 249.99, "Apple AirPods Pro"),
    ]

    for i, (name, desc, price, brand) in enumerate(headphones):
        products.append({
            "product_id": f"HEADPHONES_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Audio",
            "brand": brand,
            "rating": round(4.3 + (i * 0.11), 1),
            "num_reviews": 800 + (i * 400),
            "in_stock": True,
            "financing_available": price > 100
        })

    # ========================================================================
    # MONITORS ($150-$800)
    # ========================================================================

    monitors = [
        ("24\" 1080p Monitor 75Hz", "IPS panel, FreeSync, HDMI + DisplayPort, VESA mount", 159.99, "ASUS"),
        ("27\" 1440p Monitor 144Hz", "IPS, G-Sync Compatible, HDR400, height adjustable", 349.99, "LG"),
        ("32\" 4K Monitor 60Hz", "IPS, USB-C, color accurate 99% sRGB, built-in speakers", 499.99, "Dell"),
        ("34\" Ultrawide 1440p 100Hz", "Curved VA panel, immersive, picture-by-picture", 449.99, "Samsung"),
        ("27\" Gaming Monitor 240Hz", "Fast IPS, 1ms response, G-Sync Ultimate, RGB", 599.99, "ASUS ROG"),
    ]

    for i, (name, desc, price, brand) in enumerate(monitors):
        products.append({
            "product_id": f"MONITOR_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Monitors",
            "brand": brand,
            "rating": round(4.2 + (i * 0.10), 1),
            "num_reviews": 200 + (i * 100),
            "in_stock": True,
            "financing_available": price > 300
        })

    # ========================================================================
    # TABLETS ($150-$1100)
    # ========================================================================

    tablets = [
        ("iPad 10.2\" 9th Gen", "A13 Bionic chip, 64GB, 10.2\" Retina display, iPadOS", 329.99, "Apple"),
        ("iPad Air 5th Gen", "M1 chip, 256GB, 10.9\" Liquid Retina, Apple Pencil support", 749.99, "Apple"),
        ("iPad Pro 11\" M2", "M2 chip, 512GB, 11\" ProMotion XDR display, Face ID", 1099.99, "Apple"),
        ("Galaxy Tab S8", "Snapdragon 8 Gen 1, 128GB, 11\" 120Hz AMOLED, S Pen included", 699.99, "Samsung"),
        ("Surface Pro 9", "Intel Core i5, 256GB, 13\" PixelSense touchscreen, Windows 11", 999.99, "Microsoft"),
        ("Fire HD 10", "MediaTek processor, 32GB, 10.1\" 1080p, Alexa built-in", 149.99, "Amazon"),
    ]

    for i, (name, desc, price, brand) in enumerate(tablets):
        products.append({
            "product_id": f"TABLET_{i+1:03d}",
            "name": name,
            "description": desc,
            "price": price,
            "category": "Electronics",
            "subcategory": "Tablets",
            "brand": brand,
            "rating": round(4.4 + (i * 0.08), 1),
            "num_reviews": 600 + (i * 300),
            "in_stock": True,
            "financing_available": price > 400
        })

    logger.info(f"Generated {len(products)} sample products")
    return products


# ============================================================================
# EMBEDDING GENERATION
# ============================================================================

def generate_embeddings(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate CLIP embeddings for all products

    Args:
        products: List of product dicts

    Returns:
        Products with 'embedding' field added (512-dim CLIP vector)
    """
    logger.info(f"Generating CLIP embeddings for {len(products)} products...")

    for i, product in enumerate(products):
        # Create rich text for embedding
        search_text = (
            f"{product['name']} "
            f"{product['description']} "
            f"{product['brand']} "
            f"{product['category']} "
            f"{product['subcategory']}"
        )

        # Generate 512-dim CLIP embedding using embed_text method
        embedding = clip_embedder.embed_text(search_text)
        product['embedding'] = embedding.tolist()  # Convert to list for JSON serialization

        # Progress logging
        if (i + 1) % 20 == 0 or (i + 1) == len(products):
            logger.info(f"  Generated {i + 1}/{len(products)} embeddings")

    logger.info("✅ All embeddings generated")
    return products


# ============================================================================
# K-MEANS CLUSTERING
# ============================================================================

def perform_clustering(
    products: List[Dict[str, Any]],
    n_clusters: int = DEFAULT_N_CLUSTERS,
    random_state: int = 42
) -> List[Dict[str, Any]]:
    """
    Perform K-Means clustering on product embeddings

    Args:
        products: List of products with 'embedding' field
        n_clusters: Number of clusters to create (default from DEFAULT_N_CLUSTERS)
        random_state: Random seed for reproducibility

    Returns:
        Products with 'cluster_id' field added (0 to n_clusters-1)
    """
    logger.info(f"Performing K-Means clustering (n_clusters={n_clusters})...")

    # Extract embeddings as numpy array
    embeddings = np.array([p['embedding'] for p in products])
    logger.info(f"  Embedding shape: {embeddings.shape}")

    # MANDATORY SAFETY CHECK: Validate embedding shape
    if embeddings.ndim != 2 or embeddings.shape[1] != 512:
        raise ValueError(
            f"Invalid embedding shape: {embeddings.shape}, expected (*, 512)"
        )

    # Perform K-Means clustering
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,  # Run 10 times with different centroids
        max_iter=300,
        verbose=0
    )

    logger.info("  Fitting K-Means model...")
    cluster_labels = kmeans.fit_predict(embeddings)

    # Assign cluster_id to each product
    for product, cluster_id in zip(products, cluster_labels):
        product['cluster_id'] = int(cluster_id)

    logger.info("✅ Clustering complete")

    # Log cluster distribution
    cluster_counts = {}
    for cluster_id in cluster_labels:
        cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1

    logger.info("  Cluster distribution:")
    for cluster_id in sorted(cluster_counts.keys()):
        count = cluster_counts[cluster_id]
        percentage = (count / len(products)) * 100
        logger.info(f"    Cluster {cluster_id}: {count} products ({percentage:.1f}%)")

    # Calculate cluster quality metrics
    inertia = kmeans.inertia_
    logger.info(f"  K-Means inertia (lower is better): {inertia:.2f}")

    # OPTIONAL: Save cluster centroids for future use
    try:
        centroids_file = OUTPUT_FILE.parent / "cluster_centroids.npy"
        np.save(centroids_file, kmeans.cluster_centers_)
        logger.info(f"  Saved cluster centroids to {centroids_file}")
    except Exception as e:
        logger.warning(f"  Could not save centroids: {e}")

    return products


# ============================================================================
# CLUSTER ANALYSIS
# ============================================================================

def analyze_clusters(products: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Analyze cluster characteristics

    Returns:
        Dict mapping cluster_id to cluster statistics
    """
    logger.info("Analyzing cluster characteristics...")

    cluster_analysis = defaultdict(lambda: {
        'count': 0,
        'products': [],
        'avg_price': 0,
        'price_range': (float('inf'), 0),
        'categories': defaultdict(int),
        'subcategories': defaultdict(int),
        'brands': defaultdict(int)
    })

    # Collect cluster statistics
    for product in products:
        cluster_id = product['cluster_id']
        cluster = cluster_analysis[cluster_id]

        cluster['count'] += 1
        cluster['products'].append(product['name'])

        # Price stats
        price = product['price']
        cluster['avg_price'] += price
        min_price, max_price = cluster['price_range']
        cluster['price_range'] = (min(min_price, price), max(max_price, price))

        # Category stats
        cluster['categories'][product['category']] += 1
        cluster['subcategories'][product['subcategory']] += 1
        cluster['brands'][product['brand']] += 1

    # Calculate averages
    for cluster_id, cluster in cluster_analysis.items():
        if cluster['count'] > 0:
            cluster['avg_price'] /= cluster['count']

    # Log analysis
    logger.info("\n" + "=" * 80)
    logger.info("CLUSTER ANALYSIS")
    logger.info("=" * 80)

    for cluster_id in sorted(cluster_analysis.keys()):
        cluster = cluster_analysis[cluster_id]
        logger.info(f"\nCluster {cluster_id} ({cluster['count']} products):")
        logger.info(f"  Average Price: ${cluster['avg_price']:.2f}")
        logger.info(f"  Price Range: ${cluster['price_range'][0]:.2f} - ${cluster['price_range'][1]:.2f}")

        # Top categories
        top_cats = sorted(cluster['categories'].items(), key=lambda x: x[1], reverse=True)[:3]
        logger.info(f"  Top Categories: {', '.join(f'{cat} ({count})' for cat, count in top_cats)}")

        # Top subcategories
        top_subcats = sorted(cluster['subcategories'].items(), key=lambda x: x[1], reverse=True)[:3]
        logger.info(f"  Top Subcategories: {', '.join(f'{subcat} ({count})' for subcat, count in top_subcats)}")

        # Sample products
        sample_products = cluster['products'][:5]
        logger.info(f"  Sample Products:")
        for prod_name in sample_products:
            logger.info(f"    - {prod_name}")

    logger.info("=" * 80)

    return dict(cluster_analysis)


# ============================================================================
# SAVE & EXPORT
# ============================================================================

def save_clustered_products(products: List[Dict[str, Any]], output_file: Path):
    """
    Save clustered products to JSON file

    Args:
        products: List of products with cluster_id
        output_file: Path to output JSON file
    """
    logger.info(f"Saving clustered products to {output_file}...")

    # Keep embeddings for Qdrant population
    products_for_json = products

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products_for_json, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Saved {len(products)} products to {output_file}")
    logger.info(f"   File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


def save_cluster_analysis(analysis: Dict, output_file: Path):
    """Save cluster analysis to text file"""
    logger.info(f"Saving cluster analysis to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PRICESENSE - PRODUCT CLUSTER ANALYSIS\n")
        f.write("=" * 80 + "\n\n")

        for cluster_id in sorted(analysis.keys()):
            cluster = analysis[cluster_id]
            f.write(f"CLUSTER {cluster_id}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Product Count: {cluster['count']}\n")
            f.write(f"Average Price: ${cluster['avg_price']:.2f}\n")
            f.write(f"Price Range: ${cluster['price_range'][0]:.2f} - ${cluster['price_range'][1]:.2f}\n\n")

            f.write("Top Categories:\n")
            for cat, count in sorted(cluster['categories'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"  - {cat}: {count} products\n")

            f.write("\nTop Subcategories:\n")
            for subcat, count in sorted(cluster['subcategories'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"  - {subcat}: {count} products\n")

            f.write("\nSample Products:\n")
            for prod_name in cluster['products'][:10]:
                f.write(f"  - {prod_name}\n")

            f.write("\n" + "=" * 80 + "\n\n")

    logger.info(f"✅ Saved analysis to {output_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow"""
    logger.info("\n" + "=" * 80)
    logger.info("🎯 K-MEANS PRODUCT CLUSTERING")
    logger.info("=" * 80)
    logger.info("")

    # Step 1: Generate products
    logger.info("1️⃣ Generating sample products...")
    products = generate_sample_products()
    logger.info(f"✅ Generated {len(products)} products")
    logger.info("")

    # Step 2: Generate embeddings
    logger.info("2️⃣ Generating CLIP embeddings...")
    products = generate_embeddings(products)
    logger.info("")

    # Step 3: Perform clustering
    logger.info("3️⃣ Performing K-Means clustering...")
    products = perform_clustering(products, n_clusters=DEFAULT_N_CLUSTERS)
    logger.info("")

    # Step 4: Analyze clusters
    logger.info("4️⃣ Analyzing clusters...")
    analysis = analyze_clusters(products)
    logger.info("")

    # Step 5: Save outputs
    logger.info("5️⃣ Saving outputs...")

    # Save clustered products
    save_clustered_products(products, OUTPUT_FILE)

    # Save analysis
    analysis_file = OUTPUT_FILE.parent / "cluster_analysis.txt"
    save_cluster_analysis(analysis, analysis_file)

    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ CLUSTERING COMPLETE!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("📊 Summary:")
    logger.info(f"   - Total products: {len(products)}")
    logger.info(f"   - Number of clusters: {DEFAULT_N_CLUSTERS}")
    logger.info(f"   - Output file: {OUTPUT_FILE}")
    logger.info(f"   - Analysis file: {analysis_file}")
    logger.info("")
    logger.info("🎯 Next steps:")
    logger.info("   1. Review cluster_analysis.txt to see cluster characteristics")
    logger.info("   2. Use products_clustered.json in populate_qdrant.py")
    logger.info("   3. Products are ready for Qdrant population!")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    logger.info("## 🔗 AGENT 2.5 (PATHFINDER) CLUSTER USAGE CONTRACT")
    logger.info("")
    logger.info("- `cluster_id` defines semantic similarity between products")
    logger.info("- Products sharing the same `cluster_id` are considered comparable alternatives")
    logger.info("")
    logger.info("Agent 2.5 SHOULD:")
    logger.info("  1. Detect unaffordable product")
    logger.info("  2. Filter products with the same `cluster_id`")
    logger.info("  3. Sort alternatives by price ascending")
    logger.info("  4. Recommend cheaper options within the same cluster")
    logger.info("")
    logger.info("Agent 2.5 MUST NOT:")
    logger.info("  - Compare products across different clusters")
    logger.info("  - Ignore cluster_id when suggesting alternatives")
    logger.info("")
    logger.info("This contract MUST remain stable.")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
