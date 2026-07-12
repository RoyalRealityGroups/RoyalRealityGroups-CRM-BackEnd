#!/usr/bin/env python
"""
Diagnostic script to check auto-approval configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from Core.Users.models import AuthorizationDefinition, Authorization
from Users.models import User
from Sales.models import SalesOrder

def check_auto_approval_config():
    print("=" * 80)
    print("AUTO-APPROVAL CONFIGURATION DIAGNOSTIC")
    print("=" * 80)
    
    # Get SalesOrder ContentType
    try:
        sales_order_ct = ContentType.objects.get(app_label='Sales', model='salesorder')
        print(f"\n✓ Found ContentType for SalesOrder: {sales_order_ct}")
    except ContentType.DoesNotExist:
        print("\n✗ SalesOrder ContentType not found!")
        return
    
    # Check Authorization Definitions
    print("\n" + "-" * 80)
    print("AUTHORIZATION DEFINITIONS FOR SALES ORDER:")
    print("-" * 80)
    
    auth_defs = AuthorizationDefinition.objects.filter(
        screen=sales_order_ct,
        is_deleted=False
    )
    
    if not auth_defs.exists():
        print("✗ No Authorization Definitions found for SalesOrder")
        return
    
    for auth_def in auth_defs:
        print(f"\nAuthorization Definition ID: {auth_def.id}")
        print(f"  - Name: {auth_def.authorization_name}")
        print(f"  - Status: {'Active' if auth_def.status else 'Inactive'}")
        print(f"  - Final Level: {auth_def.level}")
        print(f"  - Auto-Approve Creator Level: {auth_def.auto_approve_creator_level}")
        print(f"  - Effective From: {auth_def.effective_from}")
        print(f"  - Company: {auth_def.companies.first() if not auth_def.has_all_companies else 'All Companies'}")
        print(f"  - Location: {auth_def.locations.first() if not auth_def.has_all_locations else 'All Locations'}")
        
        if not auth_def.auto_approve_creator_level:
            print("\n  ⚠ WARNING: auto_approve_creator_level is FALSE")
            print("  → This means records will NOT be auto-approved even if creator is final approver")
            print("  → To enable, set auto_approve_creator_level = True in AuthorizationDefinition")
    
    # Check Authorizations (Approvers)
    print("\n" + "-" * 80)
    print("AUTHORIZATIONS (APPROVERS) FOR SALES ORDER:")
    print("-" * 80)
    
    authorizations = Authorization.objects.filter(
        screen=sales_order_ct,
        is_deleted=False
    ).order_by('level')
    
    if not authorizations.exists():
        print("✗ No Authorizations found for SalesOrder")
        return
    
    for auth in authorizations:
        print(f"\nAuthorization ID: {auth.id}")
        print(f"  - Level: {auth.level}")
        print(f"  - Type: {'User' if auth.type == 1 else 'Group'}")
        
        if auth.type == 1:  # User
            print(f"  - User Type: {auth.user_type}")
            print(f"  - User ID: {auth.user_identifier}")
            # Try to get user details
            try:
                user = User.objects.get(id=auth.user_identifier)
                print(f"  - User Name: {user.username}")
                print(f"  - User Email: {user.email}")
            except User.DoesNotExist:
                print(f"  - User not found")
        else:  # Group
            print(f"  - Group: {auth.group.name if auth.group else 'None'}")
            if auth.group:
                users = auth.group.user_set.all()
                print(f"  - Group Members: {', '.join([u.username for u in users])}")
        
        print(f"  - Authorization Definition: {auth.authorization_definition_id if auth.authorization_definition_id else 'Not linked'}")
    
    # Test scenario
    print("\n" + "-" * 80)
    print("TEST SCENARIO:")
    print("-" * 80)
    
    # Get an active auth definition
    active_auth_def = auth_defs.filter(status=True).first()
    if not active_auth_def:
        print("✗ No active Authorization Definition found")
        return
    
    print(f"\nUsing Authorization Definition: {active_auth_def.authorization_name}")
    print(f"Final Level Required: {active_auth_def.level}")
    print(f"Auto-Approve Creator Level: {active_auth_def.auto_approve_creator_level}")
    
    # Check each user to see if they would get auto-approved
    print("\n\nCHECKING USERS WHO WOULD GET AUTO-APPROVED:")
    print("-" * 80)
    
    all_users = User.objects.filter(is_active=True, is_deleted=False)[:10]  # Limit to 10 for testing
    
    for user in all_users:
        user_type = user.__class__.__name__
        user_identifier = str(user.id)
        group_ids = list(user.groups.values_list('id', flat=True))
        
        # Find user's authorization level (same logic as get_creator_level)
        levels_qs = Authorization.objects.filter(
            authorization_definition=active_auth_def,
            screen=sales_order_ct,
            is_deleted=False
        ).filter(
            models.Q(type=1, user_type=user_type, user_identifier=user_identifier) |
            models.Q(type=2, group_id__in=group_ids)
        )
        
        if levels_qs.exists():
            levels = list(levels_qs.values_list('level', flat=True))
            max_level = max(levels) if levels else None
            
            if max_level:
                would_auto_approve = (
                    active_auth_def.auto_approve_creator_level and 
                    max_level >= active_auth_def.level
                )
                
                status_icon = "✓" if would_auto_approve else "○"
                print(f"\n{status_icon} User: {user.username}")
                print(f"   - Max Level: {max_level}")
                print(f"   - Final Level Required: {active_auth_def.level}")
                
                if would_auto_approve:
                    print(f"   - Would AUTO-APPROVE: YES (level {max_level} >= {active_auth_def.level})")
                else:
                    if not active_auth_def.auto_approve_creator_level:
                        print(f"   - Would AUTO-APPROVE: NO (auto_approve_creator_level is disabled)")
                    else:
                        print(f"   - Would AUTO-APPROVE: NO (level {max_level} < {active_auth_def.level})")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    
    if not active_auth_def.auto_approve_creator_level:
        print("\n1. ENABLE AUTO-APPROVAL:")
        print("   Go to Settings > Authorization Definitions")
        print(f"   Edit: {active_auth_def.authorization_name}")
        print("   Enable 'Auto-Approve Creator Level' switch")
        print("   Save")
    else:
        print("\n✓ Auto-approval is enabled")
    
    final_level_auths = authorizations.filter(level=active_auth_def.level)
    if final_level_auths.exists():
        print(f"\n2. USERS WHO CAN CREATE AUTO-APPROVED RECORDS:")
        for auth in final_level_auths:
            if auth.type == 1:
                try:
                    user = User.objects.get(id=auth.user_identifier)
                    print(f"   - {user.username} (User, Level {auth.level})")
                except User.DoesNotExist:
                    print(f"   - User ID {auth.user_identifier} (Not found)")
            else:
                print(f"   - {auth.group.name if auth.group else 'Unknown Group'} (Group, Level {auth.level})")
                if auth.group:
                    for u in auth.group.user_set.all():
                        print(f"     • {u.username}")
    else:
        print(f"\n⚠ WARNING: No approvers found at final level {active_auth_def.level}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    from django.db import models
    check_auto_approval_config()
