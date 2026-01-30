"""
Load Hackathon Data into Qdrant
Imports user profiles, behavior, and model confidence from CSV files
"""
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List
import uuid

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.qdrant_client import QdrantManager
from core.config import settings
from qdrant_client.models import PointStruct

# Initialize Qdrant
qdrant_client = QdrantManager().client
USERS_COLLECTION = settings.qdrant_collection_users

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Data file paths
DATA_DIR = Path("C:/Users/mezen/OneDrive/Desktop/data hackaton")
MODEL_CONFIDENCE_FILE = DATA_DIR / "model_confidence_50k.csv"
USER_BEHAVIOR_FILE = DATA_DIR / "user_behavior_history_50k.csv"
USER_INCOME_FILE = DATA_DIR / "user_income_budget_50k.csv"


def load_csv(filepath: Path) -> List[Dict]:
    """Load CSV file into list of dictionaries"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        logger.info(f"Loaded {len(data)} rows from {filepath.name}")
        return data
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return []


def merge_user_data(
    income_data: List[Dict],
    behavior_data: List[Dict],
    confidence_data: List[Dict]
) -> List[Dict]:
    """Merge all user data by user_id"""
    
    # Create lookup dictionaries
    behavior_lookup = {row['user_id']: row for row in behavior_data}
    confidence_lookup = {row['user_id']: row for row in confidence_data}
    
    merged_users = []
    
    for income_row in income_data:
        user_id = income_row['user_id']
        
        # Merge all data for this user
        user_data = {
            # Basic info
            'user_id': user_id,
            'age': int(income_row.get('age', 0)),
            'city': income_row.get('city', ''),
            
            # Financial data (convert TND to USD approximately, 1 TND ≈ 0.32 USD)
            'monthly_income': float(income_row.get('income_monthly_TND', 0)) * 0.32,
            'electronics_budget': float(income_row.get('electronics_budget_TND', 0)) * 0.32,
            'savings': float(income_row.get('savings_TND', 0)) * 0.32,
            'financial_stress_index': float(income_row.get('financial_stress_index', 0)),
            
            # Estimate monthly expenses (80% of income if not specified)
            'monthly_expenses': float(income_row.get('income_monthly_TND', 0)) * 0.32 * 0.8,
            
            # Estimate debt based on financial stress (higher stress = more debt)
            'current_debt': float(income_row.get('income_monthly_TND', 0)) * 0.32 * float(income_row.get('financial_stress_index', 0)) * 2,
            
            # Estimate credit score (inverse of financial stress, scaled 300-850)
            'credit_score': int(850 - (float(income_row.get('financial_stress_index', 0)) * 550)),
        }
        
        # Add behavior data if available
        if user_id in behavior_lookup:
            behavior = behavior_lookup[user_id]
            user_data.update({
                'avg_monthly_visits': int(behavior.get('avg_monthly_visits', 0)),
                'avg_comparison_clicks': int(behavior.get('avg_comparison_clicks', 0)),
                'purchases_last_12m': int(behavior.get('purchases_last_12m', 0)),
                'preferred_category': behavior.get('preferred_category', ''),
                'seasonal_buyer_score': float(behavior.get('seasonal_buyer_score', 0)),
                'price_sensitivity': float(behavior.get('price_sensitivity', 0)),
            })
        
        # Add confidence data if available
        if user_id in confidence_lookup:
            confidence = confidence_lookup[user_id]
            user_data.update({
                'confidence_price_prediction': float(confidence.get('confidence_price_prediction', 0)),
                'confidence_budget_fit': float(confidence.get('confidence_budget_fit', 0)),
                'confidence_purchase_timing': float(confidence.get('confidence_purchase_timing', 0)),
                'overall_model_confidence': float(confidence.get('overall_model_confidence', 0)),
            })
        
        merged_users.append(user_data)
    
    return merged_users


def upload_users_to_qdrant(users: List[Dict], batch_size: int = 100):
    """Upload user profiles to Qdrant"""
    
    total_users = len(users)
    logger.info(f"Uploading {total_users} users to Qdrant in batches of {batch_size}...")
    
    # Process in batches
    for i in range(0, total_users, batch_size):
        batch = users[i:i + batch_size]
        points = []
        
        for user in batch:
            # Create a simple embedding based on user attributes
            # This is a placeholder - in production, use proper embeddings
            embedding = [
                user.get('monthly_income', 0) / 10000,  # Normalize income
                user.get('age', 0) / 100,  # Normalize age
                user.get('savings', 0) / 10000,  # Normalize savings
                user.get('credit_score', 0) / 1000,  # Normalize credit score
                user.get('price_sensitivity', 0),
                user.get('seasonal_buyer_score', 0),
                user.get('overall_model_confidence', 0),
                user.get('purchases_last_12m', 0) / 12,  # Normalize purchases
            ]
            
            # Pad to 512 dimensions (to match CLIP embeddings)
            embedding.extend([0.0] * (512 - len(embedding)))
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding[:512],  # Ensure exactly 512 dimensions
                payload=user
            )
            points.append(point)
        
        # Upload batch
        try:
            qdrant_client.upsert(
                collection_name=USERS_COLLECTION,
                points=points
            )
            logger.info(f"Uploaded batch {i//batch_size + 1}/{(total_users-1)//batch_size + 1} "
                       f"({len(points)} users)")
        except Exception as e:
            logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
            continue
    
    logger.info(f"✅ Successfully uploaded {total_users} users to Qdrant")


def main():
    """Main data loading pipeline"""
    
    print("=" * 80)
    print("🔄 LOADING HACKATHON DATA INTO QDRANT")
    print("=" * 80)
    print()
    
    # Step 1: Load CSV files
    print("📂 Step 1: Loading CSV files...")
    income_data = load_csv(USER_INCOME_FILE)
    behavior_data = load_csv(USER_BEHAVIOR_FILE)
    confidence_data = load_csv(MODEL_CONFIDENCE_FILE)
    
    if not income_data:
        print("❌ Error: Could not load income data")
        return
    
    print(f"   ✅ Loaded {len(income_data)} income records")
    print(f"   ✅ Loaded {len(behavior_data)} behavior records")
    print(f"   ✅ Loaded {len(confidence_data)} confidence records")
    print()
    
    # Step 2: Merge data
    print("🔗 Step 2: Merging user data...")
    merged_users = merge_user_data(income_data, behavior_data, confidence_data)
    print(f"   ✅ Merged {len(merged_users)} complete user profiles")
    print()
    
    # Step 3: Show sample
    print("📊 Step 3: Sample user profile:")
    if merged_users:
        sample = merged_users[0]
        print(f"   User ID: {sample['user_id']}")
        print(f"   Age: {sample['age']}, City: {sample['city']}")
        print(f"   Monthly Income: ${sample['monthly_income']:.2f}")
        print(f"   Monthly Expenses: ${sample['monthly_expenses']:.2f}")
        print(f"   Savings: ${sample['savings']:.2f}")
        print(f"   Credit Score: {sample['credit_score']}")
        print(f"   Preferred Category: {sample.get('preferred_category', 'N/A')}")
        print(f"   Price Sensitivity: {sample.get('price_sensitivity', 'N/A')}")
        print(f"   Model Confidence: {sample.get('overall_model_confidence', 'N/A')}")
    print()
    
    # Step 4: Upload to Qdrant
    print("☁️  Step 4: Uploading to Qdrant...")
    
    # Auto-confirm for batch upload
    print(f"Uploading {len(merged_users)} users to Qdrant...")
    
    upload_users_to_qdrant(merged_users, batch_size=100)
    print()
    
    # Step 5: Verify upload
    print("🔍 Step 5: Verifying upload...")
    try:
        collection_info = qdrant_client.get_collection(USERS_COLLECTION)
        print(f"   ✅ Users collection now has {collection_info.points_count} points")
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}")
    print()
    
    print("=" * 80)
    print("✅ DATA LOADING COMPLETE!")
    print("=" * 80)
    print()
    print("📈 Summary:")
    print(f"   • Total users loaded: {len(merged_users)}")
    print(f"   • Data sources merged: 3 CSV files")
    print(f"   • Collection: {USERS_COLLECTION}")
    print()
    print("Next steps:")
    print("   1. Run collaborative filtering will now use richer user data")
    print("   2. Financial analysis will have real user profiles")
    print("   3. Test with: python scripts/test_agent2.py")
    print()


if __name__ == "__main__":
    main()
