"""
Clustering Artifacts Validation Tests

Tests to ensure clustering artifacts are valid and production-ready.
Run in CI to prevent broken clustering data from reaching production.
"""
import sys
import json
from pathlib import Path
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators.cluster_validator import (
    validate_clustered_products,
    validate_single_product,
    get_validation_summary,
    ClusterValidationError
)

# Path to clustering artifacts
PRODUCTS_FILE = Path(__file__).parent.parent / "data" / "products_clustered.json"
EXPECTED_N_CLUSTERS = 10


class TestClusteringArtifacts:
    """Test suite for clustering artifacts validation"""

    @pytest.fixture(scope="class")
    def products(self):
        """Load clustered products from JSON file"""
        if not PRODUCTS_FILE.exists():
            pytest.skip(f"Clustering artifacts not found at {PRODUCTS_FILE}")

        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_artifacts_file_exists(self):
        """Test that products_clustered.json exists"""
        assert PRODUCTS_FILE.exists(), \
            f"Clustering artifacts not found at {PRODUCTS_FILE}. Run clustering script first."

    def test_artifacts_is_valid_json(self):
        """Test that artifacts file is valid JSON"""
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, list), "Products must be a JSON array"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in clustering artifacts: {e}")

    def test_has_products(self, products):
        """Test that there are products in the file"""
        assert len(products) > 0, "No products found in clustering artifacts"
        assert len(products) >= 50, f"Expected at least 50 products, got {len(products)}"

    def test_all_products_have_product_id(self, products):
        """Test that all products have product_id field"""
        for idx, product in enumerate(products):
            assert 'product_id' in product, \
                f"Product at index {idx} missing 'product_id'"
            assert isinstance(product['product_id'], str), \
                f"Product at index {idx}: product_id must be string"
            assert len(product['product_id']) > 0, \
                f"Product at index {idx}: product_id cannot be empty"

    def test_product_id_uniqueness(self, products):
        """Test that all product_ids are unique"""
        product_ids = [p['product_id'] for p in products]
        duplicates = [pid for pid in product_ids if product_ids.count(pid) > 1]
        assert len(duplicates) == 0, \
            f"Duplicate product_ids found: {set(duplicates)}"

    def test_all_products_have_embedding(self, products):
        """Test that all products have embedding field"""
        for product in products:
            assert 'embedding' in product, \
                f"Product {product.get('product_id', 'unknown')} missing 'embedding'"

    def test_embeddings_are_valid_lists(self, products):
        """Test that embeddings are lists"""
        for product in products:
            embedding = product['embedding']
            assert isinstance(embedding, list), \
                f"Product {product['product_id']}: embedding must be list, got {type(embedding).__name__}"

    def test_embeddings_have_correct_dimension(self, products):
        """CRITICAL: Test that all embeddings are 512-dimensional"""
        errors = []
        for product in products:
            embedding = product['embedding']
            if len(embedding) != 512:
                errors.append(
                    f"Product {product['product_id']}: embedding has {len(embedding)} dimensions, expected 512"
                )

        assert len(errors) == 0, \
            f"Embedding dimension errors:\n" + "\n".join(errors[:5])

    def test_embeddings_contain_only_numbers(self, products):
        """Test that embeddings contain only numeric values"""
        for product in products:
            embedding = product['embedding']
            assert all(isinstance(x, (int, float)) for x in embedding), \
                f"Product {product['product_id']}: embedding contains non-numeric values"

    def test_embeddings_no_nan_or_inf(self, products):
        """Test that embeddings don't contain NaN or Infinity"""
        for product in products:
            embedding = product['embedding']

            # Check for NaN
            has_nan = any(x != x for x in embedding)  # NaN != NaN
            assert not has_nan, \
                f"Product {product['product_id']}: embedding contains NaN values"

            # Check for Infinity
            has_inf = any(abs(x) == float('inf') for x in embedding)
            assert not has_inf, \
                f"Product {product['product_id']}: embedding contains Infinity values"

    def test_all_products_have_cluster_id(self, products):
        """Test that all products have cluster_id field"""
        for product in products:
            assert 'cluster_id' in product, \
                f"Product {product.get('product_id', 'unknown')} missing 'cluster_id'"

    def test_cluster_ids_are_integers(self, products):
        """Test that cluster_ids are integers"""
        for product in products:
            cluster_id = product['cluster_id']
            assert isinstance(cluster_id, int), \
                f"Product {product['product_id']}: cluster_id must be int, got {type(cluster_id).__name__}"

    def test_cluster_ids_in_valid_range(self, products):
        """CRITICAL: Test that cluster_ids are in valid range [0, N_CLUSTERS-1]"""
        errors = []
        for product in products:
            cluster_id = product['cluster_id']
            if cluster_id < 0 or cluster_id >= EXPECTED_N_CLUSTERS:
                errors.append(
                    f"Product {product['product_id']}: cluster_id {cluster_id} out of range [0, {EXPECTED_N_CLUSTERS-1}]"
                )

        assert len(errors) == 0, \
            f"Cluster ID range errors:\n" + "\n".join(errors[:5])

    def test_at_least_two_products_per_cluster(self, products):
        """SOFT: Warn if any cluster has less than 2 products"""
        cluster_counts = {}
        for product in products:
            cluster_id = product['cluster_id']
            cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1

        sparse_clusters = [
            (cid, count) for cid, count in cluster_counts.items() if count < 2
        ]

        if sparse_clusters:
            pytest.skip(
                f"Warning: Some clusters have < 2 products: {sparse_clusters}. "
                "This may cause poor alternative recommendations."
            )

    def test_all_clusters_represented(self, products):
        """Test that all expected clusters have at least one product"""
        cluster_ids = {product['cluster_id'] for product in products}
        expected_clusters = set(range(EXPECTED_N_CLUSTERS))
        missing_clusters = expected_clusters - cluster_ids

        assert len(missing_clusters) == 0, \
            f"Missing clusters: {sorted(missing_clusters)}"

    def test_validator_passes(self, products):
        """Test that the full validator passes"""
        try:
            validate_clustered_products(products, expected_n_clusters=EXPECTED_N_CLUSTERS)
        except ClusterValidationError as e:
            pytest.fail(f"Clustering validation failed: {e}")

    def test_validation_summary(self, products):
        """Test validation summary generation"""
        summary = get_validation_summary(products)

        assert summary['total_products'] == len(products)
        assert summary['valid_products'] > 0
        assert summary['invalid_products'] == 0, \
            f"Found {summary['invalid_products']} invalid products"
        assert summary['missing_embeddings'] == 0, \
            f"Found {summary['missing_embeddings']} products with missing embeddings"
        assert summary['invalid_embeddings'] == 0, \
            f"Found {summary['invalid_embeddings']} products with invalid embeddings"
        assert summary['missing_cluster_id'] == 0, \
            f"Found {summary['missing_cluster_id']} products with missing cluster_id"
        assert summary['invalid_cluster_id'] == 0, \
            f"Found {summary['invalid_cluster_id']} products with invalid cluster_id"


class TestSingleProductValidation:
    """Test single product validation helper"""

    def test_valid_product(self):
        """Test that a valid product passes validation"""
        product = {
            'product_id': 'TEST_001',
            'embedding': [0.1] * 512,
            'cluster_id': 5
        }
        assert validate_single_product(product) == True

    def test_missing_product_id(self):
        """Test that missing product_id fails validation"""
        product = {
            'embedding': [0.1] * 512,
            'cluster_id': 5
        }
        assert validate_single_product(product) == False

    def test_missing_embedding(self):
        """Test that missing embedding fails validation"""
        product = {
            'product_id': 'TEST_001',
            'cluster_id': 5
        }
        assert validate_single_product(product) == False

    def test_missing_cluster_id(self):
        """Test that missing cluster_id fails validation"""
        product = {
            'product_id': 'TEST_001',
            'embedding': [0.1] * 512
        }
        assert validate_single_product(product) == False

    def test_wrong_embedding_dimension(self):
        """Test that wrong embedding dimension fails validation"""
        product = {
            'product_id': 'TEST_001',
            'embedding': [0.1] * 256,  # Wrong dimension
            'cluster_id': 5
        }
        assert validate_single_product(product) == False

    def test_invalid_cluster_id_type(self):
        """Test that non-integer cluster_id fails validation"""
        product = {
            'product_id': 'TEST_001',
            'embedding': [0.1] * 512,
            'cluster_id': "5"  # String instead of int
        }
        assert validate_single_product(product) == False


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
