"""
Initial migration for travel_gallery app.

This migration creates the GalleryImage model to store travel gallery images.
"""

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """
    Initial migration for the travel_gallery app.
    
    This migration creates the GalleryImage model which stores travel gallery
    images with their metadata, including title, description, image URL,
    location, coordinates, featured status, and display order.
    """

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GalleryImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, help_text='Title of the gallery image')),
                ('description', models.TextField(blank=True, help_text='Detailed description of the image and location')),
                ('image_url', models.URLField(help_text='URL to the image file (hosted externally or in CDN)')),
                ('location', models.CharField(max_length=200, help_text='Location where the image was taken')),
                ('coordinates', models.CharField(blank=True, max_length=100, help_text='GPS coordinates in format "lat,lng"')),
                ('is_featured', models.BooleanField(default=False, help_text='Whether this image is featured on homepage or key pages')),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Order in which to display images (lower numbers first)')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time when this image was added')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date and time when this image was last updated')),
            ],
            options={
                'verbose_name': 'Gallery Image',
                'verbose_name_plural': 'Gallery Images',
                'ordering': ['display_order', '-created_at'],
            },
        ),
    ]
