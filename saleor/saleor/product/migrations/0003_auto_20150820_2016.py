# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("product", "0002_auto_20150722_0545")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="attributes",
            field=models.ManyToManyField(
                related_name="products", to="product.ProductAttribute", blank=True
            ),
        )
    ]
