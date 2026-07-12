from django.core.management.base import BaseCommand
from django.apps import apps
from Core.Users.serializers import get_pending_approver_names


class Command(BaseCommand):
    help = 'Test pending approver names for actual pending records'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n=== Testing Pending Approver Names ===\n'))
        
        # Test Sales Orders
        SalesOrder = apps.get_model('Sales', 'salesorder')
        pending_sos = SalesOrder.objects.filter(
            authorized_status=1,
            is_deleted=False
        ).order_by('-created_on')[:5]
        
        self.stdout.write(f'\n--- Pending Sales Orders ({pending_sos.count()}) ---')
        for so in pending_sos:
            self.stdout.write(f'\nSO: {so.order_number}')
            self.stdout.write(f'  ID: {so.id}')
            self.stdout.write(f'  Status: {so.authorized_status} (Pending)')
            self.stdout.write(f'  Current Level: {so.authorized_level}')
            self.stdout.write(f'  Next Level: {(so.authorized_level or 0) + 1}')
            
            approver_names = get_pending_approver_names(so)
            self.stdout.write(f'  Approver Names: "{approver_names}"')
            if not approver_names:
                self.stdout.write(self.style.WARNING('    ⚠️  No approver names found!'))
        
        # Test Dispatch Plans
        DispatchPlan = apps.get_model('Dispatch', 'dispatchplan')
        pending_dps = DispatchPlan.objects.filter(
            authorized_status=1,
            is_deleted=False
        ).order_by('-created_on')[:5]
        
        self.stdout.write(f'\n--- Pending Dispatch Plans ({pending_dps.count()}) ---')
        for dp in pending_dps:
            self.stdout.write(f'\nDP: {dp.dispatch_number}')
            self.stdout.write(f'  ID: {dp.id}')
            self.stdout.write(f'  Status: {dp.authorized_status} (Pending)')
            self.stdout.write(f'  Current Level: {dp.authorized_level}')
            self.stdout.write(f'  Next Level: {(dp.authorized_level or 0) + 1}')
            
            approver_names = get_pending_approver_names(dp)
            self.stdout.write(f'  Approver Names: "{approver_names}"')
            if not approver_names:
                self.stdout.write(self.style.WARNING('    ⚠️  No approver names found!'))
        
        # Test Invoices (should return empty since no auth configured)
        Invoice = apps.get_model('Invoice', 'invoice')
        pending_invoices = Invoice.objects.filter(
            authorized_status=1,
            is_deleted=False
        ).order_by('-created_on')[:3]
        
        self.stdout.write(f'\n--- Pending Invoices ({pending_invoices.count()}) ---')
        if pending_invoices.count() > 0:
            self.stdout.write(self.style.WARNING('  ⚠️  No Authorization configured for Invoice model'))
            for inv in pending_invoices:
                approver_names = get_pending_approver_names(inv)
                self.stdout.write(f'  Invoice {inv.invoice_number}: "{approver_names}" (Expected: empty)')
        
        self.stdout.write(self.style.SUCCESS('\n=== Test Complete ===\n'))
