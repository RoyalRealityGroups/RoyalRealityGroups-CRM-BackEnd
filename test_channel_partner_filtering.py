#!/usr/bin/env python
"""
Test script for Channel Partner Self-Service functionality
Run: python manage.py shell < test_channel_partner_filtering.py
"""

from Users.models import User
from Masters.models import Superstockist, Distributor, Retailer, Company
from Sales.models import SalesOrder
from django.contrib.auth.models import Group

print("\n" + "="*80)
print("CHANNEL PARTNER SELF-SERVICE TEST")
print("="*80 + "\n")

# Get or create test company
company, _ = Company.objects.get_or_create(
    code='TEST_COMP',
    defaults={'name': 'Test Company'}
)
print(f"✓ Using company: {company.name}")

# Create test channel partners
print("\n1. Creating test channel partners...")

ss, _ = Superstockist.objects.get_or_create(
    code='SS001',
    defaults={
        'name': 'Test Superstockist',
        'company': company,
        'state_id': '1'  # Adjust based on your data
    }
)
print(f"   ✓ Superstockist: {ss.name}")

dist, _ = Distributor.objects.get_or_create(
    code='DIST001',
    defaults={
        'name': 'Test Distributor',
        'company': company,
        'superstockist': ss,
        'state_id': '1'
    }
)
print(f"   ✓ Distributor: {dist.name}")

retailer, _ = Retailer.objects.get_or_create(
    code='RET001',
    defaults={
        'name': 'Test Retailer',
        'company': company,
        'distributor': dist,
        'state_id': '1'
    }
)
print(f"   ✓ Retailer: {retailer.name}")

# Create test users
print("\n2. Creating test users...")

# Get or create a default group
group, _ = Group.objects.get_or_create(name='Channel Partners')

# Staff user
staff_user, created = User.objects.get_or_create(
    username='staff_user',
    defaults={
        'channel_partner_type': 'STAFF',
        'is_staff': False,
        'is_superuser': False
    }
)
if created:
    staff_user.set_password('password123')
    staff_user.groups.add(group)
    staff_user.save()
print(f"   ✓ Staff User: {staff_user.username}")

# Superstockist user
ss_user, created = User.objects.get_or_create(
    username='ss_user',
    defaults={
        'channel_partner_type': 'SUPERSTOCKIST',
        'superstockist': ss,
        'is_staff': False,
        'is_superuser': False
    }
)
if created:
    ss_user.set_password('password123')
    ss_user.groups.add(group)
    ss_user.save()
print(f"   ✓ Superstockist User: {ss_user.username} -> {ss.name}")

# Distributor user
dist_user, created = User.objects.get_or_create(
    username='dist_user',
    defaults={
        'channel_partner_type': 'DISTRIBUTOR',
        'distributor': dist,
        'is_staff': False,
        'is_superuser': False
    }
)
if created:
    dist_user.set_password('password123')
    dist_user.groups.add(group)
    dist_user.save()
print(f"   ✓ Distributor User: {dist_user.username} -> {dist.name}")

# Retailer user
ret_user, created = User.objects.get_or_create(
    username='ret_user',
    defaults={
        'channel_partner_type': 'RETAILER',
        'retailer': retailer,
        'is_staff': False,
        'is_superuser': False
    }
)
if created:
    ret_user.set_password('password123')
    ret_user.groups.add(group)
    ret_user.save()
print(f"   ✓ Retailer User: {ret_user.username} -> {retailer.name}")

# Test filtering
print("\n3. Testing data visibility...")

print("\n   A. Superstockist Master Visibility:")
print(f"      Staff User sees: {Superstockist.filtered_objects.get_qs(user=staff_user, company=company).count()} superstockists")
print(f"      SS User sees: {Superstockist.filtered_objects.get_qs(user=ss_user, company=company).count()} superstockist (their own)")
print(f"      Dist User sees: {Superstockist.filtered_objects.get_qs(user=dist_user, company=company).count()} superstockists")
print(f"      Retailer User sees: {Superstockist.filtered_objects.get_qs(user=ret_user, company=company).count()} superstockists")

print("\n   B. Distributor Master Visibility:")
print(f"      Staff User sees: {Distributor.filtered_objects.get_qs(user=staff_user, company=company).count()} distributors")
print(f"      SS User sees: {Distributor.filtered_objects.get_qs(user=ss_user, company=company).count()} distributor(s) under them")
print(f"      Dist User sees: {Distributor.filtered_objects.get_qs(user=dist_user, company=company).count()} distributor (their own)")
print(f"      Retailer User sees: {Distributor.filtered_objects.get_qs(user=ret_user, company=company).count()} distributors")

print("\n   C. Retailer Master Visibility:")
print(f"      Staff User sees: {Retailer.filtered_objects.get_qs(user=staff_user, company=company).count()} retailers")
print(f"      SS User sees: {Retailer.filtered_objects.get_qs(user=ss_user, company=company).count()} retailer(s) under them")
print(f"      Dist User sees: {Retailer.filtered_objects.get_qs(user=dist_user, company=company).count()} retailer(s) under them")
print(f"      Retailer User sees: {Retailer.filtered_objects.get_qs(user=ret_user, company=company).count()} retailer (their own)")

# Test with sales orders if any exist
so_count = SalesOrder.objects.filter(is_deleted=False).count()
if so_count > 0:
    print("\n   D. Sales Order Visibility:")
    print(f"      Staff User sees: {SalesOrder.filtered_objects.get_qs(user=staff_user).count()} orders")
    print(f"      SS User sees: {SalesOrder.filtered_objects.get_qs(user=ss_user).count()} orders")
    print(f"      Dist User sees: {SalesOrder.filtered_objects.get_qs(user=dist_user).count()} orders")
    print(f"      Retailer User sees: {SalesOrder.filtered_objects.get_qs(user=ret_user).count()} orders")
else:
    print("\n   D. Sales Order Visibility: (No sales orders to test)")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nTest users created with password: password123")
print("You can now login with these users to test the filtering:\n")
print(f"  - staff_user (sees all data)")
print(f"  - ss_user (sees only {ss.name} data)")
print(f"  - dist_user (sees only {dist.name} data)")
print(f"  - ret_user (sees only {retailer.name} data)")
print("\n")
