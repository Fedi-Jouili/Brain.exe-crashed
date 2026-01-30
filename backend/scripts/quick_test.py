import requests

print('Testing search endpoint...')
r = requests.post(
    'http://localhost:8000/api/search',
    json={'query': 'laptop', 'use_cache': False},
    timeout=60
)

print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    print(f'✅ Success: {data["success"]}')
    print(f'Path: {data["path_taken"]}')
    print(f'Complexity: {data["complexity_score"]:.2f}')
    print(f'Recommendations: {len(data["recommendations"])}')
    print(f'Execution Time: {data["execution_time_ms"]}ms')
    
    if data["recommendations"]:
        top = data["recommendations"][0]
        print(f'\n🏆 Top Recommendation:')
        print(f'   {top["product"]["name"]}')
        print(f'   Price: ${top["product"]["price"]:.2f}')
        print(f'   Score: {top["final_score"]:.1f}')
        if top.get("explanation"):
            print(f'   Explanation: {top["explanation"][:100]}...')
else:
    print(f'❌ Error: {r.text}')
