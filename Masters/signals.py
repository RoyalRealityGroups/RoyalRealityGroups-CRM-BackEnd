from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Project, ProjectStatusHistory


@receiver(pre_save, sender=Project)
def capture_previous_project_status(sender, instance, **kwargs):
    """Stash the existing status so the post_save handler can diff it."""
    if instance.pk:
        try:
            previous = Project.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
        except Project.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Project)
def write_project_status_history(sender, instance, created, **kwargs):
    """Auto-write a status-history row on create and on every status change."""
    from Users.models import User

    user = None
    if instance.modified_by_identifier:
        try:
            user = User.objects.get(id=instance.modified_by_identifier)
        except (User.DoesNotExist, ValueError, TypeError):
            user = None
    elif instance.created_by_identifier:
        try:
            user = User.objects.get(id=instance.created_by_identifier)
        except (User.DoesNotExist, ValueError, TypeError):
            user = None

    previous = getattr(instance, '_previous_status', None)

    if created:
        ProjectStatusHistory.objects.create(
            project=instance,
            from_status=None,
            to_status=instance.status,
            changed_by_identifier=str(user.id) if user else None,
            remarks='Project created',
        )
    elif previous and previous != instance.status:
        ProjectStatusHistory.objects.create(
            project=instance,
            from_status=previous,
            to_status=instance.status,
            changed_by_identifier=str(user.id) if user else None,
            remarks='Status changed',
        )