from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from Invoice.models import Invoice
from Receipts.ledger_service import (
    deactivate_ledger_entry,
    sync_invoice_ledger,
    sync_receipt_ledger,
)
from Receipts.models import Receipt


@receiver(post_save, sender=Invoice)
def sync_invoice_ledger_on_save(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    sync_invoice_ledger(instance)


@receiver(post_delete, sender=Invoice)
def deactivate_invoice_ledger_on_delete(sender, instance, **kwargs):
    deactivate_ledger_entry('INVOICE', instance.id, 'INVOICE_POSTED')


@receiver(post_save, sender=Receipt)
def sync_receipt_ledger_on_save(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    sync_receipt_ledger(instance)


@receiver(post_delete, sender=Receipt)
def deactivate_receipt_ledger_on_delete(sender, instance, **kwargs):
    deactivate_ledger_entry('RECEIPT', instance.id, 'RECEIPT_POSTED')
