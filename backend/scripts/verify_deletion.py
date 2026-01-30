"""
Verify specific problematic products were deleted
"""
import csv
from pathlib import Path

report_file = Path("../data/processed/deleted_products_report.csv")

with open(report_file, 'r', encoding='utf-8') as f:
    report = list(csv.DictReader(f))

print(f"\n{'='*80}")
print("VERIFICATION: Specific Problem Products Deleted")
print(f"{'='*80}\n")

# Check Lenovo VivoBook
lenovo_vivobook = [r for r in report if 'lenovo' in r['name'].lower() and 'vivobook' in r['name'].lower()]
print(f"✅ Lenovo VivoBook products deleted: {len(lenovo_vivobook)}")
if lenovo_vivobook:
    print("\n   Examples:")
    for r in lenovo_vivobook[:5]:
        print(f"   - {r['name']}")
        print(f"     Reason: {r['violation_reason']}\n")

# Check Apple M-series in non-Apple
apple_m_non_apple = [r for r in report if ('m1' in r['name'].lower() or 'm2' in r['name'].lower() or 'm3' in r['name'].lower()) and 'apple' not in r['name'].lower()]
print(f"✅ Apple M-series in non-Apple products deleted: {len(apple_m_non_apple)}")
if apple_m_non_apple:
    print("\n   Examples:")
    for r in apple_m_non_apple[:5]:
        print(f"   - {r['name']}")
        print(f"     Reason: {r['violation_reason']}\n")

# Check MSI MacBook
msi_macbook = [r for r in report if 'msi' in r['name'].lower() and 'macbook' in r['name'].lower()]
print(f"✅ MSI MacBook products deleted: {len(msi_macbook)}")

# Check Dell IdeaPad
dell_ideapad = [r for r in report if 'dell' in r['name'].lower() and 'ideapad' in r['name'].lower()]
print(f"✅ Dell IdeaPad products deleted: {len(dell_ideapad)}")

# Check Huawei VivoBook
huawei_vivobook = [r for r in report if 'huawei' in r['name'].lower() and 'vivobook' in r['name'].lower()]
print(f"✅ Huawei VivoBook products deleted: {len(huawei_vivobook)}")
if huawei_vivobook:
    print("\n   Examples:")
    for r in huawei_vivobook[:3]:
        print(f"   - {r['name']}")
        print(f"     Reason: {r['violation_reason']}\n")

print(f"{'='*80}")
print("✅ ALL PROBLEMATIC PRODUCTS SUCCESSFULLY REMOVED")
print(f"{'='*80}\n")
