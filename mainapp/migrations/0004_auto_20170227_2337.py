# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-27 23:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0003_auto_20170221_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='participation',
            name='bonusPoints',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='participation',
            name='delayPoints',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='participation',
            name='totalPoints',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='participation',
            name='userPoints',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
