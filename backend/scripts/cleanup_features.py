"""
Feature Cleanup Script - Remove Invalid Features
Removes 26 architecturally invalid features from products_with_features.json
Based on architectural audit findings
"""

import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Features to delete based on architectural audit
FEATURES_TO_DELETE = [
    # Thompson Sampling conflicts (2)
    'thompson_alpha_hint',
    'thompson_beta_hint',

    # Popularity bias (4)
    'popularity_score',
    'is_bestseller',
    'is_major_brand',

    # Model outcome leakage (5)
    'conversion_probability',
    'purchase_readiness',
    'recommendation_confidence',
    'rating_confidence',
    'satisfaction_proxy',

    # Agent logic duplication (6)
    'quality_score',
    'value_for_money',
    'deal_score',
    'affordability_score',
    'urgency_score',
    'value_indicator',

    # Redundant/weak features (10)
    'description_word_count',
    'name_word_count',
    'has_multiple_colors',
    'discount_tier',
    'is_budget_friendly',
    'is_new_product',
    'is_premium_product',
    'info_completeness_score',
    'price_tier',
    'seller_product_count',
]

# Features to keep (25 valid features)
VALID_FEATURES = [
    # Metadata (5)
    'has_brand_model',
    'has_detailed_description',
    'has_main_image',
    'image_count',
    'specifications_count',

    # Text (2)
    'name_length',
    'description_length',

    # Price (5)
    'price_normalized',
    'price_category',
    'has_discount',
    'discount_amount_TND',
    'features_count',

    # Rating (3)
    'rating_normalized',
    'rating_category',
    'reviews_log',

    # Inventory (4)
    'availability_encoded',
    'stock_level',
    'condition_encoded',
    'color_options_count',

    # Logistics (4)
    'has_free_shipping',
    'shipping_cost',
    'has_warranty',
    'warranty_months',

    # Dataset stats (2) - use for filtering only
    'category_frequency',
    'brand_frequency',
]


def cleanup_features(input_path: str, output_path: str):
    """Remove invalid features from dataset"""

    logger.info("=" * 70)
    logger.info("FEATURE CLEANUP - Architectural Compliance")
    logger.info("=" * 70)

    # Load data
    logger.info(f"Loading data from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} products")

    # Track deletions
    deletion_stats = {feature: 0 for feature in FEATURES_TO_DELETE}
    features_before = 0
    features_after = 0

    # Clean each product
    for product in data:
        if 'ml_features' not in product:
            continue

        features_before = len(product['ml_features'])

        # Delete invalid features
        for feature in FEATURES_TO_DELETE:
            if feature in product['ml_features']:
                del product['ml_features'][feature]
                deletion_stats[feature] += 1

        features_after = len(product['ml_features'])

    # Verify cleanup
    logger.info("\n" + "=" * 70)
    logger.info("CLEANUP RESULTS")
    logger.info("=" * 70)
    logger.info(f"Features before: {features_before}")
    logger.info(f"Features after: {features_after}")
    logger.info(f"Features deleted: {features_before - features_after}")

    # Verify all products have exactly 25 features
    feature_counts = [len(p.get('ml_features', {})) for p in data]
    unique_counts = set(feature_counts)

    if unique_counts == {25}:
        logger.info("✅ All products have exactly 25 valid features")
    else:
        logger.warning(f"⚠️ Inconsistent feature counts: {unique_counts}")

    # Show deletion breakdown
    logger.info("\nDeleted Features Breakdown:")
    logger.info("-" * 70)

    categories = {
        "Thompson Sampling Conflicts": [
            'thompson_alpha_hint', 'thompson_beta_hint'
        ],
        "Popularity Bias": [
            'popularity_score', 'is_bestseller', 'is_major_brand'
        ],
        "Model Outcome Leakage": [
            'conversion_probability', 'purchase_readiness',
            'recommendation_confidence', 'rating_confidence', 'satisfaction_proxy'
        ],
        "Agent Logic Duplication": [
            'quality_score', 'value_for_money', 'deal_score',
            'affordability_score', 'urgency_score', 'value_indicator'
        ],
        "Redundant/Weak": [
            'description_word_count', 'name_word_count', 'has_multiple_colors',
            'discount_tier', 'is_budget_friendly', 'is_new_product',
            'is_premium_product', 'info_completeness_score', 'price_tier',
            'seller_product_count'
        ]
    }

    for category, features in categories.items():
        deleted_count = sum(deletion_stats[f] for f in features if f in deletion_stats)
        logger.info(f"  {category}: {len(features)} features")

    # Save cleaned data
    logger.info(f"\nSaving cleaned data to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Final verification
    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION")
    logger.info("=" * 70)

    # Reload and verify
    with open(output_path, 'r', encoding='utf-8') as f:
        verified_data = json.load(f)

    sample_features = set(verified_data[0]['ml_features'].keys())
    expected_features = set(VALID_FEATURES)

    if sample_features == expected_features:
        logger.info("✅ Feature set matches expected 25 valid features")
    else:
        missing = expected_features - sample_features
        extra = sample_features - expected_features
        if missing:
            logger.error(f"❌ Missing features: {missing}")
        if extra:
            logger.error(f"❌ Unexpected features: {extra}")

    logger.info(f"\n✅ Cleanup complete!")
    logger.info(f"✅ {len(data)} products with 25 valid features each")
    logger.info(f"✅ Output: {output_path}")
    logger.info("=" * 70)

    return data


def main():
    """Main execution"""
    input_path = "data/features/products_with_features.json"
    output_path = "data/features/products_with_features_cleaned.json"

    # Optionally backup original
    backup_path = "data/features/products_with_features_backup.json"

    logger.info("Creating backup of original file...")
    import shutil
    shutil.copy2(input_path, backup_path)
    logger.info(f"✅ Backup saved to {backup_path}")

    # Cleanup features
    cleaned_data = cleanup_features(input_path, output_path)

    logger.info("\n" + "=" * 70)
    logger.info("NEXT STEPS")
    logger.info("=" * 70)
    logger.info("1. Review the cleaned dataset:")
    logger.info(f"   {output_path}")
    logger.info("")
    logger.info("2. If satisfied, replace the original:")
    logger.info(f"   mv {output_path} {input_path}")
    logger.info("")
    logger.info("3. Update downstream scripts to use 25 features")
    logger.info("")
    logger.info("4. Implement agent logic for deleted features:")
    logger.info("   - Agent 2: affordability_score, value_for_money")
    logger.info("   - Agent 3: quality_score")
    logger.info("   - Agent 2.5: deal_score, urgency_score")
    logger.info("")
    logger.info("5. Initialize Thompson Sampling with uniform priors:")
    logger.info("   - All products: alpha=1, beta=1 (NOT from ratings)")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
