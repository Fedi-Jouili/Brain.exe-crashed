"""
Data Cleaning Script for Tunisian Electronics Dataset
Processes tunisian_electronics_50k.json to clean, standardize, and validate product data
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Set
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans and standardizes the Tunisian electronics dataset"""

    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.stats = {
            'total_records': 0,
            'cleaned_records': 0,
            'duplicates_removed': 0,
            'invalid_records': 0,
            'field_corrections': {}
        }

    def load_data(self) -> List[Dict[str, Any]]:
        """Load JSON data from file"""
        logger.info(f"Loading data from {self.input_path}")
        with open(self.input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.stats['total_records'] = len(data)
        logger.info(f"Loaded {len(data)} records")
        return data

    def clean_text(self, text: Any) -> str:
        """Clean and standardize text fields"""
        if text is None:
            return ""

        text = str(text).strip()

        # Fix common encoding issues
        text = text.replace('Ã©', 'é')
        text = text.replace('Ã¨', 'è')
        text = text.replace('Ã´', 'ô')
        text = text.replace('Ã ', 'à')
        text = text.replace('Ã§', 'ç')
        text = text.replace('\u0027', "'")

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def normalize_price(self, price: Any) -> float:
        """Normalize and validate price values"""
        try:
            price = float(price)
            return round(price, 2) if price > 0 else 0.0
        except (ValueError, TypeError):
            return 0.0

    def normalize_rating(self, rating: Any) -> float:
        """Normalize rating to 0-5 scale"""
        try:
            rating = float(rating)
            # Ensure rating is between 0 and 5
            return round(max(0.0, min(5.0, rating)), 1)
        except (ValueError, TypeError):
            return 0.0

    def normalize_availability(self, availability: str) -> str:
        """Standardize availability status"""
        if not availability:
            return "unknown"

        availability = self.clean_text(availability.lower())

        # Map various formats to standard values
        if any(x in availability for x in ['disponible', 'en stock', 'available', 'in stock']):
            return "in_stock"
        elif any(x in availability for x in ['bientôt', 'bientot', 'soon', 'pre-commande', 'precommande']):
            return "coming_soon"
        elif any(x in availability for x in ['rupture', 'épuisé', 'epuise', 'out of stock']):
            return "out_of_stock"
        else:
            return "unknown"

    def normalize_condition(self, condition: str) -> str:
        """Standardize product condition"""
        if not condition:
            return "new"

        condition = self.clean_text(condition.lower())

        if any(x in condition for x in ['neuf', 'new', 'nouveau']):
            return "new"
        elif any(x in condition for x in ['reconditionné', 'reconditionne', 'refurbished']):
            return "refurbished"
        elif 'occasion' in condition:
            if 'comme neuf' in condition or 'excellent' in condition:
                return "used_like_new"
            elif 'bon' in condition or 'good' in condition:
                return "used_good"
            else:
                return "used_acceptable"
        else:
            return "new"

    def normalize_shipping(self, shipping: str) -> Dict[str, Any]:
        """Parse shipping information"""
        if not shipping:
            return {"type": "standard", "cost": 0.0, "is_free": False}

        shipping = self.clean_text(shipping.lower())

        is_free = any(x in shipping for x in ['gratuit', 'free', 'offert'])

        # Extract shipping cost if present
        cost_match = re.search(r'(\d+(?:\.\d+)?)\s*tnd', shipping)
        cost = float(cost_match.group(1)) if cost_match else 0.0

        # Determine shipping type
        if 'express' in shipping or 'rapide' in shipping:
            ship_type = "express"
        elif 'standard' in shipping:
            ship_type = "standard"
        else:
            ship_type = "standard" if not is_free else "free"

        return {
            "type": ship_type,
            "cost": cost,
            "is_free": is_free
        }

    def normalize_warranty(self, warranty: str) -> Dict[str, Any]:
        """Parse warranty information"""
        if not warranty:
            return {"duration": 0, "unit": "months", "has_warranty": False}

        warranty = self.clean_text(warranty.lower())

        # Extract duration
        year_match = re.search(r'(\d+)\s*an', warranty)
        month_match = re.search(r'(\d+)\s*mois', warranty)

        if year_match:
            duration = int(year_match.group(1))
            unit = "years"
        elif month_match:
            duration = int(month_match.group(1))
            unit = "months"
        else:
            duration = 0
            unit = "months"

        return {
            "duration": duration,
            "unit": unit,
            "has_warranty": duration > 0
        }

    def normalize_colors(self, color: Any, colors_available: Any) -> Dict[str, Any]:
        """Normalize color information"""
        primary_color = self.clean_text(color) if color else ""

        # Handle colors_available
        if isinstance(colors_available, list):
            available_colors = [self.clean_text(c) for c in colors_available if c]
        else:
            available_colors = []

        # Ensure primary color is in available colors
        if primary_color and primary_color not in available_colors:
            available_colors.insert(0, primary_color)

        return {
            "primary": primary_color,
            "available": available_colors,
            "count": len(available_colors)
        }

    def clean_specifications(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize specifications"""
        if not isinstance(specs, dict):
            return {}

        cleaned_specs = {}
        for key, value in specs.items():
            # Clean key
            clean_key = key.strip().lower().replace(' ', '_')

            # Clean value
            if isinstance(value, str):
                clean_value = self.clean_text(value)
            else:
                clean_value = value

            cleaned_specs[clean_key] = clean_value

        return cleaned_specs

    def clean_features(self, features: Any) -> List[str]:
        """Clean and deduplicate features list"""
        if not isinstance(features, list):
            return []

        cleaned_features = []
        seen = set()

        for feature in features:
            if feature:
                clean_feature = self.clean_text(feature)
                if clean_feature and clean_feature.lower() not in seen:
                    cleaned_features.append(clean_feature)
                    seen.add(clean_feature.lower())

        return cleaned_features

    def clean_images(self, images: Any, main_image: Any) -> Dict[str, Any]:
        """Clean and organize image URLs"""
        # Clean main image
        main = self.clean_text(main_image) if main_image else ""

        # Clean additional images
        if isinstance(images, list):
            additional = [self.clean_text(img) for img in images if img]
        else:
            additional = []

        # Remove duplicates
        all_images = list(dict.fromkeys([main] + additional if main else additional))

        return {
            "main": main,
            "additional": additional,
            "all": all_images,
            "count": len(all_images)
        }

    def validate_record(self, record: Dict[str, Any]) -> bool:
        """Validate that a record has minimum required fields"""
        required_fields = ['id', 'name', 'category', 'price_TND']

        for field in required_fields:
            if field not in record or not record[field]:
                return False

        # Validate price is positive
        if record.get('price_TND', 0) <= 0:
            return False

        return True

    def clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single product record"""
        cleaned = {}

        # Basic fields
        cleaned['id'] = self.clean_text(record.get('id', ''))
        cleaned['name'] = self.clean_text(record.get('name', ''))
        cleaned['category'] = self.clean_text(record.get('category', ''))
        cleaned['subcategory'] = self.clean_text(record.get('subcategory', ''))
        cleaned['brand'] = self.clean_text(record.get('brand', ''))
        cleaned['model'] = self.clean_text(record.get('model', ''))
        cleaned['sku'] = self.clean_text(record.get('sku', ''))

        # Price fields
        cleaned['price_TND'] = self.normalize_price(record.get('price_TND', 0))
        cleaned['original_price_TND'] = self.normalize_price(record.get('original_price_TND', 0))
        cleaned['currency'] = 'TND'

        # Calculate discount if not present or incorrect
        if cleaned['original_price_TND'] > 0 and cleaned['price_TND'] > 0:
            discount = ((cleaned['original_price_TND'] - cleaned['price_TND']) / cleaned['original_price_TND']) * 100
            cleaned['discount_percentage'] = round(max(0, discount), 2)
        else:
            cleaned['discount_percentage'] = 0.0

        # Stock and availability
        cleaned['availability'] = self.normalize_availability(record.get('availability', ''))
        cleaned['condition'] = self.normalize_condition(record.get('condition', ''))
        cleaned['stock_quantity'] = max(0, int(record.get('stock_quantity', 0)))

        # Colors
        color_info = self.normalize_colors(record.get('color'), record.get('colors_available'))
        cleaned['color'] = color_info['primary']
        cleaned['colors_available'] = color_info['available']
        cleaned['color_count'] = color_info['count']

        # Specifications
        cleaned['specifications'] = self.clean_specifications(record.get('specifications', {}))

        # Text fields
        cleaned['description'] = self.clean_text(record.get('description', ''))
        cleaned['features'] = self.clean_features(record.get('features', []))

        # Images
        image_info = self.clean_images(record.get('images'), record.get('main_image'))
        cleaned['main_image'] = image_info['main']
        cleaned['images'] = image_info['additional']
        cleaned['image_count'] = image_info['count']

        # Ratings and reviews
        cleaned['rating'] = self.normalize_rating(record.get('rating', 0))
        cleaned['number_of_reviews'] = max(0, int(record.get('number_of_reviews', 0)))

        # Seller info
        cleaned['seller'] = self.clean_text(record.get('seller', ''))

        # Warranty
        warranty_info = self.normalize_warranty(record.get('warranty', ''))
        cleaned['warranty'] = warranty_info

        # Shipping
        shipping_info = self.normalize_shipping(record.get('shipping', ''))
        cleaned['shipping'] = shipping_info

        # Timestamps
        cleaned['created_at'] = record.get('created_at', '')
        cleaned['updated_at'] = record.get('updated_at', '')

        return cleaned

    def remove_duplicates(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate records based on ID"""
        seen_ids: Set[str] = set()
        unique_records = []

        for record in records:
            record_id = record.get('id', '')
            if record_id and record_id not in seen_ids:
                seen_ids.add(record_id)
                unique_records.append(record)
            else:
                self.stats['duplicates_removed'] += 1

        logger.info(f"Removed {self.stats['duplicates_removed']} duplicate records")
        return unique_records

    def process(self):
        """Main processing pipeline"""
        logger.info("Starting data cleaning process")

        # Load data
        raw_data = self.load_data()

        # Clean each record
        cleaned_data = []
        for i, record in enumerate(raw_data):
            try:
                cleaned_record = self.clean_record(record)

                # Validate record
                if self.validate_record(cleaned_record):
                    cleaned_data.append(cleaned_record)
                    self.stats['cleaned_records'] += 1
                else:
                    self.stats['invalid_records'] += 1
                    logger.warning(f"Invalid record at index {i}: {cleaned_record.get('id', 'NO_ID')}")

            except Exception as e:
                self.stats['invalid_records'] += 1
                logger.error(f"Error processing record at index {i}: {str(e)}")

        # Remove duplicates
        cleaned_data = self.remove_duplicates(cleaned_data)

        # Save cleaned data
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving cleaned data to {self.output_path}")
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

        # Print statistics
        self.print_stats()

        return cleaned_data

    def print_stats(self):
        """Print cleaning statistics"""
        logger.info("=" * 60)
        logger.info("DATA CLEANING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total records: {self.stats['total_records']}")
        logger.info(f"Successfully cleaned: {self.stats['cleaned_records']}")
        logger.info(f"Invalid records: {self.stats['invalid_records']}")
        logger.info(f"Duplicates removed: {self.stats['duplicates_removed']}")
        logger.info(f"Final dataset size: {self.stats['cleaned_records'] - self.stats['duplicates_removed']}")
        logger.info("=" * 60)


def main():
    """Main execution function"""
    # Define paths
    input_path = "data/raw/tunisian_electronics_50k.json"
    output_path = "data/processed/products_cleaned.json"

    # Create cleaner instance
    cleaner = DataCleaner(input_path, output_path)

    # Process data
    cleaned_data = cleaner.process()

    logger.info(f"✓ Data cleaning complete! Cleaned dataset saved to {output_path}")
    logger.info(f"✓ Ready for feature engineering")

    return cleaned_data


if __name__ == "__main__":
    main()
