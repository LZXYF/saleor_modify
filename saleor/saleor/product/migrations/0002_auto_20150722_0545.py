# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("product", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(default="", verbose_name="description", blank=True),
        )
    ]
