#!/usr/bin/env python3
"""
Complete diagnostic for authorization history issue
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationHistory
from Sales.models import SalesOrder
from Dispatch.models import DispatchPlan
from Invoice.models import Invoice
from Delivery.models import ProofOfDelivery

print("\n" + "=" * 80)
print("AUTHORIZATION HISTORY DIAGNOSTIC")
print("=" * 80)

# Step 1: Check what ContentTypes exist for our models
print("\n1. AVAILABLE CONTENT TYPES:")
print("-" * 80)

test_models = [
    ('Sales', 'salesorder'),
    ('sales', 'salesorder'),
    ('Dispatch', 'dispatchplan'),
    ('dispatch', 'dispatchplan'),
    ('Invoice', 'invoice'),
    ('invoice', 'invoice'),
    ('Delivery', 'proofofdelivery'),
    ('delivery', 'proofofdelivery'),
]

for app_label, model_name in test_models:
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
        print(f"✓ Found: app_label='{app_label}', model='{model_name}' → {ct}")
    except ContentType.DoesNotExist:
        pass  # Don't print failures for brevity

# Step 2: Check what AuthorizationHistory records exist
print("\n2. AUTHORIZATION HISTORY RECORDS:")
print("-" * 80)

total_records = AuthorizationHistory.objects.count()
print(f"Total records in DB: {total_records}")

deleted_records = AuthorizationHistory.objects.filter(is_deleted=True).count()
not_deleted_records = AuthorizationHistory.objects.filter(is_deleted=False).count()
null_deleted_records = AuthorizationHistory.objects.filter(is_deleted__isnull=True).count()

print(f"is_deleted=True: {deleted_records}")
print(f"is_deleted=False: {not_deleted_records}")
print(f"is_deleted=NULL: {null_deleted_records}")

print("\nSample records:")
for record in AuthorizationHistory.objects.all()[:3]:
    print(f"\nRecord ID: {record.id}")
    print(f"  screen_id: {record.screen_id}")
    print(f"  screen: {record.screen}")
    print(f"  instance_id: {record.instance_id}")
    print(f"  is_deleted: {record.is_deleted}")
    print(f"  authorized_status: {record.authorized_status}")

# Step 3: Test the actual query that AuthorizationHistoryView uses
print("\n3. TESTING AUTHORIZATION HISTORY VIEW QUERY:")
print("-" * 80)

# Get a sample SalesOrder with authorization history
sales_orders = SalesOrder.objects.filter(is_deleted=False)[:1]
if sales_orders.exists():
    so = sales_orders.first()
    print(f"\nTesting with SalesOrder: {so.id}")
    
    # Test the query
    app_label = 'sales'
    model_name = 'salesorder'
    instance_id = str(so.id)
    
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
        print(f"ContentType: {ct}")
        
        # Try the exact query from AuthorizationHistoryView
        records = AuthorizationHistory.objects.filter(
            screen=ct, 
            instance_id=instance_id,
            is_deleted=False
        )
        
        print(f"Query: AuthorizationHistory.objects.filter(screen={ct}, instance_id='{instance_id}', is_deleted=False)")
        print(f"Result count: {records.count()}")
        
        if records.exists():
            for r in records:
                print(f"  ✓ Found: {r.id} - level={r.authorized_level}, status={r.authorized_status}")
        else:
            print("  ✗ No records found")
            
            # Try without is_deleted filter
            records_all = AuthorizationHistory.objects.filter(
                screen=ct,
                instance_id=instance_id
            )
            print(f"\n  Without is_deleted filter: {records_all.count()} records")
            for r in records_all:
                print(f"    - {r.id}: is_deleted={r.is_deleted}")
                
    except ContentType.DoesNotExist as e:
        print(f"✗ ContentType not found: {e}")

# Step 4: Check if records are being created at all for specific instances
print("\n4. CHECKING RECORDS FOR FIRST 5 INSTANCES:")
print("-" * 80)

for model_class, model_name in [(SalesOrder, 'SalesOrder'), (DispatchPlan, 'DispatchPlan')]:
    instances = model_class.objects.filter(is_deleted=False)[:5]
    print(f"\n{model_name}:")
    for inst in instances:
        ct = ContentType.objects.get_for_model(model_class)
        records = AuthorizationHistory.objects.filter(
            screen=ct,
            instance_id=str(inst.id),
            is_deleted=False
        )
        print(f"  {inst.id}: {records.count()} auth history records")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80 + "\n")
