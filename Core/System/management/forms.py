from email.policy import default
from urllib import request
from django import forms

RESTORE_CHOICES= [
    ('YES', 'Yes'),
    ('NO', 'No'),
    ]

class UserForm(forms.Form):
    
    output= forms.CharField(label='Are You Sure You want to Restore', widget=forms.RadioSelect(choices=RESTORE_CHOICES))
