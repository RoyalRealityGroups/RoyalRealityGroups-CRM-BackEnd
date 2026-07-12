#!/usr/bin/env python3
"""
Test script to verify import field API endpoints for location resources
"""

import django
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from General.reports import only_import_models

print("=" * 70)
print("TESTING LOCATION IMPORT FIELD INFO")
print("=" * 70)

location_models = ['SuperstockistLocation', 'DistributorLocation', 'RetailerLocation']

for model_name in location_models:
    print(f"\n{'=' * 70}")
    print(f"Model: {model_name}")
    print("=" * 70)
    
    if model_name not in only_import_models:
        print(f"❌ ERROR: {model_name} NOT in only_import_models")
        continue
    
    config = only_import_models[model_name]
    resource_class = config.get('resource_class')
    
    if not resource_class:
        print(f"❌ ERROR: No resource_class for {model_name}")
        continue
    
    print(f"✓ Resource class: {resource_class.__name__}")
    
    # Instantiate resource
    resource = resource_class()
    
    # Check get_field_info method
    if not hasattr(resource, 'get_field_info'):
        print(f"❌ ERROR: No get_field_info method")
        continue
    
    # Get field info
    fields = resource.get_field_info()
    
    print(f"✓ Field count: {len(fields)}")
    print("\nFields:")
    print("-" * 70)
    
    for field in fields:
        mandatory = "✓ REQUIRED" if field.get('is_mandatory') else "  Optional"
        print(f"{mandatory} | {field.get('field_name'):20s} | {field.get('display_name')}")
        print(f"           Type: {field.get('field_type')}")
        print(f"           Help: {field.get('help_text')}")
        if field.get('field_type') == 'FOREIGN_KEY':
            print(f"           FK: {field.get('foreign_model')}.{field.get('foreign_field')}")
        print()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nConclusion:")
print("If all models show ✓ above, the backend is working correctly.")
print("If fields are not showing in the UI, the issue is in the frontend.")
print("\nTo debug frontend issue:")
print("1. Open browser DevTools > Network tab")
print("2. Select a location import from dropdown")
print("3. Check the API call to /api/reports/import-models/{model}/fields/")
print("4. Verify the response contains the fields array")
print("5. Check console for JavaScript errors")
