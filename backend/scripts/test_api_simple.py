"""
Simple API test - Health check and basic search
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("🧪 SIMPLE API TEST")
print("=" * 80)
print()

# Test 1: Health Check
print("1️⃣  Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {data['status']}")
        print(f"   Services: {sum(1 for s in data['services'].values() if 'healthy' in s)}/{len(data['services'])} healthy")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 2: Simple Search
print("2️⃣  Testing simple search (no profile)...")
try:
    payload = {
        "query": "laptop",
        "use_cache": False
    }
    
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/search",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    elapsed = int((time.time() - start) * 1000)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data['success']}")
        print(f"   Path: {data['path_taken']}")
        print(f"   Recommendations: {len(data['recommendations'])}")
        print(f"   Time: {elapsed}ms")
        
        if data['recommendations']:
            top = data['recommendations'][0]
            print(f"   Top: {top['product']['name']} (${top['product']['price']:.2f})")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 3: Feedback
print("3️⃣  Testing feedback submission...")
try:
    payload = {
        "user_id": "test_user",
        "product_id": "laptop_1",
        "action": "view",
        "query": "laptop"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/feedback/action",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success: {data['message']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 4: Cache Stats
print("4️⃣  Testing cache stats...")
try:
    response = requests.get(f"{BASE_URL}/api/cache/stats", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Cache enabled: {data['cache_enabled']}")
        print(f"   Total keys: {data['total_keys']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 80)
print("✅ API TEST COMPLETE")
print("=" * 80)
