import uuid
from django.db import models


# Create your models here.



class SyncTrigger(models.Model):
    MANUAL  = 1
    AUTOMATIC  = 2

    SYNC_TYPE_STATUS_CHOICES = (
        (MANUAL , 'Manual'),
        (AUTOMATIC , 'Automatic'),
    )

    FOCUS  = 1
    AMCU  = 2

    SYNC_FROM_STATUS_CHOICES = (
        (FOCUS , 'Focus'),
        (AMCU , 'Amcu'),
    )

    id = models.UUIDField( primary_key=True,default=uuid.uuid4, editable=False)
    sync_type = models.SmallIntegerField(choices=SYNC_TYPE_STATUS_CHOICES, default=2, null= True, blank= True)
    sync_from = models.SmallIntegerField(choices=SYNC_FROM_STATUS_CHOICES, default=1, null= True, blank= True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True)

    __str__ = lambda self: str(self.sync_type)


class SyncLog(models.Model):
    id = models.UUIDField( primary_key=True,default=uuid.uuid4, editable=False) 
    sync_trigger = models.ForeignKey(SyncTrigger, on_delete=models.RESTRICT, related_name='sync_log_items', null=True, blank=True)
    log = models.TextField(null= True, blank= True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True)

    __str__ = lambda self: str(self.created_on)

