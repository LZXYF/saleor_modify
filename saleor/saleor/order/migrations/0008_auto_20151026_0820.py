# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0006_product_updated_at"),
        ("order", "0007_deliverygroup_tracking_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="ordereditem",
            name="stock",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                to="product.Stock",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="ordereditem",
            name="stock_location",
            field=models.CharField(
                default="", max_length=100, verbose_name="stock location"
            ),
        ),
    ]
