#!/usr/bin/env python
"""
Test auto-approval when final level approver creates a record
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationDefinition, Authorization
from Users.models import User
from Sales.models import SalesOrder
from django.db import models

def test_auto_approval_logic():
    print("=" * 80)
    print("TEST: Auto-Approval When Final Level Approver Creates Record")
    print("=" * 80)
    
    # Get the Sales user (final level approver)
    try:
        sales_user = User.objects.get(username='sales')
        print(f"\n✓ Found user: {sales_user.username} ({sales_user.email})")
    except User.DoesNotExist:
        print("\n✗ User 'sales' not found")
        return
    
    # Get SalesOrder ContentType
    sales_order_ct = ContentType.objects.get(app_label='Sales', model='salesorder')
    
    # Get Authorization Definition
    auth_def = AuthorizationDefinition.objects.filter(
        screen=sales_order_ct,
        status=True,
        is_deleted=False
    ).first()
    
    if not auth_def:
        print("\n✗ No active Authorization Definition found")
        return
    
    print(f"\nAuthorization Definition: {auth_def.authorization_name}")
    print(f"  - Final Level: {auth_def.level}")
    print(f"  - Auto-Approve Creator Level: {auth_def.auto_approve_creator_level}")
    
    # Check what level the sales user has
    user_type = sales_user.__class__.__name__
    user_identifier = str(sales_user.id)
    group_ids = list(sales_user.groups.values_list('id', flat=True))
    
    print(f"\nChecking authorization level for user '{sales_user.username}':")
    print(f"  - User Type: {user_type}")
    print(f"  - User ID: {user_identifier}")
    print(f"  - Groups: {group_ids}")
    
    # Find user's authorization level (same logic as get_creator_level)
    levels_qs = Authorization.objects.filter(
        authorization_definition=auth_def,
        screen=sales_order_ct,
    ).filter(
        models.Q(type=1, user_type=user_type, user_identifier=user_identifier) |
        models.Q(type=2, group_id__in=group_ids)
    ).filter(models.Q(is_deleted=False) | models.Q(is_deleted__isnull=True))
    
    if levels_qs.exists():
        levels = list(levels_qs.values_list('level', flat=True))
        creator_level = max(levels) if levels else None
        
        print(f"\n✓ User has authorization levels: {levels}")
        print(f"  - Maximum level (creator_level): {creator_level}")
        print(f"  - Final level required: {auth_def.level}")
        
        # Simulate the auto-approval logic from CoreModel.save()
        if auth_def.auto_approve_creator_level:
            print(f"\n✓ Auto-approve is ENABLED")
            
            if creator_level:
                final_level = auth_def.level or creator_level
                auto_level = min(creator_level, final_level)
                
                print(f"\nCalculated values:")
                print(f"  - final_level = {final_level}")
                print(f"  - auto_level = min({creator_level}, {final_level}) = {auto_level}")
                
                if auto_level >= final_level:
                    print(f"\n✅ RESULT: Record WILL be auto-approved!")
                    print(f"  - Condition: auto_level ({auto_level}) >= final_level ({final_level})")
                    print(f"  - authorized_status will be set to: APPROVED (2)")
                    print(f"  - authorized_level will be set to: {auto_level}")
                    print(f"  - {auto_level} AuthorizationHistory records will be created")
                else:
                    print(f"\n❌ RESULT: Record will NOT be auto-approved")
                    print(f"  - Condition: auto_level ({auto_level}) < final_level ({final_level})")
                    print(f"  - authorized_status will be set to: PENDING (1)")
                    print(f"  - authorized_level will be set to: {auto_level}")
            else:
                print(f"\n❌ creator_level is None - no auto-approval")
        else:
            print(f"\n❌ Auto-approve is DISABLED - feature won't work")
    else:
        print(f"\n✗ User has NO authorization levels")
        print("  - User will NOT trigger auto-approval")
    
    # Now check if there's an issue with the code
    print("\n" + "=" * 80)
    print("CHECKING CODE LOGIC")
    print("=" * 80)
    
    # Read the actual code logic from CoreModel
    print("\nThe auto-approval logic in CoreModel.save() checks:")
    print("1. authorization_def_obj exists")
    print("2. authorization_def_obj.auto_approve_creator_level is True")
    print("3. get_creator_level() returns a value")
    print("4. auto_level >= final_level")
    
    print("\n" + "=" * 80)
    print("TESTING WITH ACTUAL DATABASE QUERY")
    print("=" * 80)
    
    # Check if there are existing sales orders created by sales user
    existing_orders = SalesOrder.objects.filter(
        created_by_identifier=str(sales_user.id)
    ).order_by('-created_on')[:5]
    
    if existing_orders.exists():
        print(f"\nFound {existing_orders.count()} recent orders created by '{sales_user.username}':\n")
        for order in existing_orders:
            status_map = {1: 'PENDING', 2: 'APPROVED', 3: 'REJECTED'}
            status_name = status_map.get(order.authorized_status, f'UNKNOWN({order.authorized_status})')
            
            print(f"Order {order.order_number}:")
            print(f"  - Created on: {order.created_on}")
            print(f"  - Authorized Status: {status_name} ({order.authorized_status})")
            print(f"  - Authorized Level: {order.authorized_level}")
            
            if order.authorized_status != 2:
                print(f"  ❌ NOT AUTO-APPROVED!")
            else:
                print(f"  ✅ AUTO-APPROVED")
            print()
    else:
        print(f"\n⚠ No sales orders found created by '{sales_user.username}'")
        print("  Create a test order to verify the functionality")

if __name__ == "__main__":
    test_auto_approval_logic()
