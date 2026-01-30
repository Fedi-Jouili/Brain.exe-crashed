"""
Feature Engineering Script for Tunisian Electronics Dataset
Generates 40+ ML-ready features from cleaned product data
"""

import json
import re
import math
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import logging
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Engineers 40+ features for ML-ready product recommendations"""

    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.dataset_stats = {}
        self.feature_stats = {}

    def load_data(self) -> List[Dict[str, Any]]:
        """Load cleaned JSON data"""
        logger.info(f"Loading cleaned data from {self.input_path}")
        with open(self.input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} records")
        return data

    def compute_dataset_stats(self, data: List[Dict[str, Any]]):
        """Compute dataset-wide statistics for normalization"""
        logger.info("Computing dataset statistics...")

        prices = [r['price_TND'] for r in data if r.get('price_TND', 0) > 0]
        ratings = [r['rating'] for r in data if r.get('rating', 0) > 0]
        reviews = [r['number_of_reviews'] for r in data if r.get('number_of_reviews', 0) > 0]

        # Price statistics
        self.dataset_stats['price_mean'] = sum(prices) / len(prices) if prices else 0
        self.dataset_stats['price_std'] = self._std_dev(prices) if prices else 1
        self.dataset_stats['price_min'] = min(prices) if prices else 0
        self.dataset_stats['price_max'] = max(prices) if prices else 1

        # Rating statistics
        self.dataset_stats['rating_mean'] = sum(ratings) / len(ratings) if ratings else 0
        self.dataset_stats['rating_std'] = self._std_dev(ratings) if ratings else 1

        # Review statistics
        self.dataset_stats['reviews_mean'] = sum(reviews) / len(reviews) if reviews else 0
        self.dataset_stats['reviews_std'] = self._std_dev(reviews) if reviews else 1

        # Category counts
        category_counts = Counter(r['category'] for r in data if r.get('category'))
        self.dataset_stats['category_counts'] = dict(category_counts)

        # Brand counts
        brand_counts = Counter(r['brand'] for r in data if r.get('brand'))
        self.dataset_stats['brand_counts'] = dict(brand_counts)

        # Seller counts
        seller_counts = Counter(r['seller'] for r in data if r.get('seller'))
        self.dataset_stats['seller_counts'] = dict(seller_counts)

        logger.info(f"Dataset stats: Price range [{self.dataset_stats['price_min']:.2f}, {self.dataset_stats['price_max']:.2f}] TND")
        logger.info(f"Total categories: {len(category_counts)}, Total brands: {len(brand_counts)}")

    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 1.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance) if variance > 0 else 1.0

    def _normalize_zscore(self, value: float, mean: float, std: float) -> float:
        """Z-score normalization"""
        return (value - mean) / std if std > 0 else 0.0

    def _normalize_minmax(self, value: float, min_val: float, max_val: float) -> float:
        """Min-max normalization to [0, 1]"""
        if max_val - min_val == 0:
            return 0.0
        return (value - min_val) / (max_val - min_val)

    # ========== TEXT FEATURES (7 features) ==========

    def extract_text_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text-based features"""
        features = {}

        name = record.get('name', '')
        description = record.get('description', '')

        # 1. Name length
        features['name_length'] = len(name)
        features['name_word_count'] = len(name.split())

        # 2. Description metrics
        features['description_length'] = len(description)
        features['description_word_count'] = len(description.split())

        # 3. Feature list size
        features['features_count'] = len(record.get('features', []))

        # 4. Has detailed description
        features['has_detailed_description'] = 1 if len(description) > 100 else 0

        # 5. Specification count
        features['specifications_count'] = len(record.get('specifications', {}))

        return features

    # ========== PRICE FEATURES (8 features) ==========

    def extract_price_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract price-related features"""
        features = {}

        price = record.get('price_TND', 0)
        original_price = record.get('original_price_TND', 0)
        discount = record.get('discount_percentage', 0)

        # 1. Price normalized (z-score)
        features['price_normalized'] = self._normalize_zscore(
            price,
            self.dataset_stats['price_mean'],
            self.dataset_stats['price_std']
        )

        # 2. Price tier (0-1 scale)
        features['price_tier'] = self._normalize_minmax(
            price,
            self.dataset_stats['price_min'],
            self.dataset_stats['price_max']
        )

        # 3. Has discount
        features['has_discount'] = 1 if discount > 0 else 0

        # 4. Discount amount in TND
        features['discount_amount_TND'] = original_price - price if original_price > price else 0

        # 5. Discount tier (categorized)
        if discount >= 30:
            features['discount_tier'] = 3  # High discount
        elif discount >= 15:
            features['discount_tier'] = 2  # Medium discount
        elif discount > 0:
            features['discount_tier'] = 1  # Low discount
        else:
            features['discount_tier'] = 0  # No discount

        # 6. Price category (budget, mid, premium, luxury)
        if price < 500:
            features['price_category'] = 0  # Budget
        elif price < 2000:
            features['price_category'] = 1  # Mid-range
        elif price < 5000:
            features['price_category'] = 2  # Premium
        else:
            features['price_category'] = 3  # Luxury

        # 7. Affordability score (inverse price, higher = more affordable)
        max_price = self.dataset_stats['price_max']
        features['affordability_score'] = 1.0 - (price / max_price) if max_price > 0 else 0.5

        # 8. Value indicator (discount + low price)
        features['value_indicator'] = (features['affordability_score'] + (discount / 100)) / 2

        return features

    # ========== RATING FEATURES (5 features) ==========

    def extract_rating_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract rating and review features"""
        features = {}

        rating = record.get('rating', 0)
        num_reviews = record.get('number_of_reviews', 0)

        # 1. Rating normalized
        features['rating_normalized'] = rating / 5.0 if rating > 0 else 0.0

        # 2. Rating category
        if rating >= 4.5:
            features['rating_category'] = 4  # Excellent
        elif rating >= 4.0:
            features['rating_category'] = 3  # Very Good
        elif rating >= 3.0:
            features['rating_category'] = 2  # Good
        elif rating > 0:
            features['rating_category'] = 1  # Fair
        else:
            features['rating_category'] = 0  # No rating

        # 3. Review count normalized (log scale)
        features['reviews_log'] = math.log1p(num_reviews)

        # 4. Popularity score (rating * log(reviews + 1))
        features['popularity_score'] = rating * math.log1p(num_reviews)

        # 5. Confidence score (rating weighted by review count)
        # More reviews = higher confidence in rating
        review_weight = min(num_reviews / 100, 1.0)  # Cap at 100 reviews
        features['rating_confidence'] = rating * (0.5 + 0.5 * review_weight)

        return features

    # ========== CATEGORICAL FEATURES (5 features) ==========

    def extract_categorical_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract categorical encoding features"""
        features = {}

        category = record.get('category', '')
        brand = record.get('brand', '')
        seller = record.get('seller', '')

        # 1. Category frequency (how common is this category)
        category_count = self.dataset_stats['category_counts'].get(category, 0)
        features['category_frequency'] = category_count

        # 2. Brand frequency
        brand_count = self.dataset_stats['brand_counts'].get(brand, 0)
        features['brand_frequency'] = brand_count

        # 3. Is major brand (top 20 brands)
        top_brands = sorted(self.dataset_stats['brand_counts'].items(),
                           key=lambda x: x[1], reverse=True)[:20]
        features['is_major_brand'] = 1 if brand in dict(top_brands) else 0

        # 4. Seller reputation (based on product count)
        seller_count = self.dataset_stats['seller_counts'].get(seller, 0)
        features['seller_product_count'] = seller_count

        # 5. Has brand and model
        features['has_brand_model'] = 1 if brand and record.get('model') else 0

        return features

    # ========== INVENTORY FEATURES (3 features) ==========

    def extract_inventory_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract inventory and availability features"""
        features = {}

        availability = record.get('availability', 'unknown')
        stock = record.get('stock_quantity', 0)
        condition = record.get('condition', 'new')

        # 1. Availability encoded
        availability_map = {
            'in_stock': 2,
            'coming_soon': 1,
            'out_of_stock': 0,
            'unknown': 0
        }
        features['availability_encoded'] = availability_map.get(availability, 0)

        # 2. Stock level category
        if stock == 0:
            features['stock_level'] = 0  # No stock
        elif stock < 5:
            features['stock_level'] = 1  # Low stock
        elif stock < 20:
            features['stock_level'] = 2  # Medium stock
        else:
            features['stock_level'] = 3  # High stock

        # 3. Condition encoded
        condition_map = {
            'new': 4,
            'refurbished': 3,
            'used_like_new': 2,
            'used_good': 1,
            'used_acceptable': 0
        }
        features['condition_encoded'] = condition_map.get(condition, 4)

        return features

    # ========== SHIPPING & WARRANTY FEATURES (4 features) ==========

    def extract_logistics_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract shipping and warranty features"""
        features = {}

        shipping = record.get('shipping', {})
        warranty = record.get('warranty', {})

        # 1. Has free shipping
        features['has_free_shipping'] = 1 if shipping.get('is_free', False) else 0

        # 2. Shipping cost
        features['shipping_cost'] = shipping.get('cost', 0)

        # 3. Has warranty
        features['has_warranty'] = 1 if warranty.get('has_warranty', False) else 0

        # 4. Warranty duration (in months)
        warranty_duration = warranty.get('duration', 0)
        if warranty.get('unit') == 'years':
            warranty_duration = warranty_duration * 12
        features['warranty_months'] = warranty_duration

        return features

    # ========== VISUAL FEATURES (2 features) ==========

    def extract_visual_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract image-related features"""
        features = {}

        # 1. Image count
        features['image_count'] = record.get('image_count', 0)

        # 2. Has main image
        features['has_main_image'] = 1 if record.get('main_image') else 0

        return features

    # ========== COLOR FEATURES (2 features) ==========

    def extract_color_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract color variety features"""
        features = {}

        # 1. Color options count
        features['color_options_count'] = record.get('color_count', 0)

        # 2. Has multiple colors
        features['has_multiple_colors'] = 1 if record.get('color_count', 0) > 1 else 0

        return features

    # ========== COMPOSITE ML FEATURES (12+ features) ==========

    def extract_composite_features(self, record: Dict[str, Any], basic_features: Dict[str, Any]) -> Dict[str, Any]:
        """Extract composite features combining multiple signals"""
        features = {}

        # 1. Overall quality score
        # Combines rating, reviews, condition, and brand
        rating_score = basic_features.get('rating_normalized', 0)
        review_score = min(basic_features.get('reviews_log', 0) / 5, 1.0)
        condition_score = basic_features.get('condition_encoded', 0) / 4
        brand_score = basic_features.get('is_major_brand', 0)

        features['quality_score'] = (
            rating_score * 0.4 +
            review_score * 0.2 +
            condition_score * 0.2 +
            brand_score * 0.2
        )

        # 2. Value for money score
        # Good quality at low price
        features['value_for_money'] = (
            features['quality_score'] *
            basic_features.get('affordability_score', 0.5)
        )

        # 3. Recommendation confidence
        # How confident we are to recommend this product
        features['recommendation_confidence'] = (
            basic_features.get('rating_confidence', 0) * 0.5 +
            basic_features.get('popularity_score', 0) / 20 * 0.3 +
            features['quality_score'] * 0.2
        )

        # 4. Urgency score (stock + discount)
        stock_urgency = 1.0 if basic_features.get('stock_level', 0) == 1 else 0.5
        discount_urgency = basic_features.get('discount_tier', 0) / 3
        features['urgency_score'] = (stock_urgency + discount_urgency) / 2

        # 5. Premium indicator
        # High price + high rating + major brand
        is_premium = (
            basic_features.get('price_category', 0) >= 2 and
            basic_features.get('rating_category', 0) >= 3 and
            basic_features.get('is_major_brand', 0) == 1
        )
        features['is_premium_product'] = 1 if is_premium else 0

        # 6. Deal score (good discount + in stock)
        features['deal_score'] = (
            basic_features.get('discount_tier', 0) / 3 * 0.6 +
            basic_features.get('availability_encoded', 0) / 2 * 0.4
        )

        # 7. Completeness score (how complete is product info)
        completeness = (
            (1 if basic_features.get('has_detailed_description', 0) else 0) +
            (1 if basic_features.get('specifications_count', 0) > 5 else 0) +
            (1 if basic_features.get('image_count', 0) > 2 else 0) +
            (1 if basic_features.get('features_count', 0) > 3 else 0)
        ) / 4
        features['info_completeness_score'] = completeness

        # 8. Customer satisfaction proxy
        # Rating weighted by number of reviews
        features['satisfaction_proxy'] = basic_features.get('rating_confidence', 0)

        # 9. New product indicator
        # High price, new condition, low reviews
        is_new_product = (
            basic_features.get('condition_encoded', 0) == 4 and
            basic_features.get('number_of_reviews', 0) < 10
        )
        features['is_new_product'] = 1 if is_new_product else 0

        # 10. Best seller indicator
        # High reviews + high rating
        is_bestseller = (
            record.get('number_of_reviews', 0) > 50 and
            record.get('rating', 0) >= 4.0
        )
        features['is_bestseller'] = 1 if is_bestseller else 0

        # 11. Budget friendly indicator
        features['is_budget_friendly'] = 1 if basic_features.get('price_category', 0) == 0 else 0

        # 12. Purchase readiness score
        # In stock + has warranty + free shipping + good rating
        purchase_ready = (
            basic_features.get('availability_encoded', 0) / 2 * 0.3 +
            basic_features.get('has_free_shipping', 0) * 0.2 +
            basic_features.get('has_warranty', 0) * 0.2 +
            basic_features.get('rating_normalized', 0) * 0.3
        )
        features['purchase_readiness'] = purchase_ready

        # 13. Thompson Sampling hints (for future RL)
        # Initial alpha/beta parameters based on reviews and ratings
        num_reviews = record.get('number_of_reviews', 0)
        rating = record.get('rating', 0)

        if num_reviews > 0:
            # Convert 5-star rating to success/failure counts
            success_rate = rating / 5.0
            features['thompson_alpha_hint'] = int(num_reviews * success_rate) + 1
            features['thompson_beta_hint'] = int(num_reviews * (1 - success_rate)) + 1
        else:
            features['thompson_alpha_hint'] = 1
            features['thompson_beta_hint'] = 1

        # 14. Conversion probability estimate
        # Estimated likelihood user will purchase
        features['conversion_probability'] = (
            basic_features.get('availability_encoded', 0) / 2 * 0.25 +
            basic_features.get('rating_normalized', 0) * 0.25 +
            basic_features.get('value_indicator', 0) * 0.25 +
            features['info_completeness_score'] * 0.25
        )

        return features

    def engineer_features(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Engineer all features for a single record"""
        # Start with original record
        featured_record = record.copy()

        # Extract all feature groups
        text_features = self.extract_text_features(record)
        price_features = self.extract_price_features(record)
        rating_features = self.extract_rating_features(record)
        categorical_features = self.extract_categorical_features(record)
        inventory_features = self.extract_inventory_features(record)
        logistics_features = self.extract_logistics_features(record)
        visual_features = self.extract_visual_features(record)
        color_features = self.extract_color_features(record)

        # Combine all basic features
        all_basic_features = {
            **text_features,
            **price_features,
            **rating_features,
            **categorical_features,
            **inventory_features,
            **logistics_features,
            **visual_features,
            **color_features
        }

        # Extract composite features
        composite_features = self.extract_composite_features(record, all_basic_features)

        # Add all features to record
        featured_record['ml_features'] = {
            **all_basic_features,
            **composite_features
        }

        return featured_record

    def process(self):
        """Main feature engineering pipeline"""
        logger.info("Starting feature engineering process")

        # Load cleaned data
        data = self.load_data()

        # Compute dataset statistics
        self.compute_dataset_stats(data)

        # Engineer features for each record
        featured_data = []
        for i, record in enumerate(data):
            try:
                featured_record = self.engineer_features(record)
                featured_data.append(featured_record)

                if (i + 1) % 5000 == 0:
                    logger.info(f"Processed {i + 1}/{len(data)} records")

            except Exception as e:
                logger.error(f"Error processing record {i}: {str(e)}")
                # Keep original record without features
                featured_data.append(record)

        # Count total features
        if featured_data and 'ml_features' in featured_data[0]:
            feature_count = len(featured_data[0]['ml_features'])
            logger.info(f"Generated {feature_count} features per product")

        # Save featured data
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving featured data to {self.output_path}")
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(featured_data, f, ensure_ascii=False, indent=2)

        logger.info("=" * 60)
        logger.info("FEATURE ENGINEERING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total products: {len(featured_data)}")
        logger.info(f"Features per product: {feature_count}")
        logger.info(f"Output: {self.output_path}")
        logger.info("=" * 60)

        return featured_data


def main():
    """Main execution function"""
    # Define paths
    input_path = "data/processed/products_cleaned.json"
    output_path = "data/features/products_with_features.json"

    # Create feature engineer instance
    engineer = FeatureEngineer(input_path, output_path)

    # Process data
    featured_data = engineer.process()

    logger.info(f"✓ Feature engineering complete! ML-ready dataset saved to {output_path}")
    logger.info(f"✓ Ready for CLIP embeddings and Qdrant insertion")

    return featured_data


if __name__ == "__main__":
    main()
