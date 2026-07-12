#!/usr/bin/env python3
"""
Quick test to verify AuthorizationHistoryView ContentType lookup fix
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from Core.Users.models import AuthorizationHistory

# Test the fix
print("\n=" * 70)
print("TESTING AUTHORIZATION HISTORY FIX")
print("=" * 70)

test_paths = [
    ("sales.salesorder", "sales", "salesorder"),
    ("dispatch.dispatchplan", "dispatch", "dispatchplan"),
    ("invoice.invoice", "invoice", "invoice"),
    ("delivery.proofofdelivery", "delivery", "proofofdelivery"),
]

for model_path, expected_app_label, expected_model_name in test_paths:
    print(f"\n📝 Testing: {model_path}")
    print(f"   Expected: app_label='{expected_app_label}', model='{expected_model_name}'")
    
    try:
        # Parse
        app_label, model_name = model_path.split('.')
        print(f"   Parsed:   app_label='{app_label}', model='{model_name}'")
        
        # Get ContentType
        ct = ContentType.objects.get(app_label=expected_app_label, model=expected_model_name)
        print(f"   ✅ ContentType found: {ct.app_label}.{ct.model} (id={ct.id})")
        
        # Try querying AuthorizationHistory with this ContentType
        count = AuthorizationHistory.objects.filter(screen=ct).count()
        print(f"   📊 AuthorizationHistory records using this ContentType: {count}")
        
        if count > 0:
            sample = AuthorizationHistory.objects.filter(screen=ct).first()
            print(f"      - Sample: id={sample.id}, instance={sample.instance_id}, status={sample.authorized_status}")
        
    except ContentType.DoesNotExist:
        print(f"   ❌ ContentType NOT FOUND")
    except Exception as e:
        print(f"   ❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70 + "\n")
