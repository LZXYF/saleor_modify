# Generated by Django 2.2.3 on 2019-11-24 12:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0097_attributevalue_gender'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attributevalue',
            old_name='gender',
            new_name='type_ini',
        ),
    ]