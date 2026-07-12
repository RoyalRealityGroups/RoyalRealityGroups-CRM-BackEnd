#!/usr/bin/env python3
"""
Check if AuthorizationDefinition records are set up
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationDefinition, Authorization, AuthorizationHistory
from Sales.models import SalesOrder
from Dispatch.models import DispatchPlan
from Invoice.models import Invoice
from Delivery.models import ProofOfDelivery

print("\n" + "=" * 100)
print("AUTHORIZATION SETUP DIAGNOSTIC")
print("=" * 100)

# 1. Check AuthorizationDefinition records
print(f"\n1. AUTHORIZATION DEFINITIONS:")
auth_defs = AuthorizationDefinition.objects.filter(status=True, is_deleted=False)
print(f"   Total active definitions: {auth_defs.count()}")

if auth_defs.count() == 0:
    print("   ⚠️  NO ACTIVE AUTHORIZATION DEFINITIONS FOUND!")
    print("   This means AuthorizationHistory records will NOT be created!")
else:
    for auth_def in auth_defs[:5]:
        print(f"\n   Definition: {auth_def.name} (id={auth_def.id})")
        print(f"     screen: {auth_def.screen}")
        print(f"     level: {auth_def.level}")
        print(f"     auto_approve_creator_level: {auth_def.auto_approve_creator_level}")
        print(f"     status: {auth_def.status}")
        
        # Check Authorization records for this definition
        auths = Authorization.objects.filter(
            authorization_definition=auth_def,
            is_deleted=False
        )
        print(f"     Authorization rules: {auths.count()}")

# 2. Check Authorization records
print(f"\n2. AUTHORIZATION RULES:")
auths = Authorization.objects.filter(is_deleted=False)
print(f"   Total authorization rules: {auths.count()}")

if auths.count() > 0:
    for auth in auths[:3]:
        print(f"\n   Rule: {auth.id}")
        print(f"     definition: {auth.authorization_definition}")
        print(f"     screen: {auth.screen}")
        print(f"     level: {auth.level}")
        print(f"     type: {auth.type}")

# 3. Check if any SalesOrder has authorization applied
print(f"\n3. SALES ORDER AUTHORIZATION STATUS:")
so = SalesOrder.objects.filter(is_deleted=False).first()
if so:
    print(f"   First SalesOrder: {so.id}")
    print(f"     authorized_status: {so.authorized_status}")
    print(f"     authorized_level: {so.authorized_level}")
    print(f"     authorized_by_type: {so.authorized_by_type}")
    print(f"     authorized_by_identifier: {so.authorized_by_identifier}")
    
    # Check for history records
    ct = ContentType.objects.get_for_model(SalesOrder)
    history_records = AuthorizationHistory.objects.filter(
        screen=ct,
        instance_id=str(so.id)
    )
    print(f"     AuthorizationHistory records: {history_records.count()}")

# 4. If no auth defs, suggest what to do
if auth_defs.count() == 0:
    print(f"\n4. RESOLUTION:")
    print("   To enable authorization history, you need to:")
    print("   1. Create an AuthorizationDefinition")
    print("   2. Set auto_approve_creator_level=True")
    print("   3. Set a level value")
    print("   4. Create Authorization rules for users/groups")

print("\n" + "=" * 100)
print("END OF DIAGNOSTIC")
print("=" * 100 + "\n")
