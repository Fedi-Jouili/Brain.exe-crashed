"""
Data Validation Script
Validates cleaned and featured product data for quality assurance
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataValidator:
    """Validates product data quality and completeness"""

    def __init__(self):
        self.validation_results = {
            'total_records': 0,
            'valid_records': 0,
            'warnings': [],
            'errors': [],
            'field_coverage': {},
            'feature_stats': {}
        }

    def validate_cleaned_data(self, file_path: str) -> Tuple[bool, Dict]:
        """Validate cleaned product data"""
        logger.info(f"Validating cleaned data: {file_path}")

        # Load data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.validation_results['total_records'] = len(data)

        # Required fields for cleaned data
        required_fields = [
            'id', 'name', 'category', 'price_TND', 'availability',
            'condition', 'rating', 'seller'
        ]

        # Validate each record
        valid_count = 0
        for i, record in enumerate(data):
            is_valid = True

            # Check required fields
            for field in required_fields:
                if field not in record or record[field] is None:
                    self.validation_results['errors'].append(
                        f"Record {i} (ID: {record.get('id', 'UNKNOWN')}): Missing required field '{field}'"
                    )
                    is_valid = False

            # Validate data types and ranges
            if 'price_TND' in record:
                if not isinstance(record['price_TND'], (int, float)) or record['price_TND'] <= 0:
                    self.validation_results['errors'].append(
                        f"Record {i}: Invalid price {record.get('price_TND')}"
                    )
                    is_valid = False

            if 'rating' in record:
                if not isinstance(record['rating'], (int, float)) or not 0 <= record['rating'] <= 5:
                    self.validation_results['warnings'].append(
                        f"Record {i}: Rating out of range {record.get('rating')}"
                    )

            if is_valid:
                valid_count += 1

        self.validation_results['valid_records'] = valid_count

        # Calculate field coverage
        for field in required_fields + ['description', 'specifications', 'images']:
            count = sum(1 for r in data if r.get(field))
            coverage = (count / len(data)) * 100 if data else 0
            self.validation_results['field_coverage'][field] = f"{coverage:.1f}%"

        # Determine if validation passed
        passed = len(self.validation_results['errors']) == 0

        return passed, self.validation_results

    def validate_featured_data(self, file_path: str) -> Tuple[bool, Dict]:
        """Validate featured product data with ML features"""
        logger.info(f"Validating featured data: {file_path}")

        # Load data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.validation_results['total_records'] = len(data)

        # Validate each record has ml_features
        valid_count = 0
        feature_count = None

        for i, record in enumerate(data):
            is_valid = True

            # Check for ml_features field
            if 'ml_features' not in record:
                self.validation_results['errors'].append(
                    f"Record {i}: Missing 'ml_features' field"
                )
                is_valid = False
                continue

            ml_features = record['ml_features']

            # Count features
            current_feature_count = len(ml_features)
            if feature_count is None:
                feature_count = current_feature_count
            elif current_feature_count != feature_count:
                self.validation_results['warnings'].append(
                    f"Record {i}: Feature count mismatch (expected {feature_count}, got {current_feature_count})"
                )

            # Validate feature values are numeric
            for feat_name, feat_value in ml_features.items():
                if not isinstance(feat_value, (int, float)):
                    self.validation_results['warnings'].append(
                        f"Record {i}: Non-numeric feature '{feat_name}' = {feat_value}"
                    )

            if is_valid:
                valid_count += 1

        self.validation_results['valid_records'] = valid_count
        self.validation_results['feature_stats']['total_features'] = feature_count

        # Check if we have at least 40 features
        if feature_count and feature_count < 40:
            self.validation_results['warnings'].append(
                f"Feature count below target: {feature_count} < 40"
            )

        # Determine if validation passed
        passed = len(self.validation_results['errors']) == 0

        return passed, self.validation_results

    def print_results(self):
        """Print validation results"""
        logger.info("=" * 60)
        logger.info("DATA VALIDATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total records: {self.validation_results['total_records']}")
        logger.info(f"Valid records: {self.validation_results['valid_records']}")
        logger.info(f"Errors: {len(self.validation_results['errors'])}")
        logger.info(f"Warnings: {len(self.validation_results['warnings'])}")

        if self.validation_results['field_coverage']:
            logger.info("\nField Coverage:")
            for field, coverage in self.validation_results['field_coverage'].items():
                logger.info(f"  {field}: {coverage}")

        if self.validation_results['feature_stats']:
            logger.info("\nFeature Statistics:")
            for stat, value in self.validation_results['feature_stats'].items():
                logger.info(f"  {stat}: {value}")

        if self.validation_results['errors']:
            logger.error(f"\n❌ Found {len(self.validation_results['errors'])} errors:")
            for error in self.validation_results['errors'][:10]:  # Show first 10
                logger.error(f"  - {error}")
            if len(self.validation_results['errors']) > 10:
                logger.error(f"  ... and {len(self.validation_results['errors']) - 10} more")

        if self.validation_results['warnings']:
            logger.warning(f"\n⚠️  Found {len(self.validation_results['warnings'])} warnings:")
            for warning in self.validation_results['warnings'][:10]:  # Show first 10
                logger.warning(f"  - {warning}")
            if len(self.validation_results['warnings']) > 10:
                logger.warning(f"  ... and {len(self.validation_results['warnings']) - 10} more")

        logger.info("=" * 60)

        if len(self.validation_results['errors']) == 0:
            logger.info("✓ VALIDATION PASSED")
        else:
            logger.error("✗ VALIDATION FAILED")

        logger.info("=" * 60)


def main():
    """Main validation function"""
    validator = DataValidator()

    # Validate cleaned data
    cleaned_path = "data/processed/products_cleaned.json"
    if Path(cleaned_path).exists():
        logger.info("Validating cleaned data...")
        passed, results = validator.validate_cleaned_data(cleaned_path)
        validator.print_results()

        if not passed:
            logger.error(f"Cleaned data validation failed!")
            return False
    else:
        logger.warning(f"Cleaned data not found: {cleaned_path}")

    # Reset for featured data validation
    validator.validation_results = {
        'total_records': 0,
        'valid_records': 0,
        'warnings': [],
        'errors': [],
        'field_coverage': {},
        'feature_stats': {}
    }

    # Validate featured data
    featured_path = "data/features/products_with_features.json"
    if Path(featured_path).exists():
        logger.info("\nValidating featured data...")
        passed, results = validator.validate_featured_data(featured_path)
        validator.print_results()

        if not passed:
            logger.error(f"Featured data validation failed!")
            return False
    else:
        logger.warning(f"Featured data not found: {featured_path}")

    logger.info("\n✓ All validations passed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
