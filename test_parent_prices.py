#!/usr/bin/env python3
"""
Test script to verify parent prices are loading correctly for CITY level
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from Masters.models import PriceBook, City, State, Item
from datetime import date

def test_parent_prices():
    print("=" * 80)
    print("Testing Parent Price Loading for CITY Level")
    print("=" * 80)
    
    # Get some test data
    items = Item.objects.filter(is_deleted=False)[:3]
    cities = City.objects.filter(is_deleted=False)[:3]
    
    if not items.exists():
        print("❌ No items found in database")
        return
    
    if not cities.exists():
        print("❌ No cities found in database")
        return
    
    print(f"\n✓ Found {items.count()} items and {cities.count()} cities")
    
    # Check state-level prices
    state_prices = PriceBook.objects.filter(
        item__in=items,
        is_deleted=False,
        is_active=True,
        price_type='GEOGRAPHIC',
        city__isnull=True,
        area__isnull=True
    ).select_related('item', 'state')
    
    print(f"\n✓ Found {state_prices.count()} state-level prices")
    
    for price in state_prices:
        print(f"  - {price.item.name} in {price.state.name if price.state else 'N/A'}: ₹{price.selling_price}")
    
    # Test the logic
    print("\n" + "=" * 80)
    print("Testing Key Generation Logic")
    print("=" * 80)
    
    for city in cities:
        for item in items:
            # Simulate what the view does
            item_id_str = str(item.id)
            city_id_str = str(city.id)
            state_id_str = str(city.state_id)
            
            print(f"\nItem: {item.name} (ID: {item_id_str[:8]}...)")
            print(f"City: {city.name} (ID: {city_id_str[:8]}...)")
            print(f"State: {city.state.name} (ID: {state_id_str[:8]}...)")
            
            # Check if there's a state price for this item
            state_price = state_prices.filter(
                item_id=item.id,
                state_id=city.state_id
            ).first()
            
            if state_price:
                # Test key matching
                lookup_key = f"{item_id_str}-{state_id_str}"
                price_key_old = f"{state_price.item_id}-{state_price.state_id}"  # Old way (would fail)
                price_key_new = f"{str(state_price.item_id)}-{str(state_price.state_id)}"  # New way (fixed)
                
                print(f"  Lookup key: {lookup_key[:20]}...")
                print(f"  Old price key: {price_key_old[:20]}... - Match: {lookup_key == price_key_old}")
                print(f"  New price key: {price_key_new[:20]}... - Match: {lookup_key == price_key_new}")
                print(f"  ✓ Parent price: ₹{state_price.selling_price}")
            else:
                print(f"  ⚠ No state-level price found for this item")
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("✅ If 'New price key' shows Match: True, the fix is working!")
    print("❌ If 'Old price key' shows Match: False, that's the bug we fixed")
    print("=" * 80)

if __name__ == '__main__':
    test_parent_prices()
