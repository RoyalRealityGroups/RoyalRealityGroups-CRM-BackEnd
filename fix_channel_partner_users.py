#!/usr/bin/env python
"""
Diagnostic script to find and fix users with channel_partner_type but no assignment.

Usage:
    python fix_channel_partner_users.py --check    # Check for issues
    python fix_channel_partner_users.py --fix      # Fix issues automatically
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BaseProject.settings')
django.setup()

from Users.models import User
from Masters.models import Superstockist, Distributor, Retailer


def check_users():
    """Check for users with channel_partner_type but no assignment"""
    issues = []
    
    # Check SUPERSTOCKIST users
    sst_users = User.objects.filter(channel_partner_type='SUPERSTOCKIST', superstockist__isnull=True)
    for user in sst_users:
        issues.append({
            'user': user,
            'type': 'SUPERSTOCKIST',
            'issue': 'User has channel_partner_type=SUPERSTOCKIST but superstockist field is None'
        })
    
    # Check DISTRIBUTOR users
    dist_users = User.objects.filter(channel_partner_type='DISTRIBUTOR', distributor__isnull=True)
    for user in dist_users:
        issues.append({
            'user': user,
            'type': 'DISTRIBUTOR',
            'issue': 'User has channel_partner_type=DISTRIBUTOR but distributor field is None'
        })
    
    # Check RETAILER users
    ret_users = User.objects.filter(channel_partner_type='RETAILER', retailer__isnull=True)
    for user in ret_users:
        issues.append({
            'user': user,
            'type': 'RETAILER',
            'issue': 'User has channel_partner_type=RETAILER but retailer field is None'
        })
    
    return issues


def auto_fix_users():
    """Attempt to automatically fix users by matching username/email to partner name"""
    fixed = []
    failed = []
    
    # Fix DISTRIBUTOR users
    dist_users = User.objects.filter(channel_partner_type='DISTRIBUTOR', distributor__isnull=True)
    for user in dist_users:
        # Try to find matching distributor by name similarity
        potential_matches = Distributor.objects.filter(
            name__icontains=user.username.split('@')[0]
        ) | Distributor.objects.filter(
            name__icontains=user.first_name
        ) | Distributor.objects.filter(
            name__icontains=user.last_name
        )
        
        if potential_matches.count() == 1:
            distributor = potential_matches.first()
            user.distributor = distributor
            user.save()
            fixed.append({
                'user': user,
                'partner': distributor,
                'type': 'DISTRIBUTOR'
            })
        else:
            failed.append({
                'user': user,
                'type': 'DISTRIBUTOR',
                'matches': potential_matches.count()
            })
    
    # Fix SUPERSTOCKIST users
    sst_users = User.objects.filter(channel_partner_type='SUPERSTOCKIST', superstockist__isnull=True)
    for user in sst_users:
        potential_matches = Superstockist.objects.filter(
            name__icontains=user.username.split('@')[0]
        ) | Superstockist.objects.filter(
            name__icontains=user.first_name
        ) | Superstockist.objects.filter(
            name__icontains=user.last_name
        )
        
        if potential_matches.count() == 1:
            superstockist = potential_matches.first()
            user.superstockist = superstockist
            user.save()
            fixed.append({
                'user': user,
                'partner': superstockist,
                'type': 'SUPERSTOCKIST'
            })
        else:
            failed.append({
                'user': user,
                'type': 'SUPERSTOCKIST',
                'matches': potential_matches.count()
            })
    
    # Fix RETAILER users
    ret_users = User.objects.filter(channel_partner_type='RETAILER', retailer__isnull=True)
    for user in ret_users:
        potential_matches = Retailer.objects.filter(
            name__icontains=user.username.split('@')[0]
        ) | Retailer.objects.filter(
            name__icontains=user.first_name
        ) | Retailer.objects.filter(
            name__icontains=user.last_name
        )
        
        if potential_matches.count() == 1:
            retailer = potential_matches.first()
            user.retailer = retailer
            user.save()
            fixed.append({
                'user': user,
                'partner': retailer,
                'type': 'RETAILER'
            })
        else:
            failed.append({
                'user': user,
                'type': 'RETAILER',
                'matches': potential_matches.count()
            })
    
    return fixed, failed


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix channel partner user assignments')
    parser.add_argument('--check', action='store_true', help='Check for issues')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    
    args = parser.parse_args()
    
    if args.check:
        print("Checking for users with channel_partner_type but no assignment...\n")
        issues = check_users()
        
        if not issues:
            print("✓ No issues found!")
        else:
            print(f"Found {len(issues)} issue(s):\n")
            for issue in issues:
                print(f"  User: {issue['user'].username} ({issue['user'].email})")
                print(f"  Type: {issue['type']}")
                print(f"  Issue: {issue['issue']}\n")
    
    elif args.fix:
        print("Attempting to fix users automatically...\n")
        fixed, failed = auto_fix_users()
        
        if fixed:
            print(f"✓ Fixed {len(fixed)} user(s):\n")
            for item in fixed:
                print(f"  User: {item['user'].username}")
                print(f"  Assigned to: {item['partner'].name} ({item['type']})\n")
        
        if failed:
            print(f"⚠ Could not auto-fix {len(failed)} user(s):\n")
            for item in failed:
                print(f"  User: {item['user'].username}")
                print(f"  Type: {item['type']}")
                print(f"  Potential matches: {item['matches']}")
                print(f"  Action: Manual assignment required\n")
        
        if not fixed and not failed:
            print("✓ No issues to fix!")
    
    else:
        parser.print_help()
