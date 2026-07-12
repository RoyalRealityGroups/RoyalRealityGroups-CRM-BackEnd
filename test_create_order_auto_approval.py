#!/usr/bin/env python
"""
Test script to create a SalesOrder as the final level approver and verify auto-approval
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationDefinition, Authorization, AuthorizationHistory
from Users.models import User
from Sales.models import SalesOrder
from Masters.models import Company
from Core.Core.context.Context import set_user
import json

def test_auto_approval_creation():
    print("=" * 80)
    print("TEST: Creating SalesOrder as Final Level Approver (sales user)")
    print("=" * 80)
    
    # Get the sales user (Level 2 final approver)
    try:
        sales_user = User.objects.get(username='sales')
        print(f"\n✓ Using user: {sales_user.username} ({sales_user.email})")
    except User.DoesNotExist:
        print("\n✗ User 'sales' not found")
        return
    
    # Set the user context (simulating authenticated request)
    set_user(sales_user)
    
    # Get a company for the order
    try:
        company = Company.objects.first()
        if not company:
            print("\n✗ No company found in database")
            return
        print(f"✓ Using company: {company.name}")
    except Exception as e:
        print(f"\n✗ Error getting company: {e}")
        return
    
    # Create a test sales order
    print("\n" + "-" * 80)
    print("Creating test SalesOrder...")
    print("-" * 80)
    
    from datetime import date
    
    try:
        order = SalesOrder.objects.create(
            order_number=f"TEST-{SalesOrder.objects.count() + 1}",
            order_date=date.today(),
            company=company,
            created_by_type='User',
            created_by_identifier=str(sales_user.id)
        )
        
        print(f"\n✓ Created SalesOrder: {order.order_number}")
        print(f"  - Order ID: {order.id}")
        print(f"  - Created by: {sales_user.username}")
        print(f"  - Company: {company.name}")
        
        # Refresh from DB to get updated values
        order.refresh_from_db()
        
        # Check authorization status
        print(f"\n" + "-" * 80)
        print("AUTHORIZATION STATUS:")
        print("-" * 80)
        
        status_map = {1: 'PENDING', 2: 'APPROVED', 3: 'REJECTED'}
        status_name = status_map.get(order.authorized_status, f'UNKNOWN({order.authorized_status})')
        
        print(f"\nAuthorized Status: {status_name} ({order.authorized_status})")
        print(f"Authorized Level: {order.authorized_level}")
        print(f"Authorized By: {order.authorized_by_type} - {order.authorized_by_identifier}")
        print(f"Authorized On: {order.authorized_on}")
        
        # Check authorization history
        print(f"\n" + "-" * 80)
        print("AUTHORIZATION HISTORY:")
        print("-" * 80)
        
        history_records = AuthorizationHistory.objects.filter(
            screen__model='salesorder',
            instance_id=str(order.id)
        ).order_by('authorized_level')
        
        if history_records.exists():
            print(f"\n✓ Found {history_records.count()} AutorizationHistory records:\n")
            for hist in history_records:
                hist_status = status_map.get(hist.authorized_status, f'UNKNOWN({hist.authorized_status})')
                print(f"  Level {hist.authorized_level}:")
                print(f"    - Status: {hist_status}")
                print(f"    - Description: {hist.description}")
                print(f"    - Approved By: {hist.authorized_by_type} - {hist.authorized_by_identifier}")
                print(f"    - Approved On: {hist.authorized_on}")
        else:
            print(f"\n⚠ No AuthorizationHistory records found")
            print("  This might indicate auto-approval history creation issue")
        
        # Final verdict
        print(f"\n" + "=" * 80)
        if order.authorized_status == 2:
            print("✅ SUCCESS: Record was AUTO-APPROVED!")
            print(f"   Status: {status_name}")
            print(f"   Level: {order.authorized_level}")
            if history_records.exists():
                print(f"   History Records Created: {history_records.count()}")
        else:
            print(f"❌ FAILURE: Record was NOT auto-approved")
            print(f"   Status: {status_name} (expected APPROVED)")
            print(f"   Level: {order.authorized_level}")
            print(f"\n   Checking configuration...")
            
            # Debug: Check if the problem is in the configuration or the code
            auth_def = AuthorizationDefinition.objects.filter(
                screen__model='salesorder',
                status=True,
                is_deleted=False
            ).first()
            
            if auth_def:
                print(f"   - Auth Definition Found: {auth_def.authorization_name}")
                print(f"   - Auto-Approve: {auth_def.auto_approve_creator_level}")
                print(f"   - Final Level: {auth_def.level}")
            else:
                print(f"   - No active Auth Definition found")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error creating order: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auto_approval_creation()
