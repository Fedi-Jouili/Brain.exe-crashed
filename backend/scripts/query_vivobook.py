"""
Query all VivoBook products from Qdrant
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.qdrant_client import get_qdrant_client
from qdrant_client.models import Filter, FieldCondition, MatchText

def main():
    client = get_qdrant_client()

    # Query products with "vivobook" in the name (case-insensitive)
    results, _ = client.scroll(
        collection_name='products',
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key='name',
                    match=MatchText(text='vivobook')
                )
            ]
        ),
        limit=100,
        with_payload=True,
        with_vectors=False
    )

    print(f"\n{'='*80}")
    print(f"VIVOBOOK PRODUCTS IN DATASET")
    print(f"{'='*80}\n")
    print(f"Found {len(results)} VivoBook products:\n")

    for i, point in enumerate(results, 1):
        payload = point.payload
        print(f"{i}. {payload.get('name', 'Unknown')}")
        print(f"   Product ID: {payload.get('product_id', 'N/A')}")
        print(f"   Price: ${payload.get('price', 'N/A')}")
        print(f"   Category: {payload.get('category', 'N/A')}")

        # Check for financing
        if payload.get('financing_available'):
            terms = payload.get('financing_terms', {})
            print(f"   Financing: {terms.get('months', 12)} months @ {terms.get('apr', 0)*100:.1f}% APR")

        # Show specs if available
        if 'specs' in payload:
            specs = payload['specs']
            if specs.get('processor'):
                print(f"   Processor: {specs['processor']}")
            if specs.get('ram'):
                print(f"   RAM: {specs['ram']}")
            if specs.get('storage'):
                print(f"   Storage: {specs['storage']}")

        print()

    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
