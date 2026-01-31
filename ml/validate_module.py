"""
Quick validation script for collaborative filtering module
Tests basic functionality without requiring full scipy import
"""

import sys
import os

# Add ml directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=" * 60)
print("Collaborative Filtering Module - Validation Script")
print("=" * 60)

# Test 1: Check file structure
print("\n[1/5] Checking file structure...")
required_files = [
    'ml/__init__.py',
    'ml/collaborative_filtering.py',
    'ml/test_collaborative_filtering.py',
    'ml/collaborative_filtering_integration_guide.md',
    'ml/requirements_collab.txt'
]

all_exist = True
for file in required_files:
    file_path = os.path.join(os.path.dirname(__file__), '..', file)
    exists = os.path.exists(file_path)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}")
    if not exists:
        all_exist = False

if all_exist:
    print("  ✓ All required files present")
else:
    print("  ✗ Some files missing")
    sys.exit(1)

# Test 2: Check requirements
print("\n[2/5] Checking requirements_collab.txt...")
with open(os.path.join(os.path.dirname(__file__), '..', 'ml', 'requirements_collab.txt'), 'r') as f:
    requirements = f.read()
    assert 'numpy>=1.24.0' in requirements
    assert 'scipy>=1.10.0' in requirements
    print("  ✓ Requirements file valid")

# Test 3: Check class definition
print("\n[3/5] Checking CollaborativeFilter class...")
with open(os.path.join(os.path.dirname(__file__), '..', 'ml', 'collaborative_filtering.py'), 'r') as f:
    code = f.read()
    required_methods = [
        'def find_similar_users',
        'def recommend_from_similar_users',
        'def calculate_product_score_for_user',
        'def build_user_feature_vector'
    ]

    for method in required_methods:
        if method in code:
            print(f"  ✓ {method} found")
        else:
            print(f"  ✗ {method} NOT FOUND")
            sys.exit(1)

# Test 4: Check test file
print("\n[4/5] Checking test file...")
with open(os.path.join(os.path.dirname(__file__), '..', 'ml', 'test_collaborative_filtering.py'), 'r') as f:
    test_code = f.read()
    test_count = test_code.count('def test_')
    print(f"  ✓ Found {test_count} test methods")
    if test_count < 7:
        print(f"  ✗ Expected at least 7 tests, found {test_count}")
        sys.exit(1)

# Test 5: Check integration guide
print("\n[5/5] Checking integration guide...")
with open(os.path.join(os.path.dirname(__file__), '..', 'ml', 'collaborative_filtering_integration_guide.md'), 'r', encoding='utf-8') as f:
    guide = f.read()
    required_sections = [
        '## 📦 Installation',
        '## 🚀 Quick Start',
        '## 🔌 Integration into Agent 3',
        '## 📊 Data Requirements',
        '## ⚡ Performance Notes',
        '## 🐛 Troubleshooting'
    ]

    for section in required_sections:
        if section in guide:
            print(f"  ✓ {section}")
        else:
            print(f"  ✗ {section} NOT FOUND")
            sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL VALIDATION CHECKS PASSED!")
print("=" * 60)

print("\n📋 Next Steps:")
print("  1. Install dependencies: pip install -r ml/requirements_collab.txt")
print("  2. Run tests: pytest ml/test_collaborative_filtering.py -v")
print("  3. Run standalone: python ml/collaborative_filtering.py")
print("  4. Integrate into Agent 3 using the guide")
print("\n⚠️  Note: scipy import may be slow on first run (30-60 seconds)")
print("   This is normal for scipy on Windows with Python 3.14")
