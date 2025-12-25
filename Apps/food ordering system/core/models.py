"""
Core app models.
Defines base abstract models used by other apps.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides timestamp fields.
    All models can inherit from this to automatically track creation and update times.
    
    Fields:
        created_at: DateTime when the record was created
        updated_at: DateTime when the record was last updated
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
