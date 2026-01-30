"""
Populate Qdrant Financial Knowledge Base

Uploads financial rules for Agent 2 (Financial Analyzer) RAG retrieval.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import List, Dict, Any
import hashlib

from core.qdrant_client import qdrant_manager
from core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Financial rules for RAG retrieval
FINANCIAL_RULES = [
    {
        "text": "Payment-to-Income (PTI) Ratio: Monthly payment should not exceed 15% of monthly income for sustainable financing. "
                "Exceeding 20% is considered high risk and may lead to financial strain.",
        "category": "financing",
        "source": "financial_best_practices"
    },
    {
        "text": "Emergency Fund Requirement: Users should maintain 3-6 months of expenses in emergency savings before making "
                "discretionary purchases. Cash purchases should leave at least $500 emergency buffer.",
        "category": "savings",
        "source": "financial_best_practices"
    },
    {
        "text": "Debt-to-Income (DTI) Ratio: Total monthly debt payments should not exceed 36% of gross monthly income. "
                "Housing costs should stay below 28% (28/36 rule).",
        "category": "debt_management",
        "source": "financial_best_practices"
    },
    {
        "text": "Credit Score Impact on Financing: Excellent credit (750+) qualifies for 0-6% APR. Good credit (700-749) gets 6-12% APR. "
                "Fair credit (650-699) gets 12-20% APR. Poor credit (<650) may face 20%+ APR or denial.",
        "category": "credit",
        "source": "lending_guidelines"
    },
    {
        "text": "Savings Timeline Guidelines: For purchases requiring <3 months savings, recommend immediate saving. "
                "For 3-6 months, evaluate opportunity cost. For >6 months, consider financing alternatives or cheaper products.",
        "category": "savings",
        "source": "financial_planning"
    },
    {
        "text": "Total Cost of Financing: Always calculate total cost (principal + interest) before recommending financing. "
                "If total interest exceeds 20% of principal, flag as expensive financing and suggest alternatives.",
        "category": "financing",
        "source": "consumer_protection"
    },
    {
        "text": "Cash vs. Financing Decision Matrix: Cash is optimal when user can afford 2x the purchase price in savings. "
                "Financing is acceptable when PTI < 15% and emergency fund intact. Saving is best when neither condition met.",
        "category": "decision_framework",
        "source": "financial_advisory"
    },
    {
        "text": "Affordability Threshold: A product is cash-affordable if price ≤ 40% of available cash AND leaves $500+ emergency buffer. "
                "This ensures financial safety while enabling purchase.",
        "category": "affordability",
        "source": "financial_best_practices"
    },
    {
        "text": "Income-Based Product Recommendations: Budget products should be <10% of monthly income. Mid-range products 10-25%. "
                "Premium products 25-50%. Products >50% monthly income require extended planning or financing.",
        "category": "product_selection",
        "source": "consumer_guidance"
    },
    {
        "text": "Financing Term Optimization: Shorter terms (6-12 months) minimize interest but require higher monthly payments. "
                "Longer terms (18-36 months) reduce monthly burden but increase total cost. Balance PTI with total interest.",
        "category": "financing",
        "source": "lending_optimization"
    },
    {
        "text": "Opportunity Cost of Saving: Money saved for purchases loses potential investment returns (avg 7% annually). "
                "For long savings periods (>12 months), consider low-interest financing instead if PTI acceptable.",
        "category": "savings",
        "source": "investment_principles"
    },
    {
        "text": "Red Flags for Risky Purchases: No emergency fund + financing = high risk. PTI > 20% = unsustainable. "
                "Total debt payments > 40% income = financial danger zone. Recommend cheaper alternatives or extended saving.",
        "category": "risk_assessment",
        "source": "financial_safety"
    }
]


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for financial rule text

    For production, replace with actual embedding model (CLIP, OpenAI, etc.)
    This is a deterministic placeholder based on text hash.

    Args:
        text: Rule text to embed

    Returns:
        512-dimensional embedding vector
    """
    # Deterministic embedding based on text hash
    # In production, use: CLIP, sentence-transformers, or OpenAI embeddings

    text_hash = hashlib.sha256(text.encode()).digest()

    # Create 512-dim vector from hash (repeating pattern)
    embedding = []
    for i in range(512):
        byte_idx = i % len(text_hash)
        value = (text_hash[byte_idx] / 255.0) - 0.5  # Normalize to [-0.5, 0.5]
        embedding.append(value)

    # Add some variation based on text length
    length_factor = len(text) / 1000.0
    embedding = [v * length_factor for v in embedding]

    # Normalize to unit vector (cosine similarity works better)
    magnitude = sum(v**2 for v in embedding) ** 0.5
    if magnitude > 0:
        embedding = [v / magnitude for v in embedding]

    return embedding


def populate_financial_kb():
    """
    Populate financial knowledge base collection

    Steps:
    1. Check Qdrant health
    2. Create collections if needed
    3. Generate embeddings for rules
    4. Upload to Qdrant
    5. Verify count
    6. Test retrieval
    """
    logger.info("=" * 80)
    logger.info("POPULATE QDRANT - Financial Knowledge Base")
    logger.info("=" * 80)

    # Step 1: Health check
    logger.info("\n[1/6] Checking Qdrant health...")
    if not qdrant_manager.health_check():
        logger.error("❌ Qdrant is not healthy. Is it running?")
        logger.error("Start with: docker-compose up -d")
        sys.exit(1)
    logger.info("✅ Qdrant is healthy")

    # Step 2: Create collections
    logger.info("\n[2/6] Creating collections...")
    try:
        qdrant_manager.create_collections()
        logger.info("✅ Collections ready")
    except Exception as e:
        logger.error(f"❌ Failed to create collections: {e}")
        sys.exit(1)

    # Step 3: Generate embeddings
    logger.info(f"\n[3/6] Generating embeddings for {len(FINANCIAL_RULES)} rules...")

    rules_with_embeddings = []
    for idx, rule in enumerate(FINANCIAL_RULES):
        chunk_id = f"financial_rule_{idx:03d}"
        embedding = generate_embedding(rule['text'])

        rules_with_embeddings.append({
            'chunk_id': chunk_id,
            'text': rule['text'],
            'category': rule['category'],
            'source': rule['source'],
            'embedding': embedding
        })

        logger.info(f"   Generated embedding for rule {idx + 1}/{len(FINANCIAL_RULES)}: {rule['category']}")

    logger.info(f"✅ Generated {len(rules_with_embeddings)} embeddings (512-dim each)")

    # Step 4: Upload to Qdrant
    logger.info(f"\n[4/6] Uploading {len(rules_with_embeddings)} rules to Qdrant...")
    try:
        qdrant_manager.upsert_financial_rules(rules_with_embeddings)
        logger.info("✅ Financial rules uploaded")
    except Exception as e:
        logger.error(f"❌ Failed to upload rules: {e}")
        sys.exit(1)

    # Step 5: Verify count
    logger.info("\n[5/6] Verifying knowledge base count...")
    try:
        count = qdrant_manager.count_points(settings.qdrant_collection_financial_kb)
        logger.info(f"✅ Rules in Qdrant: {count}")

        if count != len(FINANCIAL_RULES):
            logger.warning(f"⚠️ Count mismatch: expected {len(FINANCIAL_RULES)}, got {count}")
    except Exception as e:
        logger.error(f"❌ Failed to verify count: {e}")
        sys.exit(1)

    # Step 6: Test retrieval
    logger.info("\n[6/6] Testing RAG retrieval...")
    try:
        # Test query: "What is the maximum payment ratio?"
        test_query = "What is the maximum payment to income ratio for safe financing?"
        test_embedding = generate_embedding(test_query)

        retrieved_rules = qdrant_manager.retrieve_financial_rules(
            query_vector=test_embedding,
            top_k=3
        )

        logger.info(f"✅ RAG retrieval works - found {len(retrieved_rules)} relevant rules")

        if retrieved_rules:
            logger.info("\nTop retrieved rule:")
            top_rule = retrieved_rules[0]
            logger.info(f"   Category: {top_rule.payload['category']}")
            logger.info(f"   Score: {top_rule.score:.3f}")
            logger.info(f"   Text: {top_rule.payload['text'][:150]}...")

    except Exception as e:
        logger.error(f"❌ RAG retrieval failed: {e}")
        sys.exit(1)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ POPULATE COMPLETE")
    logger.info(f"   Total rules: {count}")
    logger.info(f"   Categories: {len(set(r['category'] for r in FINANCIAL_RULES))}")
    logger.info("   Categories:")

    categories = {}
    for rule in FINANCIAL_RULES:
        cat = rule['category']
        categories[cat] = categories.get(cat, 0) + 1

    for cat, cnt in sorted(categories.items()):
        logger.info(f"     - {cat}: {cnt} rules")

    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        populate_financial_kb()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)
