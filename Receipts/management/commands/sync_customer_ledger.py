from django.core.management.base import BaseCommand

from Invoice.models import Invoice
from Receipts.ledger_service import (
    is_invoice_postable,
    is_receipt_postable,
    sync_invoice_ledger,
    sync_receipt_ledger,
)
from Receipts.models import CustomerLedgerEntry, Receipt


class Command(BaseCommand):
    help = "Backfill/sync customer ledger entries for invoices and receipts"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Mark existing ledger entries as inactive before sync',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview how many records are postable without writing data',
        )

    def handle(self, *args, **options):
        reset = options['reset']
        dry_run = options['dry_run']

        if reset:
            existing_qs = CustomerLedgerEntry.objects.filter(is_deleted=False)
            existing_count = existing_qs.count()
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] Would mark {existing_count} ledger entries as inactive"
                    )
                )
            else:
                existing_qs.update(
                    is_deleted=True,
                    entry_status='INACTIVE',
                    modified_by_type='System',
                    modified_by_identifier='ledger-backfill',
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Marked {existing_count} existing ledger entries as inactive"
                    )
                )

        invoices = Invoice.objects.filter(is_deleted=False).select_related(
            'sales_order',
            'sales_order__retailer',
            'sales_order__distributor',
            'sales_order__superstockist',
            'company',
            'location',
        )
        receipts = Receipt.objects.filter(is_deleted=False).select_related(
            'retailer',
            'distributor',
            'superstockist',
            'company',
            'location',
        )

        invoice_postable = 0
        receipt_postable = 0

        for invoice in invoices.iterator():
            if is_invoice_postable(invoice):
                invoice_postable += 1
            if not dry_run:
                sync_invoice_ledger(invoice)

        for receipt in receipts.iterator():
            if is_receipt_postable(receipt):
                receipt_postable += 1
            if not dry_run:
                sync_receipt_ledger(receipt)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Customer ledger dry-run summary:'))
            self.stdout.write(f"Invoices postable: {invoice_postable}")
            self.stdout.write(f"Receipts postable: {receipt_postable}")
            return

        active_count = CustomerLedgerEntry.objects.filter(is_deleted=False).count()
        self.stdout.write(self.style.SUCCESS('Customer ledger sync completed successfully'))
        self.stdout.write(f"Invoices posted: {invoice_postable}")
        self.stdout.write(f"Receipts posted: {receipt_postable}")
        self.stdout.write(f"Active ledger entries: {active_count}")
