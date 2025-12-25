# Generated migration to add 'serving' status to Order model

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration to add 'serving' status option to Order.STATUS_CHOICES.
    
    This status is specifically for table orders where food is being served to customers.
    It fits between 'preparing' and 'out_for_delivery' in the order workflow.
    
    Workflow:
    pending → accepted → preparing → serving → delivered
    """

    dependencies = [
        ('orders', '0008_order_guest_email_order_guest_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('accepted', 'Accepted'),
                    ('preparing', 'Preparing'),
                    ('serving', 'Serving'),  # New status for table orders
                    ('out_for_delivery', 'Out for Delivery'),
                    ('delivered', 'Delivered'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
                max_length=20,
                help_text='Current status of the order'
            ),
        ),
    ]
