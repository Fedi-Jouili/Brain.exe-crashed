"""
Complete Data Processing Pipeline
Orchestrates cleaning, feature engineering, and validation
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.clean_data import DataCleaner
from scripts.engineer_features import FeatureEngineer
from scripts.validate_data import DataValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute complete data processing pipeline"""

    logger.info("=" * 80)
    logger.info("TUNISIAN ELECTRONICS DATASET - COMPLETE PROCESSING PIPELINE")
    logger.info("=" * 80)

    # Define paths
    raw_path = "data/raw/tunisian_electronics_50k.json"
    cleaned_path = "data/processed/products_cleaned.json"
    featured_path = "data/features/products_with_features.json"

    # Check if raw data exists
    if not Path(raw_path).exists():
        logger.error(f"❌ Raw data not found: {raw_path}")
        logger.error("Please place tunisian_electronics_50k.json in data/raw/ directory")
        return False

    # ========== STEP 1: DATA CLEANING ==========
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1/3: DATA CLEANING")
    logger.info("=" * 80)

    try:
        cleaner = DataCleaner(raw_path, cleaned_path)
        cleaned_data = cleaner.process()
        logger.info(f"✓ Data cleaning completed successfully")
        logger.info(f"✓ Output: {cleaned_path}")
    except Exception as e:
        logger.error(f"❌ Data cleaning failed: {str(e)}")
        return False

    # ========== STEP 2: FEATURE ENGINEERING ==========
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2/3: FEATURE ENGINEERING")
    logger.info("=" * 80)

    try:
        engineer = FeatureEngineer(cleaned_path, featured_path)
        featured_data = engineer.process()
        logger.info(f"✓ Feature engineering completed successfully")
        logger.info(f"✓ Output: {featured_path}")
    except Exception as e:
        logger.error(f"❌ Feature engineering failed: {str(e)}")
        return False

    # ========== STEP 3: DATA VALIDATION ==========
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3/3: DATA VALIDATION")
    logger.info("=" * 80)

    try:
        validator = DataValidator()

        # Validate cleaned data
        logger.info("Validating cleaned data...")
        passed_clean, _ = validator.validate_cleaned_data(cleaned_path)

        if not passed_clean:
            logger.error("❌ Cleaned data validation failed")
            validator.print_results()
            return False

        # Reset validator
        validator.validation_results = {
            'total_records': 0,
            'valid_records': 0,
            'warnings': [],
            'errors': [],
            'field_coverage': {},
            'feature_stats': {}
        }

        # Validate featured data
        logger.info("Validating featured data...")
        passed_featured, _ = validator.validate_featured_data(featured_path)

        validator.print_results()

        if not passed_featured:
            logger.error("❌ Featured data validation failed")
            return False

        logger.info(f"✓ Data validation completed successfully")

    except Exception as e:
        logger.error(f"❌ Data validation failed: {str(e)}")
        return False

    # ========== PIPELINE COMPLETE ==========
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("=" * 80)
    logger.info("✓ All steps completed successfully!")
    logger.info("")
    logger.info("Generated Files:")
    logger.info(f"  1. {cleaned_path}")
    logger.info(f"  2. {featured_path}")
    logger.info("")
    logger.info("Next Steps:")
    logger.info("  • Generate CLIP embeddings for product images/text")
    logger.info("  • Insert products into Qdrant vector database")
    logger.info("  • Initialize Thompson Sampling parameters in Redis")
    logger.info("  • Start the PriceSense backend API")
    logger.info("=" * 80)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
