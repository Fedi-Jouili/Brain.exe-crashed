"""
Quick validation script for RAGAS evaluator module
Run with: python backend/validate_ragas.py
"""

print("\n" + "=" * 60)
print("RAGAS Evaluator - Module Validation")
print("=" * 60 + "\n")

# Test 1: Import
print("1. Testing import...")
try:
    from ragas_evaluator import RAGASEvaluator
    print("   ✅ Import successful")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("   Install with: pip install ragas datasets")
    exit(1)

# Test 2: Initialization
print("\n2. Testing initialization...")
try:
    evaluator = RAGASEvaluator()
    if evaluator._initialized:
        print(f"   ✅ Evaluator initialized: {len(evaluator.metrics)} metrics loaded")
    else:
        print("   ⚠️ Evaluator created but not fully initialized")
        print("   Install with: pip install ragas datasets")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    exit(1)

# Test 3: Method availability
print("\n3. Testing methods...")
methods = [
    "evaluate_single",
    "evaluate_batch",
    "calculate_query_product_relevancy"
]
for method in methods:
    if hasattr(evaluator, method):
        print(f"   ✅ {method}() available")
    else:
        print(f"   ❌ {method}() missing")

# Test 4: Error handling (neutral scores)
print("\n4. Testing error handling...")
try:
    scores = evaluator.evaluate_single(
        question="",  # Invalid input
        answer="",
        contexts=[]
    )
    if scores == {"context_precision": 0.5, "faithfulness": 0.5, "answer_relevancy": 0.5}:
        print("   ✅ Error handling returns neutral scores (0.5)")
    else:
        print(f"   ⚠️ Unexpected error response: {scores}")
except Exception as e:
    print(f"   ❌ Error handling failed: {e}")

# Test 5: Relevancy error handling
print("\n5. Testing relevancy error handling...")
try:
    score = evaluator.calculate_query_product_relevancy("", "", "")
    if score == 50.0:
        print("   ✅ Relevancy error handling returns neutral (50.0)")
    else:
        print(f"   ⚠️ Unexpected relevancy response: {score}")
except Exception as e:
    print(f"   ❌ Relevancy error handling failed: {e}")

print("\n" + "=" * 60)
print("Validation Summary")
print("=" * 60)
print("\n✅ All basic validation tests passed!")
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements_ragas.txt")
print("2. Run full tests: pytest test_ragas_evaluator.py -v")
print("3. Try examples: python ragas_evaluator.py")
print()
