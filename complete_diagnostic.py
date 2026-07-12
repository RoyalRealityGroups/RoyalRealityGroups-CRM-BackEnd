#!/usr/bin/env python3
"""
Complete diagnostic - check if records exist and query works
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationHistory
from Sales.models import SalesOrder
from Dispatch.models import DispatchPlan

print("\n" + "=" * 100)
print("COMPLETE AUTHORIZATION HISTORY DIAGNOSTIC")
print("=" * 100)

# 1. Check total records
total = AuthorizationHistory.objects.count()
deleted = AuthorizationHistory.objects.filter(is_deleted=True).count()
not_deleted = AuthorizationHistory.objects.filter(is_deleted=False).count()

print(f"\n1. AUTHORIZATION HISTORY RECORDS IN DATABASE:")
print(f"   Total: {total}")
print(f"   is_deleted=True: {deleted}")
print(f"   is_deleted=False: {not_deleted}")

if total == 0:
    print("\n   ⚠️  NO RECORDS IN DATABASE - Records are not being created at all!")
    
    # Check if there are any SalesOrders
    so_count = SalesOrder.objects.filter(is_deleted=False).count()
    print(f"\n   SalesOrders in DB: {so_count}")
    if so_count > 0:
        so = SalesOrder.objects.filter(is_deleted=False).first()
        print(f"   First SalesOrder ID: {so.id}")
        print(f"   First SalesOrder authorized_status: {so.authorized_status}")
        print(f"   First SalesOrder authorized_level: {so.authorized_level}")
        
else:
    print(f"\n   ✓ Records exist in database")
    
    # 2. Show sample records
    print(f"\n2. SAMPLE AUTHORIZATION HISTORY RECORDS:")
    for i, record in enumerate(AuthorizationHistory.objects.all()[:5], 1):
        print(f"\n   Record {i}:")
        print(f"     ID: {record.id}")
        print(f"     screen_id: {record.screen_id}")
        print(f"     instance_id: {record.instance_id} (type: {type(record.instance_id).__name__})")
        print(f"     is_deleted: {record.is_deleted}")
        print(f"     authorized_status: {record.authorized_status}")

# 3. Check ContentTypes
print(f"\n3. CONTENT TYPES:")
print("   Checking for different app_label formats:")

for app_label in ['sales', 'Sales', 'dispatch', 'Dispatch', 'invoice', 'Invoice']:
    count = ContentType.objects.filter(app_label=app_label).count()
    if count > 0:
        cts = ContentType.objects.filter(app_label=app_label)
        print(f"   app_label='{app_label}': {count} types")
        for ct in cts:
            print(f"     - {ct.app_label}.{ct.model} (id={ct.id})")

# 4. Test exact query
print(f"\n4. TESTING EXACT QUERY:")
print("   Looking for SalesOrder with auth history...")

so = SalesOrder.objects.filter(is_deleted=False).first()
if so:
    print(f"\n   Using SalesOrder: {so.id}")
    
    # Test ContentType lookup
    try:
        ct = ContentType.objects.get(app_label='sales', model='salesorder')
        print(f"   ✓ ContentType found: {ct}")
        
        # Test the exact query
        records = AuthorizationHistory.objects.filter(
            screen=ct,
            instance_id=str(so.id),
            is_deleted=False
        )
        print(f"   Query result: {records.count()} records")
        
        # Also try without is_deleted filter
        records_all = AuthorizationHistory.objects.filter(
            screen=ct,
            instance_id=str(so.id)
        )
        print(f"   Without is_deleted filter: {records_all.count()} records")
        
        # Try exact instance_id match
        print(f"\n   Checking instance_id matching:")
        print(f"   Looking for instance_id='{so.id}'")
        records_by_id = AuthorizationHistory.objects.filter(instance_id=str(so.id))
        print(f"   Records with exact instance_id match: {records_by_id.count()}")
        
        # Show all instances in AuthorizationHistory
        unique_instances = AuthorizationHistory.objects.values_list('instance_id', flat=True).distinct()
        print(f"\n   All unique instance_ids in DB: {list(unique_instances)[:5]}")
        
    except ContentType.DoesNotExist:
        print(f"   ✗ ContentType NOT found for app_label='sales', model='salesorder'")

# 5. Show what's really in the database
print(f"\n5. RAW DATABASE QUERY:")
if AuthorizationHistory.objects.exists():
    record = AuthorizationHistory.objects.first()
    print(f"   First record details:")
    print(f"   - id: {record.id}")
    print(f"   - screen: {record.screen}")
    print(f"   - screen_id: {record.screen_id}")
    print(f"   - instance_id: '{record.instance_id}'")
    print(f"   - created_on: {record.created_on}")

print("\n" + "=" * 100)
print("DIAGNOSTIC COMPLETE")
print("=" * 100 + "\n")
