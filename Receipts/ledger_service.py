from decimal import Decimal

from .models import CustomerLedgerEntry


APPROVED_STATUS = 2
ACTIVE_INVOICE_STATUSES = {'CONFIRMED', 'PAID', 'PARTIALLY_PAID'}


def _customer_payload(customer_type, retailer=None, distributor=None, superstockist=None):
    return {
        'customer_type': customer_type,
        'retailer': retailer,
        'distributor': distributor,
        'superstockist': superstockist,
    }


def deactivate_ledger_entry(document_type, document_id, event_type):
    """Mark a previously posted ledger entry as inactive."""
    CustomerLedgerEntry.objects.filter(
        document_type=document_type,
        document_id=document_id,
        event_type=event_type,
        is_deleted=False,
    ).update(
        is_deleted=True,
        entry_status='INACTIVE',
        modified_by_type='System',
        modified_by_identifier='ledger-sync',
    )


def is_invoice_postable(invoice):
    return (
        invoice.sales_order_id is not None
        and invoice.authorized_status == APPROVED_STATUS
        and invoice.status in ACTIVE_INVOICE_STATUSES
        and invoice.grand_total > 0
    )


def is_receipt_postable(receipt):
    return (
        receipt.authorized_status == APPROVED_STATUS
        and receipt.total_amount > 0
    )


def sync_invoice_ledger(invoice):
    """Upsert the invoice debit entry; deactivate it when invoice is not postable."""
    if not is_invoice_postable(invoice):
        deactivate_ledger_entry('INVOICE', invoice.id, 'INVOICE_POSTED')
        return None

    sales_order = invoice.sales_order
    defaults = {
        **_customer_payload(
            customer_type=sales_order.customer_type,
            retailer=sales_order.retailer,
            distributor=sales_order.distributor,
            superstockist=sales_order.superstockist,
        ),
        'document_number': invoice.invoice_number,
        'document_date': invoice.invoice_date,
        'posting_date': invoice.invoice_date,
        'debit_amount': invoice.grand_total,
        'credit_amount': Decimal('0.00'),
        'entry_status': 'ACTIVE',
        'company': invoice.company,
        'location': invoice.location,
        'remarks': f'Invoice posted: {invoice.invoice_number}',
        'meta_data': {
            'source_type': invoice.source_type,
            'invoice_status': invoice.status,
            'authorized_status': invoice.authorized_status,
        },
        'is_deleted': False,
    }

    entry, _ = CustomerLedgerEntry.objects.update_or_create(
        document_type='INVOICE',
        document_id=invoice.id,
        event_type='INVOICE_POSTED',
        defaults=defaults,
    )
    return entry


def sync_receipt_ledger(receipt):
    """Upsert the receipt credit entry; deactivate it when receipt is not approved."""
    if not is_receipt_postable(receipt):
        deactivate_ledger_entry('RECEIPT', receipt.id, 'RECEIPT_POSTED')
        return None

    defaults = {
        **_customer_payload(
            customer_type=receipt.customer_type,
            retailer=receipt.retailer,
            distributor=receipt.distributor,
            superstockist=receipt.superstockist,
        ),
        'document_number': receipt.receipt_number,
        'document_date': receipt.receipt_date,
        'posting_date': receipt.receipt_date,
        'debit_amount': Decimal('0.00'),
        'credit_amount': receipt.total_amount,
        'entry_status': 'ACTIVE',
        'company': receipt.company,
        'location': receipt.location,
        'remarks': f'Receipt posted: {receipt.receipt_number}',
        'meta_data': {
            'payment_mode': receipt.payment_mode,
            'reference_number': receipt.reference_number,
            'authorized_status': receipt.authorized_status,
        },
        'is_deleted': False,
    }

    entry, _ = CustomerLedgerEntry.objects.update_or_create(
        document_type='RECEIPT',
        document_id=receipt.id,
        event_type='RECEIPT_POSTED',
        defaults=defaults,
    )
    return entry
