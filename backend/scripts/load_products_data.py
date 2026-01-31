"""
Load Tunisian Electronics Products into Qdrant
Processes 50K products with CLIP embeddings
"""
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
import uuid
import time

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.qdrant_client import QdrantManager
from core.config import settings
from core.embeddings import MultimodalEmbedder
from qdrant_client.models import PointStruct

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Data file path
PRODUCTS_FILE = Path("C:/Users/mezen/OneDrive/Desktop/tunisian_electronics_50k.json")

# Initialize services
qdrant_manager = QdrantManager()
embedder = MultimodalEmbedder()
PRODUCTS_COLLECTION = settings.qdrant_collection_products


def load_json(filepath: Path) -> List[Dict]:
    """Load JSON file"""
    try:
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data)} products from {filepath.name} (encoding: {encoding})")
                return data
            except UnicodeDecodeError:
                continue

        # If all fail, try with errors='ignore'
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} products from {filepath.name} (with error handling)")
        return data

    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return []


def process_product(product: Dict) -> Dict:
    """Convert Tunisian product format to system format"""

    # Convert TND to USD (approximately 1 TND = 0.32 USD)
    tnd_to_usd = 0.32
    price_usd = product.get('price_TND', 0) * tnd_to_usd
    original_price_usd = product.get('original_price_TND', 0) * tnd_to_usd

    # Extract specifications
    specs = product.get('specifications', {})

    # Build searchable text for embedding
    search_text = f"{product.get('name', '')} {product.get('brand', '')} {product.get('category', '')} "
    search_text += f"{product.get('subcategory', '')} {product.get('description', '')} "
    search_text += f"{specs.get('processor', '')} {specs.get('ram', '')} {specs.get('storage', '')} "
    search_text += f"{specs.get('screen_size', '')} {specs.get('resolution', '')} "
    search_text += " ".join(product.get('features', []))

    # Create normalized product
    processed = {
        'product_id': product.get('id'),
        'name': product.get('name'),
        'price': round(price_usd, 2),
        'original_price': round(original_price_usd, 2),
        'category': product.get('category'),
        'subcategory': product.get('subcategory'),
        'brand': product.get('brand'),
        'model': product.get('model'),
        'description': product.get('description'),
        'rating': product.get('rating'),
        'num_reviews': product.get('number_of_reviews', 0),
        'availability': product.get('availability'),
        'condition': product.get('condition'),
        'stock_quantity': product.get('stock_quantity', 0),
        'discount_percentage': product.get('discount_percentage', 0),
        'color': product.get('color'),
        'colors_available': product.get('colors_available', []),
        'features': product.get('features', []),
        'images': product.get('images', []),
        'main_image': product.get('main_image'),
        'seller': product.get('seller'),
        'warranty': product.get('warranty'),
        'shipping': product.get('shipping'),
        'sku': product.get('sku'),
        'specifications': specs,
        'search_text': search_text,
        'created_at': product.get('created_at'),
        'updated_at': product.get('updated_at')
    }

    return processed


def upload_products_to_qdrant(products: List[Dict], batch_size: int = 50):
    """Upload products to Qdrant with CLIP embeddings"""

    total_products = len(products)
    logger.info(f"Uploading {total_products} products to Qdrant in batches of {batch_size}...")

    start_time = time.time()
    successful = 0
    failed = 0

    # Process in batches
    for i in range(0, total_products, batch_size):
        batch = products[i:i + batch_size]
        points = []

        batch_start = time.time()

        for product in batch:
            try:
                # Generate CLIP embedding from search text
                embedding = embedder.embed_text(product['search_text'])

                # Convert numpy array to list
                embedding = embedding.tolist()

                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={k: v for k, v in product.items() if k != 'search_text'}
                )
                points.append(point)

            except Exception as e:
                logger.error(f"Error processing product {product.get('product_id')}: {e}")
                failed += 1
                continue

        # Upload batch
        if points:
            try:
                qdrant_manager.client.upsert(
                    collection_name=PRODUCTS_COLLECTION,
                    points=points
                )
                successful += len(points)

                batch_time = time.time() - batch_start
                progress = (i + len(batch)) / total_products * 100

                logger.info(
                    f"Progress: {progress:.1f}% | "
                    f"Batch {i//batch_size + 1}/{(total_products-1)//batch_size + 1} | "
                    f"{len(points)} products | "
                    f"{batch_time:.2f}s"
                )

            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                failed += len(points)
                continue

    total_time = time.time() - start_time

    logger.info(f"✅ Upload complete!")
    logger.info(f"   Successful: {successful}")
    logger.info(f"   Failed: {failed}")
    logger.info(f"   Total time: {total_time:.2f}s")
    logger.info(f"   Average: {total_time/total_products:.3f}s per product")

    return successful, failed


def main():
    """Main data loading pipeline"""

    print("=" * 80)
    print("🔄 LOADING TUNISIAN ELECTRONICS PRODUCTS INTO QDRANT")
    print("=" * 80)
    print()

    # Step 1: Load JSON file
    print("📂 Step 1: Loading products JSON file...")
    raw_products = load_json(PRODUCTS_FILE)

    if not raw_products:
        print("❌ Error: Could not load products data")
        return

    print(f"   ✅ Loaded {len(raw_products)} products from JSON")
    print()

    # Step 2: Process products
    print("🔧 Step 2: Processing products...")
    processed_products = []

    for product in raw_products:
        try:
            processed = process_product(product)
            processed_products.append(processed)
        except Exception as e:
            logger.error(f"Error processing product {product.get('id')}: {e}")
            continue

    print(f"   ✅ Processed {len(processed_products)} products")
    print()

    # Step 3: Show sample
    print("📊 Step 3: Sample product:")
    if processed_products:
        sample = processed_products[0]
        print(f"   ID: {sample['product_id']}")
        print(f"   Name: {sample['name']}")
        print(f"   Brand: {sample['brand']}")
        print(f"   Category: {sample['category']} > {sample['subcategory']}")
        print(f"   Price: ${sample['price']:.2f} (was ${sample['original_price']:.2f})")
        print(f"   Discount: {sample['discount_percentage']}%")
        print(f"   Rating: {sample['rating']}/5 ({sample['num_reviews']} reviews)")
        print(f"   Availability: {sample['availability']}")
        print(f"   Stock: {sample['stock_quantity']} units")
        print(f"   Features: {len(sample['features'])} features")
        print(f"   Specifications: {len(sample['specifications'])} specs")
    print()

    # Step 4: Clear existing products (optional)
    print("🗑️  Step 4: Database cleanup...")
    try:
        existing_count = qdrant_manager.client.get_collection(PRODUCTS_COLLECTION).points_count
        print(f"   Current products in database: {existing_count}")

        # Delete and recreate collection for clean slate
        print(f"   Recreating collection for clean import...")
        qdrant_manager.delete_collection(PRODUCTS_COLLECTION)
        qdrant_manager.create_collections()
        print(f"   ✅ Collection ready for new products")

    except Exception as e:
        logger.warning(f"Could not check/clear collection: {e}")
    print()

    # Step 5: Upload to Qdrant
    print("☁️  Step 5: Uploading products with CLIP embeddings...")
    print(f"   This will take approximately {len(processed_products) * 0.1 / 60:.1f} minutes")
    print()

    successful, failed = upload_products_to_qdrant(processed_products, batch_size=50)
    print()

    # Step 6: Verify upload
    print("🔍 Step 6: Verifying upload...")
    try:
        collection_info = qdrant_manager.client.get_collection(PRODUCTS_COLLECTION)
        print(f"   ✅ Products collection now has {collection_info.points_count} points")
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}")
    print()

    print("=" * 80)
    print("✅ PRODUCT LOADING COMPLETE!")
    print("=" * 80)
    print()
    print("📈 Summary:")
    print(f"   • Total products loaded: {successful}")
    print(f"   • Failed uploads: {failed}")
    print(f"   • Collection: {PRODUCTS_COLLECTION}")
    print(f"   • Embeddings: CLIP (512 dimensions)")
    print()
    print("🎯 Categories distribution:")

    # Show category breakdown
    categories = {}
    for p in processed_products:
        cat = p.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {cat}: {count} products")

    print()
    print("Next steps:")
    print("   1. Test product search: python scripts/test_system.py")
    print("   2. Run Agent 1: python scripts/test_agent1.py")
    print("   3. Access API docs: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    main()
