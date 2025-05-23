# Generated by Django 5.2 on 2025-04-03 22:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source", models.CharField(max_length=50)),
                ("customer_name", models.CharField(blank=True, max_length=100)),
                ("customer_address", models.TextField(blank=True)),
                ("google_location", models.URLField(blank=True)),
                ("bill_file", models.FileField(upload_to="bills/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_delivered", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product_name", models.CharField(max_length=200)),
                ("quantity", models.IntegerField(default=1)),
                ("substituted_item_code", models.CharField(blank=True, max_length=100)),
                ("from_outside", models.BooleanField(default=False)),
                (
                    "external_cost",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "external_bill",
                    models.FileField(
                        blank=True, null=True, upload_to="external_bills/"
                    ),
                ),
                ("driver_name", models.CharField(blank=True, max_length=100)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                    ),
                ),
            ],
        ),
    ]
