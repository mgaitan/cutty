# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-24 22:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_openingkind_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ['code']},
        ),
        migrations.AddField(
            model_name='opening',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.Project'),
        ),
    ]