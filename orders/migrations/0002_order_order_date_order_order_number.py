# Generated by Django 5.2 on 2025-04-05 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="order_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="order_number",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
