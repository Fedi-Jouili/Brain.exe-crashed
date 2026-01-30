"""
Feature Cleanup Script - Architecture Compliance
Removes 26 invalid features from products_with_features.json
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DELETE_IMMEDIATELY = [
    'thompson_alpha_hint',
    'thompson_beta_hint',
    'popularity_score',
    'is_bestseller',
    'is_major_brand',
    'conversion_probability',
    'purchase_readiness',
    'recommendation_confidence',
    'rating_confidence',
    'satisfaction_proxy',
    'quality_score',
    'value_for_money',
    'deal_score',
    'affordability_score',
    'urgency_score',
    'value_indicator',
    'description_word_count',
    'name_word_count',
    'has_multiple_colors',
    'discount_tier',
    'is_budget_friendly',
    'is_new_product',
    'is_premium_product',
    'info_completeness_score',
    'price_tier',
    'seller_product_count'
]

EXPECTED_VALID_FEATURES = 25


def main():
    input_path = Path("data/features/products_with_features.json")
    output_path = Path("data/features/products_with_features_v2.json")

    logger.info("=" * 70)
    logger.info("FEATURE CLEANUP - ARCHITECTURE COMPLIANCE")
    logger.info("=" * 70)

    # Load data
    logger.info(f"Loading: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"Loaded: {len(products)} products")

    # Get initial feature count
    initial_features = len(products[0]['ml_features']) if products else 0
    logger.info(f"Features before cleanup: {initial_features}")

    # Track deletions
    deletion_count = {feature: 0 for feature in DELETE_IMMEDIATELY}

    # Process each product
    for product in products:
        if 'ml_features' not in product:
            continue

        # Delete invalid features
        for feature in DELETE_IMMEDIATELY:
            if feature in product['ml_features']:
                del product['ml_features'][feature]
                deletion_count[feature] += 1

    # Verify cleanup
    final_features = len(products[0]['ml_features']) if products else 0
    logger.info(f"Features after cleanup: {final_features}")
    logger.info(f"Features deleted: {initial_features - final_features}")

    # Verify all products have exactly 25 features
    feature_counts = [len(p['ml_features']) for p in products]
    unique_counts = set(feature_counts)

    if unique_counts == {EXPECTED_VALID_FEATURES}:
        logger.info(f"✅ All products have exactly {EXPECTED_VALID_FEATURES} features")
    else:
        logger.error(f"❌ Inconsistent feature counts: {unique_counts}")
        raise ValueError(f"Expected {EXPECTED_VALID_FEATURES} features, got {unique_counts}")

    # Verify no deleted features remain
    sample_features = set(products[0]['ml_features'].keys())
    remaining_deleted = sample_features.intersection(DELETE_IMMEDIATELY)

    if remaining_deleted:
        logger.error(f"❌ Deleted features still present: {remaining_deleted}")
        raise ValueError(f"Cleanup failed: {remaining_deleted} still exist")
    else:
        logger.info("✅ No deleted features remain")

    # Log deletion summary
    logger.info("\nDeletion Summary:")
    total_deleted = sum(1 for v in deletion_count.values() if v > 0)
    logger.info(f"  Features deleted: {total_deleted}/{len(DELETE_IMMEDIATELY)}")

    # Save cleaned data
    logger.info(f"\nSaving: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # Final verification
    logger.info("\nFinal Verification:")
    with open(output_path, 'r', encoding='utf-8') as f:
        verified = json.load(f)

    logger.info(f"  Products in output: {len(verified)}")
    logger.info(f"  Features per product: {len(verified[0]['ml_features'])}")
    logger.info(f"  Output file size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    logger.info("\n" + "=" * 70)
    logger.info("✅ CLEANUP COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Input:  {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Products: {len(products)}")
    logger.info(f"Features: {initial_features} → {final_features}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
