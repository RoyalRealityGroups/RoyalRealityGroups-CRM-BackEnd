from django.db.models.signals import post_save
from django.dispatch import receiver
from Sales.models import SalesOrder


@receiver(post_save, sender=SalesOrder)
def update_status_on_authorization(sender, instance, created, **kwargs):
    """
    Auto-update status when authorization status changes
    """
    if created:
        return
    
    # Avoid infinite loop by checking if we need to update
    if instance.authorized_status == 2 and instance.status in ['DRAFT', 'PENDING', 'REJECTED']:
        # Approved: move to CONFIRMED from pre-approval states
        SalesOrder.objects.filter(pk=instance.pk).update(status='CONFIRMED')
    elif instance.authorized_status == 3 and instance.status != 'CANCELLED':
        # Rejected: Change to CANCELLED
        SalesOrder.objects.filter(pk=instance.pk).update(status='CANCELLED')
