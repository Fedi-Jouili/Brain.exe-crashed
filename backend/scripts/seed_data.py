"""
Seed database with sample products, financial rules, and users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
from typing import List, Dict
from core.qdrant_client import qdrant_manager
from core.redis_client import redis_manager
from core.embeddings import MultimodalEmbedder
from core.config import settings
from sklearn.cluster import KMeans
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_products() -> List[Dict]:
    """Generate sample product data"""
    logger.info("📦 Generating sample products...")

    products = [
        # Budget Laptops (Cluster 0)
        {
            "product_id": "PROD0001",
            "name": "Budget Laptop Basic 14\"",
            "description": "Affordable 14-inch laptop with Intel Celeron processor, 4GB RAM, 128GB SSD. Perfect for basic tasks like browsing and word processing. Lightweight and portable for students.",
            "price": 349.99,
            "category": "Electronics",
            "rating": 4.1,
            "num_reviews": 127,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "12 months, 0% APR"
        },
        {
            "product_id": "PROD0002",
            "name": "Student Laptop 15.6\"",
            "description": "Entry-level 15.6-inch laptop with AMD Ryzen 3, 8GB RAM, 256GB SSD. Great battery life for all-day classes. Includes Microsoft Office.",
            "price": 449.99,
            "category": "Electronics",
            "rating": 4.3,
            "num_reviews": 203,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "12 months, 0% APR"
        },

        # Mid-Range Laptops (Cluster 3)
        {
            "product_id": "PROD0042",
            "name": "Laptop Pro 15",
            "description": "Professional 15-inch laptop with Intel i5-11th gen, 16GB RAM, 512GB SSD. Perfect for programming and multitasking. Excellent keyboard and display for developers.",
            "price": 899.99,
            "category": "Electronics",
            "rating": 4.5,
            "num_reviews": 234,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "12 months, 0% APR"
        },
        {
            "product_id": "PROD0043",
            "name": "Business Laptop Standard 14\"",
            "description": "Compact business laptop with Intel i5, 16GB RAM, 512GB SSD, and professional features. Lightweight for travel, long battery life, fingerprint reader for security.",
            "price": 849.99,
            "category": "Electronics",
            "rating": 4.4,
            "num_reviews": 156,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "12 months, 0% APR"
        },

        # Gaming Laptops (Cluster 7)
        {
            "product_id": "PROD0070",
            "name": "Gaming Laptop RTX 3050",
            "description": "Gaming laptop with Intel i5, 16GB RAM, 512GB SSD, NVIDIA RTX 3050 graphics. 144Hz display, RGB keyboard, powerful cooling system for intense gaming sessions.",
            "price": 999.99,
            "category": "Electronics",
            "rating": 4.6,
            "num_reviews": 412,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "18 months, 0% APR"
        },
        {
            "product_id": "PROD0071",
            "name": "Gaming Laptop RTX 3060",
            "description": "High-performance gaming laptop with Intel i7, 16GB RAM, 1TB SSD, NVIDIA RTX 3060 graphics. Premium 165Hz display for competitive gaming, advanced thermal management.",
            "price": 1499.99,
            "category": "Electronics",
            "rating": 4.7,
            "num_reviews": 387,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "24 months, 0% APR"
        },

        # Premium/Workstation (Cluster 9)
        {
            "product_id": "PROD0090",
            "name": "Professional Workstation 15\"",
            "description": "High-end workstation laptop with Intel i7-12th gen, 32GB RAM, 1TB SSD, NVIDIA Quadro graphics. Color-accurate 4K display for designers, engineers, and content creators.",
            "price": 2299.99,
            "category": "Electronics",
            "rating": 4.8,
            "num_reviews": 89,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "24 months, 0% APR"
        },

        # Tablets (Cluster 8) - Different category
        {
            "product_id": "PROD0080",
            "name": "Tablet Pro 11\"",
            "description": "Premium tablet with stylus support, 128GB storage, cellular connectivity. Perfect alternative to laptop for light work and entertainment. All-day battery life.",
            "price": 649.99,
            "category": "Electronics",
            "rating": 4.5,
            "num_reviews": 298,
            "in_stock": True,
            "financing_available": True,
            "financing_terms": "12 months, 0% APR"
        },
    ]

    logger.info(f"✅ Generated {len(products)} sample products")
    return products


def embed_and_cluster_products(products: List[Dict]) -> List[Dict]:
    """Add embeddings and cluster IDs to products"""
    logger.info("🧠 Generating embeddings and clustering...")

    embedder = MultimodalEmbedder()

    # Generate embeddings
    descriptions = [p['description'] for p in products]
    embeddings = embedder.embed_batch_text(descriptions)

    # Add embeddings to products
    for product, embedding in zip(products, embeddings):
        product['embedding'] = embedding.tolist()

    # K-Means clustering (for larger dataset, use 10 clusters)
    if len(products) >= 8:
        kmeans = KMeans(n_clusters=min(10, len(products) // 2), random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        for product, label in zip(products, cluster_labels):
            product['cluster_id'] = int(label)
    else:
        # For small dataset, assign based on price ranges
        for product in products:
            if product['price'] < 500:
                product['cluster_id'] = 0
            elif product['price'] < 1000:
                product['cluster_id'] = 3
            elif product['price'] < 1500:
                product['cluster_id'] = 7
            else:
                product['cluster_id'] = 9

    logger.info("✅ Embeddings and clustering complete")
    return products


def seed_products():
    """Seed products collection"""
    logger.info("📦 Seeding products...")

    products = generate_sample_products()
    products = embed_and_cluster_products(products)

    qdrant_manager.upsert_products(products)

    # Initialize Thompson Sampling parameters
    for product in products:
        redis_manager.client.set(
            f"thompson:{product['product_id']}",
            json.dumps({
                'alpha': settings.thompson_alpha_init,
                'beta': settings.thompson_beta_init
            })
        )

    logger.info(f"✅ Seeded {len(products)} products with Thompson parameters")


def generate_financial_rules() -> List[str]:
    """Generate financial knowledge base chunks"""
    rules = [
        """
        Debt-to-Income Ratio (DTI): The debt-to-income ratio is calculated as total monthly
        debt payments divided by gross monthly income. Financial advisors recommend keeping
        DTI below 43% to maintain financial health and qualify for most financing options.
        A DTI above 43% indicates financial stress and difficulty managing debt obligations.
        """,

        """
        Payment-to-Income Ratio (PTI): When considering financing for a purchase, the monthly
        payment should not exceed 15% of your gross monthly income. This ensures the payment
        remains manageable and doesn't strain your budget. Lower ratios (under 10%) are ideal
        for non-essential purchases.
        """,

        """
        Emergency Fund Requirements: Financial experts recommend maintaining an emergency fund
        covering 3-6 months of expenses. Before making a major purchase, ensure your remaining
        savings after the purchase will still cover at least 3 months of expenses. This protects
        against unexpected financial shocks.
        """,

        """
        Safe Purchase Limit: For cash purchases, a conservative rule is to spend no more than
        30% of your monthly disposable income (income minus expenses) on discretionary items.
        This prevents impulse purchases from derailing your financial goals and maintains
        financial flexibility.
        """,

        """
        Credit Score and Financing: A credit score of 650 or higher is typically required for
        favorable financing terms with 0% APR promotional offers. Scores below 650 may result
        in higher interest rates or financing denial. Maintain good credit by paying bills on
        time and keeping credit utilization below 30%.
        """,
    ]

    return [rule.strip() for rule in rules]


def seed_financial_kb():
    """Seed financial knowledge base"""
    logger.info("📚 Seeding financial knowledge base...")

    rules = generate_financial_rules()

    embedder = MultimodalEmbedder()

    # Generate embeddings and create chunks
    chunks = []
    for idx, rule in enumerate(rules):
        embedding = embedder.embed_text(rule)

        # Determine category from content
        if 'debt-to-income' in rule.lower():
            category = 'debt'
        elif 'payment-to-income' in rule.lower():
            category = 'financing'
        elif 'emergency fund' in rule.lower():
            category = 'emergency'
        elif 'purchase limit' in rule.lower():
            category = 'affordability'
        elif 'credit score' in rule.lower():
            category = 'credit'
        else:
            category = 'general'

        chunks.append({
            'chunk_id': f'RULE{idx+1:04d}',
            'text': rule,
            'embedding': embedding.tolist(),
            'category': category,
            'source': 'system'
        })

    qdrant_manager.upsert_financial_rules(chunks)
    logger.info(f"✅ Seeded {len(chunks)} financial rule chunks")


def generate_sample_users() -> List[Dict]:
    """Generate sample user profiles"""
    users = [
        {
            "user_id": "USER0001",
            "monthly_income": 5000,
            "credit_score": 720,
            "risk_tolerance": "medium",
            "preferred_categories": ["Electronics"],
            "purchase_history": ["PROD0042", "PROD0080"]
        },
        {
            "user_id": "USER0002",
            "monthly_income": 3500,
            "credit_score": 680,
            "risk_tolerance": "low",
            "preferred_categories": ["Electronics"],
            "purchase_history": ["PROD0001", "PROD0002"]
        },
        {
            "user_id": "USER0003",
            "monthly_income": 7000,
            "credit_score": 780,
            "risk_tolerance": "high",
            "preferred_categories": ["Electronics"],
            "purchase_history": ["PROD0070", "PROD0071", "PROD0090"]
        },
    ]

    return users


def seed_users():
    """Seed sample user profiles"""
    logger.info("👥 Seeding user profiles...")

    users = generate_sample_users()

    embedder = MultimodalEmbedder()

    for user in users:
        # Generate preference vector based on profile
        # Simple approach: embed preferred categories
        preference_text = f"User interested in {', '.join(user['preferred_categories'])}"
        preference_vector = embedder.embed_text(preference_text)

        user['preference_vector'] = preference_vector.tolist()

        qdrant_manager.upsert_user(user)

    logger.info(f"✅ Seeded {len(users)} user profiles")


def main():
    """Seed all collections"""
    logger.info("=" * 60)
    logger.info("🌱 PriceSense - Seeding Sample Data")
    logger.info("=" * 60)
    logger.info("")

    try:
        # Seed products
        seed_products()
        logger.info("")

        # Seed financial knowledge base
        seed_financial_kb()
        logger.info("")

        # Seed users
        seed_users()
        logger.info("")

        # Summary
        logger.info("=" * 60)
        logger.info("✅ All sample data seeded successfully!")
        logger.info("")
        logger.info("📊 Database Summary:")
        logger.info(f"   - Products: {qdrant_manager.count_points(settings.qdrant_collection_products)}")
        logger.info(f"   - Financial KB: {qdrant_manager.count_points(settings.qdrant_collection_financial_kb)}")
        logger.info(f"   - Users: {qdrant_manager.count_points(settings.qdrant_collection_users)}")
        logger.info(f"   - Transactions: {qdrant_manager.count_points(settings.qdrant_collection_transactions)}")
        logger.info("")
        logger.info("🎯 Next step: Start the backend server and test search!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}", exc_info=True)


if __name__ == "__main__":
    main()
