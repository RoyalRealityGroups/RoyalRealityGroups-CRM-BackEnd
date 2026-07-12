#!/usr/bin/env python3
"""
Test script to verify AuthorizationHistoryView app_label mapping fix
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationHistory

# Test data
print("=" * 70)
print("AUTHORIZATION HISTORY FIX TEST")
print("=" * 70)

# The mapping that should be used in AuthorizationHistoryView
app_label_map = {
    ('sales', 'salesorder'): 'Sales',
    ('sales', 'invoice'): 'Invoice',
    ('dispatch', 'dispatchplan'): 'Dispatch',
    ('delivery', 'dispatchplan'): 'Dispatch',
    ('delivery', 'proofofdelivery'): 'Delivery',
    ('masters', 'scheme'): 'Masters',
    ('masters', 'pricebookdocument'): 'Masters',
    ('invoice', 'invoice'): 'Invoice',
}

test_cases = [
    ('sales', 'salesorder', 'Sales'),
    ('dispatch', 'dispatchplan', 'Dispatch'),
    ('invoice', 'invoice', 'Invoice'),
    ('delivery', 'proofofdelivery', 'Delivery'),
]

print("\nTest Plan:")
print("-" * 70)
for frontend_app, frontend_model, expected_django_app in test_cases:
    print(f"\n1. Frontend sends: {frontend_app}.{frontend_model}")
    print(f"   Expected mapping: {expected_django_app}.{frontend_model}")
    
    # Get mapped app label
    actual_app_label = app_label_map.get((frontend_app.lower(), frontend_model.lower()))
    
    if not actual_app_label:
        print(f"   ✗ ERROR: No mapping found in app_label_map!")
        continue
    
    if actual_app_label != expected_django_app:
        print(f"   ✗ ERROR: Mapping mismatch! Got {actual_app_label}, expected {expected_django_app}")
        continue
    
    print(f"   ✓ Mapping correct: {actual_app_label}")
    
    # Try to get ContentType (case-insensitive)
    try:
        ct = ContentType.objects.get(
            app_label__iexact=actual_app_label,
            model__iexact=frontend_model.lower()
        )
        print(f"   ✓ ContentType found: id={ct.id}, {ct.app_label}.{ct.model}")
        
        # Check if there are any AuthorizationHistory records for this model
        auth_records = AuthorizationHistory.objects.filter(screen=ct)
        print(f"   ✓ AuthorizationHistory records: {auth_records.count()}")
        
        if auth_records.exists():
            sample = auth_records.first()
            print(f"      Sample record: id={sample.id}, instance={sample.instance_id}, status={sample.authorized_status}")
        
    except ContentType.DoesNotExist:
        print(f"   ✗ ERROR: ContentType not found!")
    except Exception as e:
        print(f"   ✗ ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
