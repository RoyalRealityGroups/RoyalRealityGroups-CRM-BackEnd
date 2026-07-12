def update_pod_effects(pod):
    """
    Update invoice POD status and sales order delivery status when a POD is saved.
    """
    from Invoice.models import Invoice
    
    # Update invoice POD status
    invoice = pod.invoice
    if invoice:
        if invoice.pod_status != 'RECEIVED':
            invoice.pod_status = 'RECEIVED'
            invoice.save(update_fields=['pod_status', 'modified_on'])
        
        # Update sales order delivery status
        if invoice.sales_order:
            invoice.sales_order.update_delivery_status()
