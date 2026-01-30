"""
Initialize Qdrant collections and Redis state
Run this once before starting the application
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qdrant_client import qdrant_manager
from core.redis_client import redis_manager
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_qdrant():
    """Initialize all Qdrant collections"""
    logger.info("🔧 Initializing Qdrant collections...")
    
    try:
        # Health check
        if not qdrant_manager.health_check():
            logger.error("❌ Qdrant is not healthy. Check connection.")
            return False
        
        # Create collections
        qdrant_manager.create_collections()
        
        # Verify collections
        collections = [
            settings.qdrant_collection_products,
            settings.qdrant_collection_users,
            settings.qdrant_collection_financial_kb,
            settings.qdrant_collection_transactions,
        ]
        
        for collection_name in collections:
            info = qdrant_manager.get_collection_info(collection_name)
            logger.info(f"✅ Collection '{collection_name}': {info.points_count} points")
        
        logger.info("✅ Qdrant initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing Qdrant: {e}", exc_info=True)
        return False


def init_redis():
    """Initialize Redis (clear and verify)"""
    logger.info("🔧 Initializing Redis...")
    
    try:
        # Health check
        if not redis_manager.health_check():
            logger.error("❌ Redis is not healthy. Check connection.")
            return False
        
        # Get initial stats
        stats = redis_manager.get_cache_stats()
        logger.info(f"📊 Redis stats: {stats}")
        
        memory = redis_manager.get_memory_info()
        logger.info(f"💾 Memory usage: {memory}")
        
        logger.info("✅ Redis initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing Redis: {e}", exc_info=True)
        return False


def main():
    """Run all initialization"""
    logger.info("=" * 60)
    logger.info("🚀 PriceSense - Database Initialization")
    logger.info("=" * 60)
    
    # Check configuration
    logger.info(f"📍 Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    logger.info(f"📍 Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info("")
    
    # Initialize Qdrant
    qdrant_success = init_qdrant()
    logger.info("")
    
    # Initialize Redis
    redis_success = init_redis()
    logger.info("")
    
    # Summary
    logger.info("=" * 60)
    if qdrant_success and redis_success:
        logger.info("✅ All databases initialized successfully!")
        logger.info("🎯 Next step: Run seed_data.py to load sample data")
    else:
        logger.error("❌ Initialization failed. Check logs above.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
