# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-01 23:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medialibrary', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediafiletranslation',
            name='caption',
            field=models.CharField(max_length=1024, verbose_name='caption'),
        ),
    ]
