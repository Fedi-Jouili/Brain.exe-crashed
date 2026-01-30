"""
Test FastAPI endpoints

Run the API server first:
    cd backend
    python main.py

Then run these tests:
    python scripts/test_api.py
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check endpoint"""
    print("=" * 80)
    print("🧪 TEST 1: HEALTH CHECK")
    print("=" * 80)
    print()

    response = requests.get(f"{BASE_URL}/api/health")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Overall Status: {data['status']}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Version: {data['version']}")
        print()
        print("Services:")
        for service, status in data['services'].items():
            emoji = "✅" if "healthy" in status else "❌"
            print(f"  {emoji} {service}: {status}")
        print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_search_simple():
    """Test simple search (SMART path)"""
    print("=" * 80)
    print("🧪 TEST 2: SIMPLE SEARCH (No User Profile)")
    print("=" * 80)
    print()

    payload = {
        "query": "gaming laptop",
        "use_cache": False
    }

    print(f"Query: '{payload['query']}'")
    print()

    response = requests.post(
        f"{BASE_URL}/api/search",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['success']}")
        print(f"Path Taken: {data['path_taken']}")
        print(f"Complexity: {data['complexity_score']:.2f}")
        print(f"Candidates: {data['total_candidates']}")
        print(f"Recommendations: {len(data['recommendations'])}")
        print(f"Execution Time: {data['execution_time_ms']}ms")
        print(f"Cache Hit: {data['cache_hit']}")
        print()

        if data['recommendations']:
            print("🏆 Top 3 Recommendations:")
            for rec in data['recommendations'][:3]:
                product = rec['product']
                print(f"  {rec['rank']}. {product['name']}")
                print(f"     Price: ${product['price']:.2f}")
                print(f"     Score: {rec['final_score']:.1f}")
                print(f"     Rating: {product['rating']:.1f}/5.0")
                if rec.get('explanation'):
                    print(f"     Explanation: {rec['explanation'][:80]}...")
                print()

        if data.get('errors'):
            print("⚠️ Errors:")
            for error in data['errors']:
                print(f"  - {error}")

    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_search_with_profile():
    """Test search with user profile (DEEP path)"""
    print("=" * 80)
    print("🧪 TEST 3: SEARCH WITH USER PROFILE (Financial Analysis)")
    print("=" * 80)
    print()

    payload = {
        "query": "affordable laptop for work",
        "user_profile": {
            "user_id": "test_user_123",
            "monthly_income": 6000.0,
            "monthly_expenses": 3500.0,
            "savings": 12000.0,
            "current_debt": 2000.0,
            "credit_score": 720
        },
        "filters": {
            "max_price": 2000
        },
        "use_cache": False
    }

    print(f"Query: '{payload['query']}'")
    print(f"User: ${payload['user_profile']['monthly_income']:.0f} income, {payload['user_profile']['credit_score']} credit")
    print(f"Filters: max_price=${payload['filters']['max_price']}")
    print()

    response = requests.post(
        f"{BASE_URL}/api/search",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['success']}")
        print(f"Path Taken: {data['path_taken']}")
        print(f"Complexity: {data['complexity_score']:.2f}")
        print(f"Candidates: {data['total_candidates']}")
        print(f"Recommendations: {len(data['recommendations'])}")
        print(f"Execution Time: {data['execution_time_ms']}ms")
        print()

        if data['recommendations']:
            print("🏆 Top 3 Recommendations:")
            for rec in data['recommendations'][:3]:
                product = rec['product']
                affordability = rec.get('affordability', {})

                print(f"  {rec['rank']}. {product['name']}")
                print(f"     Price: ${product['price']:.2f}")
                print(f"     Score: {rec['final_score']:.1f}")

                if affordability:
                    print(f"     Affordable: {affordability.get('is_affordable', 'N/A')}")
                    print(f"     Affordability Score: {affordability.get('affordability_score', 0):.1f}/100")

                if rec.get('trust_score') is not None:
                    print(f"     Trust Score: {rec['trust_score']:.0f}%")

                if rec.get('cluster_alternatives'):
                    print(f"     Alternatives: {len(rec['cluster_alternatives'])} similar products")

                print()

        if data.get('errors'):
            print("⚠️ Errors:")
            for error in data['errors']:
                print(f"  - {error}")

    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_feedback():
    """Test feedback submission"""
    print("=" * 80)
    print("🧪 TEST 4: FEEDBACK SUBMISSION")
    print("=" * 80)
    print()

    payload = {
        "user_id": "test_user_123",
        "product_id": "laptop_1",
        "action": "purchase",
        "query": "gaming laptop",
        "rating": 4.5
    }

    print(f"User: {payload['user_id']}")
    print(f"Product: {payload['product_id']}")
    print(f"Action: {payload['action']}")
    print(f"Rating: {payload['rating']}")
    print()

    response = requests.post(
        f"{BASE_URL}/api/feedback/action",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['success']}")
        print(f"Message: {data['message']}")
        print(f"Thompson Updated: {data['thompson_updated']}")
        print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_cache_stats():
    """Test cache statistics"""
    print("=" * 80)
    print("🧪 TEST 5: CACHE STATISTICS")
    print("=" * 80)
    print()

    response = requests.get(f"{BASE_URL}/api/cache/stats")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Cache Enabled: {data['cache_enabled']}")
        print(f"Total Keys: {data['total_keys']}")
        if data.get('memory_usage_mb'):
            print(f"Memory Usage: {data['memory_usage_mb']:.2f} MB")
        print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_recommend():
    """Test simplified recommendations endpoint"""
    print("=" * 80)
    print("🧪 TEST 6: SIMPLIFIED RECOMMENDATIONS")
    print("=" * 80)
    print()

    payload = {
        "user_id": "test_user_456",
        "category": "laptops",
        "max_price": 2000.0,
        "top_k": 3
    }

    print(f"User: {payload['user_id']}")
    print(f"Category: {payload['category']}")
    print(f"Max Price: ${payload['max_price']:.2f}")
    print(f"Top K: {payload['top_k']}")
    print()

    response = requests.post(
        f"{BASE_URL}/api/recommend",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Query: '{data['query']}'")
        print(f"Recommendations: {len(data['recommendations'])}")
        print()

        if data['recommendations']:
            print("🏆 Recommendations:")
            for rec in data['recommendations']:
                product = rec['product']
                print(f"  {rec['rank']}. {product['name']}")
                print(f"     Price: ${product['price']:.2f}")
                print(f"     Score: {rec['final_score']:.3f}")
                print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_get_product():
    """Test get product by ID"""
    print("=" * 80)
    print("🧪 TEST 7: GET PRODUCT BY ID")
    print("=" * 80)
    print()

    # First get a product ID from search
    search_response = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": "laptop", "max_results": 1}
    )

    if search_response.status_code != 200:
        print("❌ Could not get product ID from search")
        return False

    search_data = search_response.json()
    if not search_data.get('recommendations'):
        print("❌ No recommendations found")
        return False

    product_id = search_data['recommendations'][0]['product']['product_id']
    print(f"Testing with Product ID: {product_id}")
    print()

    response = requests.get(f"{BASE_URL}/api/products/{product_id}")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        product = response.json()
        print(f"✅ Product Found:")
        print(f"  Name: {product['name']}")
        print(f"  Price: ${product['price']:.2f}")
        print(f"  Category: {product.get('category', 'N/A')}")
        print(f"  Brand: {product.get('brand', 'N/A')}")
        print(f"  Rating: {product.get('rating', 0):.1f}/5.0")
        print(f"  In Stock: {product['in_stock']}")
        print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_thompson_interaction():
    """Test Thompson Sampling interaction tracking"""
    print("=" * 80)
    print("🧪 TEST 8: THOMPSON SAMPLING INTERACTION")
    print("=" * 80)
    print()

    payload = {
        "user_id": "test_user_789",
        "product_id": "PROD0042",
        "action": "purchase"
    }

    print(f"User: {payload['user_id']}")
    print(f"Product: {payload['product_id']}")
    print(f"Action: {payload['action']}")
    print()

    response = requests.post(
        f"{BASE_URL}/api/interact",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Interaction Tracked:")
        print(f"  Product: {data['product_id']}")
        print(f"  Alpha (α): {data['alpha']:.2f}")
        print(f"  Beta (β): {data['beta']:.2f}")
        print(f"  Conversion Rate: {data['conversion_rate']:.3f}")
        print(f"  Confidence: {data['confidence']}")
        print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def test_thompson_stats():
    """Test Thompson Sampling statistics"""
    print("=" * 80)
    print("🧪 TEST 9: THOMPSON SAMPLING STATISTICS")
    print("=" * 80)
    print()

    response = requests.get(f"{BASE_URL}/api/thompson/stats")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Thompson Stats:")
        print(f"  Products Tracked: {data['products_tracked']}")
        print(f"  Average Alpha: {data['avg_alpha']:.2f}")
        print(f"  Average Beta: {data['avg_beta']:.2f}")
        print(f"  Average Conversion: {data['avg_conversion']:.3f}")
        print()
        print(f"  Confidence Distribution:")
        for level, count in data['confidence'].items():
            print(f"    - {level}: {count}")
        print()
    else:
        print(f"❌ Failed: {response.text}")

    return response.status_code == 200


def main():
    """Run all API tests"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "🧪 PRICESENSE API TESTS" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        if response.status_code != 200:
            print("❌ API server not responding. Please start it with:")
            print("   cd backend")
            print("   python main.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Please start it with:")
        print("   cd backend")
        print("   python main.py")
        return

    results = []

    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Simple Search", test_search_simple()))
    results.append(("Search with Profile", test_search_with_profile()))
    results.append(("Feedback Submission", test_feedback()))
    results.append(("Cache Statistics", test_cache_stats()))
    results.append(("Simplified Recommendations", test_recommend()))
    results.append(("Get Product by ID", test_get_product()))
    results.append(("Thompson Interaction", test_thompson_interaction()))
    results.append(("Thompson Statistics", test_thompson_stats()))

    # Summary
    print()
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        emoji = "✅" if result else "❌"
        print(f"{emoji} {name}")

    print()
    print(f"{'✅ PASSED' if passed == total else '⚠️ PARTIAL'}: {passed}/{total} tests")
    print()


if __name__ == "__main__":
    main()
