from django.db import models
from Masters.models import Project


class Plot(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BLOCKED', 'Blocked'),
        ('BOOKED', 'Booked'),
        ('REGISTERED', 'Registered'),
    ]

    plot_number = models.CharField(max_length=50, unique=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='plots')
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text='Area in sq.ft')
    price = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    facing = models.CharField(max_length=30, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'plot_number']

    def __str__(self):
        return f"{self.project.name} - {self.plot_number}"


class Flat(models.Model):
    STATUS_CHOICES = Plot.STATUS_CHOICES

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='flats')
    tower = models.CharField(max_length=50)
    floor = models.IntegerField()
    unit_number = models.CharField(max_length=50)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    facing = models.CharField(max_length=30, blank=True, default='')
    price = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    notes = models.TextField(blank=True, default='')

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['project', 'tower', 'floor', 'unit_number']
        unique_together = [('project', 'tower', 'floor', 'unit_number')]

    def __str__(self):
        return f"{self.project.name} - {self.tower}-{self.floor}-{self.unit_number}"