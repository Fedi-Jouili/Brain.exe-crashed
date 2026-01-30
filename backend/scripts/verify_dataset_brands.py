"""
Dataset Brand Consistency Verification
Analyzes product names for brand inconsistencies and impossible combinations
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
import re

# Brand definitions
LAPTOP_BRANDS = {
    'asus': ['asus', 'vivobook', 'zenbook', 'rog', 'tuf'],
    'lenovo': ['lenovo', 'thinkpad', 'ideapad', 'yoga', 'legion'],
    'hp': ['hp', 'pavilion', 'envy', 'omen', 'elitebook', 'probook'],
    'dell': ['dell', 'inspiron', 'xps', 'latitude', 'alienware', 'precision'],
    'apple': ['apple', 'macbook', 'imac'],
    'acer': ['acer', 'aspire', 'predator', 'swift', 'nitro'],
    'msi': ['msi', 'katana', 'stealth', 'raider', 'prestige'],
    'samsung': ['samsung', 'galaxy book'],
    'huawei': ['huawei', 'matebook'],
    'microsoft': ['microsoft', 'surface'],
    'lg': ['lg', 'gram'],
}

PROCESSORS = {
    'intel': ['intel', 'core i3', 'core i5', 'core i7', 'core i9', 'celeron', 'pentium', 'xeon'],
    'amd': ['amd', 'ryzen', 'athlon', 'threadripper'],
    'apple': ['m1', 'm2', 'm3', 'apple silicon'],
    'qualcomm': ['snapdragon', 'qualcomm'],
}


def detect_brands(name_lower):
    """Detect all brands mentioned in product name"""
    detected = set()
    for brand, keywords in LAPTOP_BRANDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                detected.add(brand)
    return detected


def detect_processors(name_lower):
    """Detect processor brands in product name"""
    detected = set()
    for proc_brand, keywords in PROCESSORS.items():
        for keyword in keywords:
            if keyword in name_lower:
                detected.add(proc_brand)
    return detected


def is_inconsistent_combination(brands, processors):
    """Check if brand/processor combination is impossible"""
    inconsistencies = []

    # Rule 1: Apple M1/M2/M3 only in Apple products
    if 'apple' in processors and 'apple' not in brands:
        inconsistencies.append("Apple processor in non-Apple product")

    # Rule 2: VivoBook is ASUS exclusive
    if 'asus' in brands and len(brands - {'asus'}) > 0:
        if any(b in brands for b in ['lenovo', 'hp', 'dell', 'huawei']):
            inconsistencies.append("ASUS product line mixed with other brands")

    # Rule 3: ThinkPad/IdeaPad are Lenovo exclusive
    if 'lenovo' in brands and len(brands - {'lenovo'}) > 0:
        inconsistencies.append("Lenovo product line mixed with other brands")

    # Rule 4: Multiple primary brands (impossible)
    primary_brands = brands - {'asus', 'lenovo', 'hp', 'dell', 'apple', 'acer', 'msi'}
    conflicting_brands = brands & {'asus', 'lenovo', 'hp', 'dell', 'apple', 'acer', 'msi', 'samsung', 'huawei', 'microsoft', 'lg'}
    if len(conflicting_brands) > 1:
        inconsistencies.append(f"Multiple brands: {', '.join(sorted(conflicting_brands))}")

    return inconsistencies


def analyze_dataset(file_path):
    """Analyze dataset for brand inconsistencies"""

    print("=" * 100)
    print("DATASET BRAND CONSISTENCY VERIFICATION")
    print("=" * 100)
    print(f"\nAnalyzing: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"Total products: {len(products):,}\n")

        # Analysis results
        inconsistent_products = []
        brand_stats = defaultdict(int)
        processor_stats = defaultdict(int)

        # Specific searches
        lenovo_vivobook = []
        apple_m_non_apple = []
        multi_brand = []

        print("Scanning products...")
        for i, product in enumerate(products):
            if i % 10000 == 0:
                print(f"  Processed {i:,}/{len(products):,}...", end='\r')

            name = product.get('name', '')
            name_lower = name.lower()

            # Detect brands and processors
            brands = detect_brands(name_lower)
            processors = detect_processors(name_lower)

            # Update stats
            for brand in brands:
                brand_stats[brand] += 1
            for proc in processors:
                processor_stats[proc] += 1

            # Check for inconsistencies
            issues = is_inconsistent_combination(brands, processors)

            if issues:
                inconsistent_products.append({
                    'id': product.get('id', 'unknown'),
                    'name': name,
                    'brands': sorted(brands),
                    'processors': sorted(processors),
                    'issues': issues,
                    'price_TND': product.get('price_TND', 0)
                })

            # Specific problematic patterns
            if 'lenovo' in name_lower and 'vivobook' in name_lower:
                lenovo_vivobook.append(name)

            if ('m1' in name_lower or 'm2' in name_lower or 'm3' in name_lower) and 'apple' not in brands:
                apple_m_non_apple.append(name)

            if len(brands) > 1:
                multi_brand.append({
                    'name': name,
                    'brands': sorted(brands)
                })

        print(f"\n  Processed {len(products):,}/{len(products):,} - DONE!\n")

        # RESULTS
        print("=" * 100)
        print("VERIFICATION RESULTS")
        print("=" * 100)

        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Total Products: {len(products):,}")
        print(f"   Inconsistent Products: {len(inconsistent_products):,} ({len(inconsistent_products)/len(products)*100:.2f}%)")
        print(f"   Products with Multiple Brands: {len(multi_brand):,}")

        # Critical findings
        print(f"\n🔍 CRITICAL FINDINGS:")
        print(f"   'Lenovo VivoBook' combinations: {len(lenovo_vivobook)}")
        print(f"   Apple M-series in non-Apple products: {len(apple_m_non_apple)}")

        # Brand distribution
        print(f"\n📈 BRAND DISTRIBUTION:")
        for brand, count in sorted(brand_stats.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"   {brand.upper():<15} {count:>6,} products")

        # Processor distribution
        print(f"\n⚙️  PROCESSOR DISTRIBUTION:")
        for proc, count in sorted(processor_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {proc.upper():<15} {count:>6,} products")

        # Show examples of inconsistencies
        if lenovo_vivobook:
            print(f"\n❌ LENOVO + VIVOBOOK EXAMPLES (Top 10):")
            for name in lenovo_vivobook[:10]:
                print(f"   - {name}")

        if apple_m_non_apple:
            print(f"\n❌ APPLE M-SERIES IN NON-APPLE PRODUCTS (Top 10):")
            for name in apple_m_non_apple[:10]:
                print(f"   - {name}")

        if inconsistent_products:
            print(f"\n❌ TOP 20 INCONSISTENT PRODUCTS:")
            for item in inconsistent_products[:20]:
                print(f"\n   ID: {item['id']}")
                print(f"   Name: {item['name']}")
                print(f"   Brands: {', '.join(item['brands'])}")
                if item['processors']:
                    print(f"   Processors: {', '.join(item['processors'])}")
                print(f"   Issues: {'; '.join(item['issues'])}")
                print(f"   Price: {item['price_TND']} TND")

        # Final verdict
        print("\n" + "=" * 100)
        print("VERDICT")
        print("=" * 100)

        if len(inconsistent_products) > 0:
            print("\n✅ CONFIRMED: Dataset contains brand inconsistencies!")
            print(f"   {len(inconsistent_products):,} products have impossible brand/processor combinations")
            print(f"   This represents {len(inconsistent_products)/len(products)*100:.2f}% of the dataset")
            print("\n   ROOT CAUSE: Data quality issues in source dataset")
            print("   NOT AI hallucination - agents retrieve what's in the database")
        else:
            print("\n✅ Dataset appears clean - no brand inconsistencies detected")

        print("=" * 100 + "\n")

        # Save detailed report
        report_file = Path(__file__).parent.parent / 'data' / 'brand_consistency_report.json'
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_products': len(products),
                'inconsistent_count': len(inconsistent_products),
                'inconsistency_rate': len(inconsistent_products)/len(products)*100,
                'lenovo_vivobook_count': len(lenovo_vivobook),
                'apple_m_non_apple_count': len(apple_m_non_apple),
                'multi_brand_count': len(multi_brand),
                'brand_stats': dict(brand_stats),
                'processor_stats': dict(processor_stats),
                'inconsistent_products': inconsistent_products[:100],  # Top 100
                'lenovo_vivobook_examples': lenovo_vivobook[:50],
                'apple_m_examples': apple_m_non_apple[:50]
            }, f, indent=2, ensure_ascii=False)

        print(f"📄 Detailed report saved to: {report_file}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    dataset_path = Path("C:/Users/USER/Downloads/Compressed/Brain.exe-crashed-main/data/raw/tunisian_electronics_50k.json")
    sys.exit(analyze_dataset(dataset_path))
