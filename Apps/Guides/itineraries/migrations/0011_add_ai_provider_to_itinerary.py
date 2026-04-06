"""
Migration to add ai_provider field to Itinerary model.

This migration adds a new field to track which AI provider (OpenAI/Gemini)
was used to generate an AI-created itinerary.
"""

from django.db import migrations, models


def add_ai_provider_field(apps, schema_editor):
    """
    Add the ai_provider field to the Itinerary model.
    
    Args:
        apps: Registry of installed applications
        schema_editor: For database schema manipulation
    """
    Itinerary = apps.get_model('itineraries', 'Itinerary')
    
    # Add the field with a default value for existing records
    field = models.CharField(
        max_length=20,
        choices=[
            ('openai', 'OpenAI'),
            ('gemini', 'Google Gemini'),
        ],
        null=True,
        blank=True,
        help_text="Which AI provider was used to generate this itinerary"
    )
    field.contribute_to_class(Itinerary, 'ai_provider')
    
    # Create a temporary model to represent the current state
    temp_model = apps.get_model('itineraries', 'Itinerary')
    
    # Create the field in the database
    schema_editor.add_field(
        temp_model,
        temp_model._meta.get_field('ai_provider')
    )


def remove_ai_provider_field(apps, schema_editor):
    """
    Remove the ai_provider field from the Itinerary model.
    
    Args:
        apps: Registry of installed applications
        schema_editor: For database schema manipulation
    """
    Itinerary = apps.get_model('itineraries', 'Itinerary')
    
    # Remove the field from the model
    schema_editor.remove_field(Itinerary, 'ai_provider')


class Migration(migrations.Migration):
    """
    Migration class for adding ai_provider field to Itinerary model.
    """
    
    dependencies = [
        ('itineraries', '0010_auto_20231115_1234'),  # Update this to your last migration
    ]
    
    operations = [
        migrations.RunPython(
            code=add_ai_provider_field,
            reverse_code=remove_ai_provider_field,
            atomic=True
        ),
    ]
