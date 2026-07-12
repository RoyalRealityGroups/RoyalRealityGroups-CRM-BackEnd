from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead, LeadStatusHistory


@receiver(post_save, sender=Lead)
def create_lead_status_history(sender, instance, created, **kwargs):
    """Create status history entry when lead is created or status changes"""
    from Users.models import User
    user = None
    if instance.created_by_identifier:
        try:
            user = User.objects.get(id=instance.created_by_identifier)
        except User.DoesNotExist:
            pass
    
    if created:
        LeadStatusHistory.objects.create(
            lead=instance,
            from_status=None,
            to_status=instance.status,
            changed_by=user,
            remarks='Lead created'
        )
    else:
        if hasattr(instance, '_previous_status') and instance._previous_status != instance.status:
            LeadStatusHistory.objects.create(
                lead=instance,
                from_status=instance._previous_status,
                to_status=instance.status,
                changed_by=user,
                remarks='Status changed'
            )
